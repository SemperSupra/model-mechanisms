#!/usr/bin/env python3
"""Source-only schema census of the publisher's original MeG data ZIP.

Downloads are handled by the disposable CI runner, not this tool.
No sample values are printed or stored in receipts; the source archive is
not extracted or published. No author Python, model, or pickle is executed.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

SOURCE_SHA = "d8abdd06a77318d0af5f6f3414092eafe3b29a3fe10eb890704d6c237c760d71"
NESTED_SHA = "10f0cad94529f9d1522a34dad9379e6f7e15ea51f9500180fe4f892edffde088"
NESTED_NAME = "code_and_data_for_our_MeG/data_for_our_MeG.zip"
PREFIX = "data_for_our_MeG/"
MAX_OUTER = 512_000_000
MAX_FILE = 100_000_000
EXPECTED = {
    "edit_data/gptj_cf_edit.json": ("dda379804da92a3f55dabf7b70619479b137d9ca92102cbf90401c73c7f38a53", 41121404),
    "edit_data/gptj_zsre_edit.json": ("236e2bc315800d07773cb2dedd8b4435dd6974fc39588fa22b58f8b64f5e0958", 21865696),
    "edit_data/phi2_cf_edit.json": ("34c9a0f9f65feda4fb618825ec59a35394f982bdf144fdfc0172a968b603c7c2", 41287967),
    "edit_data/phi2_zsre_edit.json": ("100fa2b28e9ed97256cd19e680392f563caa245e03cad7b6a31b6a04cf6783f7", 20357962),
    "new_split_data/multi_counterfact_new_id.json": ("f36ac1453742dae5481565982fdaefeadd74e5bca957ea4054e63d02c3969afc", 49980934),
    "new_split_data/zsre_for_bert_train.json": ("438dc2f1c98aec85f828eaf95fed2f40c19d470a1cdb6723f9103aa8e304ec18", 3733310),
    "new_split_data/zsre_mend_eval_new.json": ("aa7e3780ead75be8b45fcf06117ac253a07804e8c7e048ad3ca0704cb584e7c7", 10907819),
    "new_split_data/zsre_mend_eval_new_rephrase.json": ("46be35aa7657366bf2bb6a71bcb16f716eca58ab384ac03c6cca170ab5131167", 22541146),
    "new_split_data/zsre_train_new.json": ("326185f83eb381778ae0d498ca53e9dfa2d1d78b1ca9687c70adaf8c1984bc7a", 47938134),
    "raw_data/multi_counterfact.json": ("977a6acce4705507b5fd6bfcea8f61cd78f9ed0f9cd9c9a6bcd6c8a3ed61c833", 42914741),
    "raw_data/rephrase.prompt": ("707fd63436ee5d82642f6e9f6605d0eecd434a547345f5ad51881fe1a7d6e042", 2005),
    "raw_data/zsre_mend_eval.json": ("2c3f9fc31810df14bf4cf2b3b5a9342d90cdbe6f6956762cce10e1905abb562c", 10333353),
    "raw_data/zsre_mend_train.json": ("68a5bc2a0f2b33986c6d23c98a64bfd57571c79b0e9e471b8a638c2fea1ae0ef", 86173432),
    "raw_data/zsre_mend_train_10000.json": ("640ec98a583fc79a1b9b526f83654a9932f483715fdcc382e5ea646766f9a432", 5277557),
    "train_familiar/cf_fake_id_class.json": ("b1b60bbe3a311fd6c83bbe265fa07ceaa241e98df808b8f827a1cb434ad90dd0", 24171877),
    "train_familiar/zsre_gptj_fake_id_class.json": ("eaaa4a4b0799efb9365814d83ca3e512d3bf7a5e887618f7208363b3c35e3606", 12345892),
    "train_familiar/zsre_phi2_fake_id_class.json": ("2649173060b87de94c0f576df883ca4bc965dc7ab92449aba81100d4be412b56", 12071586),
    "README.md": ("99d849156d58ccb1be0f01531dd9f58d570f8e6293706438e1a2f7d80b10461e", 1770),
}

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def overlap_first_last(n: int, first: int = 1024, last: int = 2000) -> dict:
    if type(n) is not int or n < 0 or first < 0 or last < 0:
        raise ValueError("INVALID_SLICE_LENGTH")
    a = min(first, n)
    b = max(0, n - last)
    return {
        "total_records": n,
        "validation_first_count": a,
        "training_last_count": n - b,
        "positional_overlap_count": max(0, a - b),
        "validation_and_training_disjoint_by_index": a <= b,
    }

def stage1_field_profile(records: list[dict]) -> dict:
    """Aggregate source-key/types only; never return data values."""
    n=len(records)
    src_ok=sum(isinstance(x.get("src"),str) for x in records)
    rephrase_ok=sum(
        isinstance(x.get("rephrase"),list)
        and all(isinstance(p,str) for p in x["rephrase"])
        for x in records
    )
    both_ok=sum(
        isinstance(x.get("src"),str)
        and isinstance(x.get("rephrase"),list)
        and all(isinstance(p,str) for p in x["rephrase"])
        for x in records
    )
    return {
        "total_records":n,
        "src_string_records":src_ok,
        "rephrase_string_list_records":rephrase_ok,
        "trainer_compatible_records":both_ok,
        "trainer_compatible":both_ok==n,
        "source_values_emitted":False,
    }

def text_overlap_first_last(records: list[dict]) -> dict:
    """Aggregate normalized *text* overlaps, never emit original questions.

    This is not semantic entity-level contamination detection. The released
    Stage1 validation uses first 1024 records and training last 2000.
    """
    if not isinstance(records, list) or any(not isinstance(x,dict) for x in records):
        raise ValueError("INVALID_STAGE1_RECORDS")
    n=len(records)
    validation=records[:1024]
    training=records[max(0,n-2000):]
    def texts(record: dict) -> set[str]:
        question=record.get("src")
        rephrases=record.get("rephrase")
        if not isinstance(question,str) or not isinstance(rephrases,list):
            raise ValueError("INVALID_STAGE1_QUERY_OR_REPHRASES")
        if any(not isinstance(x,str) for x in rephrases):
            raise ValueError("INVALID_STAGE1_REPHRASE_TYPE")
        raw_texts=[question,*rephrases]
        return {" ".join(s.split()).casefold() for s in raw_texts if s.strip()}
    for record in validation + training:
        texts(record)  # fail legibly before querying fields in any comprehension
    train_src={" ".join(r["src"].split()).casefold() for r in training}
    val_src={" ".join(r["src"].split()).casefold() for r in validation}
    training_texts=set().union(*(texts(r) for r in training)) if training else set()
    val_texts=set().union(*(texts(r) for r in validation)) if validation else set()
    contaminated_validation_records=sum(bool(texts(r)&training_texts) for r in validation)
    return {
        "training_records":len(training),
        "validation_records":len(validation),
        "unique_src_overlap":len(train_src&val_src),
        "unique_src_or_rephrase_overlap":len(training_texts&val_texts),
        "validation_records_with_any_exact_text_overlap":contaminated_validation_records,
        "deduplication_normalization":"unicode_casefold_collapse_whitespace",
        "semantic_subject_overlap_evaluated":False,
        "question_text_or_hashes_emitted":False,
    }

def validate_shape(rel: str, raw: bytes) -> dict:
    # Enumerates keys only. Never emit subject/prompt/label values or record bytes.
    if rel.endswith(".json"):
        parsed = json.loads(raw)
        if not isinstance(parsed, list) or any(not isinstance(x, dict) for x in parsed):
            raise ValueError("EXPECTED_LIST_OF_OBJECTS:" + rel)
        keys = sorted({key for x in parsed for key in x.keys()})
        if any(not isinstance(k, str) for k in keys):
            raise ValueError("NONSTRING_FIELD_NAME")
        return {"type": "record_list", "record_count": len(parsed), "field_names": keys}
    return {"type": "text", "record_count": None, "field_names": []}

def audit(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_OUTER:
        raise ValueError("OUTER_ARCHIVE_SIZE_INVALID")
    outer_raw = path.read_bytes()
    if sha(outer_raw) != SOURCE_SHA:
        raise ValueError("OUTER_ARCHIVE_SHA256_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(outer_raw)) as outer:
        if NESTED_NAME not in outer.namelist():
            raise ValueError("DATA_ZIP_NOT_FOUND")
        if outer.getinfo(NESTED_NAME).file_size > MAX_OUTER:
            raise ValueError("INNER_ZIP_SIZE_INVALID")
        inner_raw = outer.read(NESTED_NAME)
    if sha(inner_raw) != NESTED_SHA:
        raise ValueError("DATA_ZIP_SHA256_MISMATCH")
    observed = []
    stage1 = None
    stage1_text_overlap = None
    stage1_field_profile_result = None
    with zipfile.ZipFile(io.BytesIO(inner_raw)) as inner:
        actual = {x.filename for x in inner.infolist() if not x.is_dir()}
        expected = {PREFIX + name for name in EXPECTED}
        if actual != expected:
            raise ValueError("PUBLISHER_MEMBER_SET_MISMATCH")
        for relative, (digest, expected_size) in sorted(EXPECTED.items()):
            member = PREFIX + relative
            info = inner.getinfo(member)
            if info.file_size != expected_size or info.file_size > MAX_FILE:
                raise ValueError("DATA_MEMBER_SIZE_MISMATCH:" + relative)
            # Bound retained data, then verify exact member bytes before JSON decoding.
            with inner.open(member) as stream:
                raw = stream.read(MAX_FILE + 1)
            if len(raw) != expected_size or sha(raw) != digest:
                raise ValueError("DATA_MEMBER_SHA256_MISMATCH:" + relative)
            shape = validate_shape(relative, raw)
            observed.append({"path": member, "sha256": digest, "bytes": expected_size, **shape})
            if relative == "new_split_data/zsre_for_bert_train.json":
                stage1 = overlap_first_last(shape["record_count"])
                stage1_records = json.loads(raw)
                stage1_field_profile_result = stage1_field_profile(stage1_records)
                if stage1_field_profile_result["trainer_compatible"]:
                    stage1_text_overlap = text_overlap_first_last(stage1_records)
    return {
        "schema": "model-mechanisms.meg-publisher-data-census/v1",
        "status": "SOURCE_SCHEMA_VERIFIED",
        "official_outer_sha256": SOURCE_SHA,
        "official_data_archive_sha256": NESTED_SHA,
        "file_count": len(observed),
        "files": observed,
        "stage1_zsre_index_overlap": stage1,
        "stage1_zsre_text_overlap": stage1_text_overlap,
        "stage1_zsre_field_profile": stage1_field_profile_result,
        "stage1_text_overlap_state": ("MEASURED_EXACT_TEXT" if stage1_text_overlap is not None
                                      else "BLOCKED_SOURCE_FIELD_MISMATCH"),
        "publisher_data_bytes_redistributed": False,
        "author_code_executed": False,
        "model_trained": False,
        "foundry_approval": False,
        "claim": "PUBLISHED_INPUT_LAYOUT_ONLY",
    }

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--publisher-zip", required=True, type=Path)
    p.add_argument("--receipt", required=True, type=Path)
    args = p.parse_args()
    if args.receipt.exists():
        raise SystemExit("REFUSE_OVERWRITE")
    result = audit(args.publisher_zip)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Print bounded summary only; public job logs contain no file contents.
    print(json.dumps({
        "status": result["status"], "file_count": result["file_count"],
        "stage1_zsre_index_overlap": result["stage1_zsre_index_overlap"],
        "stage1_zsre_text_overlap": result["stage1_zsre_text_overlap"],
        "stage1_zsre_field_profile": result["stage1_zsre_field_profile"],
        "stage1_text_overlap_state": result["stage1_text_overlap_state"],
        "file_record_counts": {i["path"]: i["record_count"] for i in result["files"]},
        "publisher_data_bytes_redistributed": False,
    }, sort_keys=True))

if __name__ == "__main__":
    main()
