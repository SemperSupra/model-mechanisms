#!/usr/bin/env python3
"""One synthetic source-safe Apple MLX / gsplat-mlx differentiation oracle.

R0 checks one real Metal-backed Gaussian rasterization, spatial transform,
covariance gradients, and finite-difference/render Jacobian correspondence.
Strictly NOT learned reconstruction, learned model inference, or human content.
"""
import hashlib
import importlib.metadata as md
import json
import math
import os
import platform
import sys
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
from PIL import Image
from gsplat_mlx import rasterization
from gsplat_mlx.core.covariance import quat_scale_to_covar_preci

ROOT = Path(os.environ.get("MLX_GSPLAT_OUT", "out/mlx-gsplat")).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
WIDTH = HEIGHT = 32
FX = FY = 24.
Z = 2.
SHIFT_M = 0.2
CAM_CX = 16.
CAM_CY = 16.
STEP = 0.002

def scalar(x):
    mx.eval(x)
    return float(np.asarray(x).item())

def render(shift):
    means = mx.stack([shift, mx.array(0., dtype=mx.float32), mx.array(Z, dtype=mx.float32)])[None, :]
    quats = mx.array([[1., 0., 0., 0.]], dtype=mx.float32)
    scales = mx.array([[0.18, 0.22, 0.16]], dtype=mx.float32)
    opacity = mx.array([0.68], dtype=mx.float32)
    colors = mx.array([[[0.95, 0.16, 0.26]]], dtype=mx.float32)  # C,N,3 direct
    viewmats = mx.eye(4, dtype=mx.float32)[None, :, :]
    Ks = mx.array([[[FX, 0., CAM_CX], [0., FY, CAM_CY], [0., 0., 1.]]], dtype=mx.float32)
    image, alpha, info = rasterization(
        means, quats, scales, opacity, colors, viewmats, Ks,
        WIDTH, HEIGHT, near_plane=0.01, far_plane=10.,
        sh_degree=None, differentiable=True, backgrounds=mx.array([[0.,0.,0.]], dtype=mx.float32)
    )
    return image, alpha

def image_centroid(alpha):
    a = np.asarray(alpha)[0, :, :, 0]
    assert np.isfinite(a).all() and a.max() > 0.01 and a.sum() > 0, "transparent/NaN image"
    return float((a * np.arange(WIDTH, dtype=float)[None, :]).sum() / a.sum())

def moment(x):
    _, a = render(x)
    xx = mx.arange(WIDTH, dtype=mx.float32)[None, :]
    return mx.sum(a[0, :, :, 0] * xx) / mx.sum(a)

def covariance_oracle():
    q = mx.array([[1.,0.,0.,0.]], dtype=mx.float32)
    s = mx.array([[0.1,0.2,0.3]], dtype=mx.float32)
    C, P = quat_scale_to_covar_preci(q,s,compute_covar=True,compute_preci=True)
    mx.eval(C,P)
    c = np.asarray(C)[0]
    p = np.asarray(P)[0]
    assert np.allclose(c, np.diag([0.01,0.04,0.09]),atol=1e-6), c
    assert np.allclose(c @ p, np.eye(3),atol=1e-5), p
    def trace_cov(scalar_scales):
        cov,_ = quat_scale_to_covar_preci(q,scalar_scales,compute_covar=True,compute_preci=False)
        return mx.sum(cov)
    d = mx.grad(trace_cov)(s)
    mx.eval(d)
    expected = np.array([[0.2,0.4,0.6]])
    # trace covariance == sum(scale^2) for unit quaternion
    assert np.allclose(np.asarray(d),expected,atol=1e-5),np.asarray(d)
    return {"covariance_diag":np.diag(c).tolist(),"trace_scale_grad":np.asarray(d).tolist()}

def record_png(path, image):
    im = np.asarray(image)[0]
    assert im.shape == (HEIGHT,WIDTH,3)
    assert np.isfinite(im).all()
    Image.fromarray(np.uint8(np.clip(im,0,1)*255),"RGB").save(path)
    return {"filename":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    record={"schema":"mlx-gsplat-r0/v1","status":"FAIL","qualification":"tiny original synthetic source-only Gaussian rendering and gradient on free Mac GHA",
            "upstream_repo":"RobotFlow-Labs/gsplat-mlx",
            "upstream_commit":"9e53709a94e9c56fb66db2708d7d728832176713",
            "run_head":os.environ.get("GITHUB_SHA","LOCAL"),
            "mlx_version":md.version("mlx"),"gsplat_mlx_version":md.version("gsplat-mlx"),
            "platform":platform.platform(),"architecture":platform.machine(),
            "device":str(mx.default_device()),"tests":{}}
    try:
        mx.set_default_device(mx.gpu)
        if mx.default_device() != mx.gpu:
            raise RuntimeError("MLX did not expose Metal GPU")
        record["device"]=str(mx.default_device())
        record["tests"]["covariance"]=covariance_oracle()
        start=time.monotonic()
        img0,a0=render(mx.array(0.,dtype=mx.float32))
        img1,a1=render(mx.array(SHIFT_M,dtype=mx.float32))
        mx.eval(img0,a0,img1,a1)
        record["tests"]["two_renders_elapsed_ms"]=round((time.monotonic()-start)*1000,1)
        c0,c1=image_centroid(a0),image_centroid(a1)
        measured=c1-c0
        expected=FX*SHIFT_M/Z
        if abs(measured-expected)>0.75:
            raise AssertionError(f"centroid displacement {measured} vs projection expected {expected}")
        record["tests"]["image_displacement"]={"initial_x":c0,"final_x":c1,
            "observed_px":measured,"expected_px":expected,"error_px":measured-expected,
            "source_edit_m":SHIFT_M}
        record["tests"]["images"]=[record_png(ROOT/"gaussian_origin.png",img0),
                                  record_png(ROOT/"gaussian_shifted.png",img1)]
        value_grad=mx.grad(moment)(mx.array(0.,dtype=mx.float32))
        analytic=scalar(value_grad)
        plus=scalar(moment(mx.array(STEP,dtype=mx.float32)))
        minus=scalar(moment(mx.array(-STEP,dtype=mx.float32)))
        finite=(plus-minus)/(2*STEP)
        if not math.isfinite(analytic) or not math.isfinite(finite):
            raise AssertionError("nonfinite position gradient")
        if abs(analytic-finite)>max(0.5,0.20*abs(finite)):
            raise AssertionError(f"MLX gradient vs finite difference: {analytic} vs {finite}")
        record["tests"]["image_centroid_gradient"]={"autodiff":analytic,"finite_diff":finite,
            "abs_error":abs(analytic-finite),"step_m":STEP}
        record["status"]="PASS"
    except BaseException as exc:
        record["error"]={"type":type(exc).__name__,"message":str(exc)}
        raise
    finally:
        (ROOT/"receipt.json").write_text(json.dumps(record,indent=2,sort_keys=True)+"\n")
        print(json.dumps(record,indent=2,sort_keys=True),flush=True)

if __name__=="__main__":
    sys.exit(main())
