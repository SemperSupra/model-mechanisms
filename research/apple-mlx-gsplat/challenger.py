#!/usr/bin/env python3
"""Apple MLX alternative renderer: bounded render-only metal vs reference smoke.

All geometry is original 1-Gaussian synthetic, no external model/data.
The upstream package expressly excludes model training and gradient optimization.
"""
import hashlib
import importlib.metadata as md
import json
import math
import os
import platform
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
from PIL import Image
from mlx_splat.core import Camera, GaussianSet
from mlx_splat.renderer import render_gaussians

OUT = Path(os.environ.get("MLX_SPLAT_OUT", "out/mlx-splat-challenger")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
W = H = 32
FX = FY = 24.0
Z = 2.0
DX = 0.2

def camera():
    return Camera(width=W,height=H,fx=FX,fy=FY,cx=16.0,cy=16.0,
                  R_c2w=mx.eye(3),t_c2w=mx.zeros(3))

def scene(x):
    sh = np.zeros((1,3,16),dtype=np.float32)
    sh[0,:,0]=[2.0,0.5,-0.5]
    return GaussianSet(
        positions=mx.array([[x,0.0,Z]],dtype=mx.float32),
        log_scales=mx.array([[math.log(0.18),math.log(0.22),math.log(0.16)]],dtype=mx.float32),
        quats=mx.array([[1.,0.,0.,0.]],dtype=mx.float32),
        opacity=mx.array([1.0],dtype=mx.float32),
        sh=mx.array(sh))

def render(x,algorithm):
    start=time.monotonic()
    img=render_gaussians(scene(x),camera(),background=(0.0,0.0,0.0),
                         raster_algorithm=algorithm,
                         projection_algorithm="fast",
                         tile_algorithm="global",use_culling=False,sh_degree=0)
    mx.eval(img)
    a=np.asarray(img)
    if a.shape!=(H,W,3) or not np.isfinite(a).all() or np.max(a)<=0.01:
        raise AssertionError(f"empty/invalid {algorithm} image")
    return a,round((time.monotonic()-start)*1000,2)

def center(a):
    lum=np.maximum(a.mean(axis=2),0.0)
    weight=lum.sum()
    if weight<=0.0: raise AssertionError("zero image weight")
    return float((lum*np.arange(W,dtype=float)[None,:]).sum()/weight)

def write_png(name,a):
    p=OUT/name
    Image.fromarray(np.uint8(np.clip(a,0.0,1.0)*255),"RGB").save(p)
    return {"filename":name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    rec={"schema":"mlx-splat-challenger-r0/v1","status":"FAIL",
         "upstream_repo":"daikiad/mlx-splat",
         "upstream_commit":"84e838856d13597b479465d4648aed472d01da8e",
         "device":str(mx.default_device()),
         "mlx_version":md.version("mlx"),"architecture":platform.machine(),
         "platform":platform.platform(),"source_commit":os.environ.get("GITHUB_SHA","LOCAL"),
         "qualification":"render-only Metal, no differentiable raster training claim","tests":{}}
    try:
        mx.set_default_device(mx.gpu)
        if mx.default_device()!=mx.gpu: raise AssertionError("No actual MLX GPU device")
        rec["device"]=str(mx.default_device())
        metal0, t0=render(0.0,"metal")
        metal1, t1=render(DX,"metal")
        naive0, t2=render(0.0,"naive")
        expected=FX*DX/Z
        actual=center(metal1)-center(metal0)
        discrepancy=actual-expected
        if abs(discrepancy)>0.75:
            raise AssertionError(f"Metal rendered centroid movement {actual} vs expected {expected}")
        max_diff=float(np.max(np.abs(metal0-naive0)))
        if max_diff>0.05:
            raise AssertionError(f"Metal and naive raster differ too much: max {max_diff}")
        rec["tests"]["centroid"]={"expected_px":expected,"observed_px":actual,"error_px":discrepancy}
        rec["tests"]["reference_agreement"]={"max_abs_diff":max_diff,"threshold":0.05}
        rec["tests"]["render_times_ms"]={"metal_origin":t0,"metal_moved":t1,"naive_origin":t2}
        rec["tests"]["images"]=[write_png("metal_origin.png",metal0),write_png("metal_moved.png",metal1),write_png("naive_origin.png",naive0)]
        rec["status"]="PASS"
    except BaseException as exc:
        rec["error"]={"type":type(exc).__name__,"message":str(exc)}
        raise
    finally:
        (OUT/"receipt.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
        print(json.dumps(rec,indent=2,sort_keys=True),flush=True)

if __name__=="__main__":main()
