#!/usr/bin/env python3
"""Measure exact Stage1 textual cross-split collisions in ICLR publisher data.

Source bytes are SHA-pinned and discarded in the disposable CI job.
Output is aggregate collision counts only: no raw text, subjects or hashes.
No models, user data, third-party execution, or provider credentials.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import unicodedata
import zipfile

OUTER_SHA="d8abdd06a77318d0af5f6f3414092eafe3b29a3fe10eb890704d6c237c760d71"
INNER_SHA="10f0cad94529f9d1522a34dad9379e6f7e15ea51f9500180fe4f892edffde088"
SOURCE_SHA="438dc2f1c98aec85f828eaf95fed2f40c19d470a1cdb6723f9103aa8e304ec18"
INNER_PATH="code_and_data_for_our_MeG/data_for_our_MeG.zip"
SOURCE_PATH="data_for_our_MeG/new_split_data/zsre_for_bert_train.json"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def norm(text:str)->str:
    if not isinstance(text,str):
        raise ValueError("UNSUPPORTED_TEXT_FIELD")
    return " ".join(unicodedata.normalize("NFKC",text).casefold().split())

def phrases(record:dict,policy:str)->list[str]:
    field=record.get("rephrase")
    if isinstance(field,list) and all(isinstance(v,str) for v in field):
        return field[:2]
    if isinstance(field,str):
        return list(field[:2]) if policy=="literal" else [field]
    raise ValueError("UNEXPECTED_REPHRASE_SOURCE_TYPE")

def compare(records:list[dict])->dict:
    if not isinstance(records,list) or len(records)!=4000 or any(not isinstance(r,dict) for r in records):
        raise ValueError("EXPECTED_EXACT_4000_PUBLISHER_RECORDS")
    train=records[-2000:]
    valid=records[:1024]
    # Original author's val() uses rephrase[0], not both rephrase variants.
    for r in train+valid:
        if not isinstance(r.get("src"),str):
            raise ValueError("BAD_PUBLISHER_SRC")
    if any(not isinstance(r.get("rephrase"),list)
           or len(r["rephrase"])<1
           or not all(isinstance(x,str) for x in r["rephrase"]) for r in valid):
        raise ValueError("BAD_VALIDATION_REPHRASE_LIST")

    def norm_set(xs:list[str])->set[str]:
        return {s for v in xs if (s:=norm(v))}
    val_src=[norm(r["src"]) for r in valid]
    val_reph=[norm(r["rephrase"][0]) for r in valid]
    out={
        "schema":"model-mechanisms.meg-stage1-crosssplit-text/v1",
        "status":"EXACT_TEXT_COMPARISON_ONLY",
        "source_sha256":SOURCE_SHA,
        "record_count":4000,
        "training_record_count":2000,
        "validation_record_count":1024,
        "normalization":"NFKC + unicode casefold + collapse whitespace",
        "validation_unique_src":len(set(val_src)),
        "validation_unique_first_rephrase":len(set(val_reph)),
        "models_or_teacher_weights_loaded":False,
        "subject_or_semantic_leakage_tested":False,
        "question_text_or_hashes_emitted":False,
        "scientific_result_claimed":False,
        "policies":{},
    }
    for policy in ("literal","corrected"):
        tsrc=norm_set([r["src"] for r in train])
        tphrase=norm_set([v for r in train for v in phrases(r,policy)])
        train_texts=tsrc|tphrase
        by_src=sum(bool(a and a in train_texts) for a in val_src)
        by_rephrase=sum(bool(b and b in train_texts) for b in val_reph)
        any_collision=sum(bool((a and a in train_texts) or (b and b in train_texts))
                          for a,b in zip(val_src,val_reph))
        out["policies"][policy]={
            "training_pair_count":sum(len(phrases(r,policy)) for r in train),
            "training_unique_src":len(tsrc),
            "training_unique_paraphrase_tokens":len(tphrase),
            "validation_src_in_training_src":sum(bool(a and a in tsrc) for a in val_src),
            "validation_src_in_training_paraphrases":sum(bool(a and a in tphrase) for a in val_src),
            "validation_rephrase_in_training_src":sum(bool(b and b in tsrc) for b in val_reph),
            "validation_rephrase_in_training_paraphrases":sum(bool(b and b in tphrase) for b in val_reph),
            "validation_src_in_any_training_text":by_src,
            "validation_rephrase_in_any_training_text":by_rephrase,
            "validation_records_with_any_exact_text_collision":any_collision,
            "train_unique_src_or_paraphrase":len(train_texts),
        }
    if out["policies"]["literal"]["training_pair_count"]!=4000:
        raise ValueError("ORIGINAL_TRAINING_PAIR_COUNT_CHANGED")
    if out["policies"]["corrected"]["training_pair_count"]!=2668:
        raise ValueError("CORRECTED_TRAINING_PAIR_COUNT_CHANGED")
    return out

def original_records(zip_path:Path)->list[dict]:
    if not zip_path.is_file() or zip_path.stat().st_size>512000000:
        raise ValueError("BAD_ARCHIVE_SIZE")
    outer=zip_path.read_bytes()
    if sha(outer)!=OUTER_SHA:raise ValueError("OUTER_DIGEST_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(outer)) as z:
        if z.getinfo(INNER_PATH).file_size>512000000:raise ValueError("INNER_SIZE_LIMIT")
        inner=z.read(INNER_PATH)
    if sha(inner)!=INNER_SHA:raise ValueError("INNER_DIGEST_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(inner)) as z:
        if z.getinfo(SOURCE_PATH).file_size>5000000:raise ValueError("SOURCE_FILE_TOO_LARGE")
        raw=z.read(SOURCE_PATH)
    if sha(raw)!=SOURCE_SHA:raise ValueError("STAGE1_INPUT_DIGEST_MISMATCH")
    return json.loads(raw)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--official-supplement",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    args=p.parse_args()
    if args.receipt.exists():raise SystemExit("REFUSE_OVERWRITE")
    result=compare(original_records(args.official_supplement))
    args.receipt.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
