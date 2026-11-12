#!/usr/bin/env python3
"""Independent, non-executing MeG Stage-2 reference source and entropy audit.

No published author code imported, patched on disk, or redistributed.
No BERT checkpoint, model, dataset, Kaggle provider, or GPU used.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path

AUTHOR="9fa8ae10cf33c82dd2200057f70dfcb73388cd74"
TRAIN_BLOB="a4bfdd000ab04a4b79eca68b816ebd541efa555a"
CONFIG_BLOB="85902387314cae916cd5ec62ce3c0d5f660dffbb"
MISSING_COMMA='                "threshold": task_data["threshold"]\n                "bert_checkpoint_path":'
COMPLETE='                "threshold": task_data["threshold"],\n                "bert_checkpoint_path":'
EXPECTED_THRESHOLD=0.1
EXPECTED_SIZES={1024:(1024,1800),2048:(1024,1400),4096:(1024,2100),10000:(2000,4000)}

def blob_sha(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def inspect_author_source(raw:bytes)->dict:
    if blob_sha(raw)!=TRAIN_BLOB:
        raise ValueError("STAGE2_SOURCE_IDENTITY_MISMATCH")
    source=raw.decode("utf-8")
    if source.count(MISSING_COMMA)!=1:
        raise ValueError("EXPECTED_PARSER_BREAK_MISSING")
    # Intentionally CHECK the released source as-is rather than executing it.
    try:
        ast.parse(source)
    except SyntaxError as e:
        parser_failure={"line":e.lineno,"kind":"SyntaxError"}
    else:
        raise ValueError("UNEXPECTED_AUTHOR_SYNTAX_SUCCESS")
    # In-memory diagnostic ONLY. Never publish a disguised patched training file.
    fixed=source.replace(MISSING_COMMA,COMPLETE)
    tree=ast.parse(fixed)
    functions={node.name for node in tree.body if isinstance(node,ast.FunctionDef)}
    if not {"get_config","train_model","calculate_entropy"}.issubset(functions):
        raise ValueError("MISSING_EXPECTED_STAGE2_FUNCTION")
    if "torch.load(checkpoint_path" not in source:
        raise ValueError("UNEXPECTED_CHECKPOINT_LOADING_CONTRACT")
    if "optimizer.zero_grad()" not in source:
        raise ValueError("UNEXPECTED_STAGE2_OPTIMIZER_RESET")
    if "set_seed(42)" not in source:
        raise ValueError("UNEXPECTED_STAGE2_SEED")
    return {
      "original_git_blob_sha1":TRAIN_BLOB,
      "original_source_importable":False,
      "syntax_error":parser_failure,
      "minimal_in_memory_one_comma_repair_parses":True,
      "original_source_modified_or_executed":False,
      "unsafe_pickle_checkpoint_load_present":True,
      "optimizer_zero_grad_present":True,
      "set_seed_42_in_cli":True,
      "checkpoint_families":"BERT + familiarity classifier, not trained checkpoints",
      "release_gate":"SOURCE_SYNTAX_CORRECTION_REQUIRES_EXPLICIT_DEVIATION"
    }

def inspect_config(raw:bytes)->dict:
    if blob_sha(raw)!=CONFIG_BLOB:
        raise ValueError("STAGE2_HPARAM_IDENTITY_MISMATCH")
    text=raw.decode("utf-8")
    block=text.split("  phi2:\n",1)[1].split("    cf:\n",1)[0]
    if not block.startswith("    zsre:\n"):
        raise ValueError("PHI2_ZSRE_BLOCK_MISSING")
    if "      threshold: 0.1\n" not in block:
        raise ValueError("ENTROPY_THRESHOLD_DRIFT")
    path="./checkpoints_trained_bert/bert_phi2_zsre/model_epoch_100.pth"
    if path not in block:
        raise ValueError("STAGE1_CHECKPOINT_DEPENDENCY_DRIFT")
    for size,(batch,epochs) in EXPECTED_SIZES.items():
        needle=f"- edit_size: {size}\n          batch_size: {batch}\n          epoch: {epochs}"
        if needle not in block:
            raise ValueError("CONFIG_CELL_MISMATCH:"+str(size))
    return {
      "source_git_blob_sha1":CONFIG_BLOB,
      "task":"phi2_zsre",
      "entropy_threshold":EXPECTED_THRESHOLD,
      "upstream_stage1_checkpoint_reference":path,
      "edit_size_batch_epoch":[{"edit_size":n,"batch_size":batch,"epochs":ep}
                               for n,(batch,ep) in sorted(EXPECTED_SIZES.items())],
      "source_checkpoint_exists":False
    }

def softmax(logits:list[float])->list[float]:
    if len(logits)!=10 or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in logits):
        raise ValueError("INVALID_10_CLASS_LOGITS")
    mx=max(logits)
    exp=[math.exp(x-mx) for x in logits]
    total=sum(exp)
    return [v/total for v in exp]

def entropy_probabilities(probabilities:list[float])->float:
    if len(probabilities)!=10 or any(not math.isfinite(x) or x<0 for x in probabilities):
        raise ValueError("INVALID_10_CLASS_PROBABILITIES")
    if not math.isclose(sum(probabilities),1.0,rel_tol=1e-9,abs_tol=1e-9):
        raise ValueError("PROBABILITIES_NOT_NORMALIZED")
    return -sum(max(v,1e-8)*math.log(max(v,1e-8)) for v in probabilities)

def route(logits:list[float],threshold:float=EXPECTED_THRESHOLD)->dict:
    if not math.isfinite(threshold) or threshold<0:
        raise ValueError("BAD_ENTROPY_THRESHOLD")
    p=softmax(logits)
    h=entropy_probabilities(p)
    high=h>threshold  # strict greater-than, same as released source
    return {"entropy":h,"abstained":high,"class_index":-1 if high else max(range(10),key=p.__getitem__)}

def report(src:bytes,cfg:bytes)->dict:
    return {
      "schema":"model-mechanisms.meg-stage2-static-routing/v1",
      "status":"SOURCE_SYNTAX_BLOCKER_VERIFIED",
      "upstream_revision":AUTHOR,
      "source":inspect_author_source(src),
      "configuration":inspect_config(cfg),
      "numerical_oracle":{
          "uniform_entropy":route([0.]*10)["entropy"],
          "uniform_abstains":route([0.]*10)["abstained"],
          "confident_entropy":route([20.]+[-20.]*9)["entropy"],
          "confident_abstains":route([20.]+[-20.]*9)["abstained"],
      },
      "published_stage2_checkpoint_loaded":False,
      "stage2_training_executed":False,
      "scientific_meg_result":False,
      "trained_stage1_dependency_available":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--hparams",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    if a.receipt.exists():
        raise SystemExit("REFUSE_OVERWRITE_RECEIPT")
    result=report(a.source.read_bytes(),a.hparams.read_bytes())
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":main()
