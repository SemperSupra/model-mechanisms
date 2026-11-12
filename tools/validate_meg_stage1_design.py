#!/usr/bin/env python3
"""Offline 2x2 source-fidelity DOE manifest admission guard (no model/training)."""
import argparse
import json
from pathlib import Path

PARA=("as_published_character_iteration","type_corrected_full_question")
GRAD=("as_published_accumulated_gradients","reset_gradients_each_batch")
PAIRS={PARA[0]:4000,PARA[1]:2668}
FRAGMENTS={PARA[0]:2664,PARA[1]:0}

def validate(doc:dict) -> dict:
    if doc.get("schema")!="model-mechanisms.meg-stage1-fidelity-factorial/v1":
        raise ValueError("BAD_SCHEMA")
    if doc.get("status")!="PRE_REGISTERED_NOT_ADMITTED":
        raise ValueError("WRONG_ADMISSION_STATE")
    if doc.get("author_code_revision")!="9fa8ae10cf33c82dd2200057f70dfcb73388cd74":
        raise ValueError("AUTHOR_SOURCE_DRIFT")
    if doc.get("author_train_git_blob")!="df2f3eaa23dda322657f2821ffef899f11273bc7":
        raise ValueError("TRAIN_BLOB_DRIFT")
    if doc.get("author_config_git_blob")!="86cb6baa036fd5da0ba50f465f0f42d55add7366":
        raise ValueError("CONFIG_BLOB_DRIFT")
    if doc.get("original_publisher_stage1_data_sha256")!="438dc2f1c98aec85f828eaf95fed2f40c19d470a1cdb6723f9103aa8e304ec18":
        raise ValueError("PUBLISHER_DATA_DRIFT")
    for field,value in {
        "dataset_records":4000,"training_source_records":2000,
        "validation_source_records":1024,"positional_overlap_count":0,
        "source_literal_training_pairs":4000,
        "source_literal_character_fragment_pairs":2664,
        "type_corrected_training_pairs":2668,
        "source_training_full_epochs":30000,"original_batch_size":4000,
    }.items():
        if doc.get(field)!=value:raise ValueError("MEASURED_SOURCE_FACT_DRIFT:"+field)
    factors=doc.get("factors",{})
    if factors!={"paraphrase_policy":list(PARA),"gradient_policy":list(GRAD)}:
        raise ValueError("MISSING_OR_UNREVIEWED_FACTOR")
    budget=doc.get("screen_budget")
    if budget!={"max_records":16,"max_epochs":1,"max_device_type":"cpu",
               "provider_calls_allowed":False}:
        raise ValueError("UNAUTHORIZED_BUDGET_OR_PROVIDER")
    if any(doc.get(field) is not False for field in (
        "scientific_promotion_allowed","publisher_rights_review_complete",
        "model_weights_downloaded","training_run_executed")):
        raise ValueError("PREMATURE_SCIENCE_OR_SOURCE_PROMOTION")
    if doc.get("holdout_subject_identity") is not None or doc.get("original_bert_model_revision") is not None:
        raise ValueError("UNKNOWN_SOURCE_IDENTITIES_MUST_STAY_UNKNOWN")
    cells=doc.get("cells")
    if not isinstance(cells,list) or len(cells)!=4:
        raise ValueError("INCORRECT_CELL_COUNT")
    expected={(a,b) for a in PARA for b in GRAD}
    observed=set()
    for c in cells:
        if not isinstance(c,dict):
            raise ValueError("BAD_CELL")
        pair=(c.get("paraphrase_policy"),c.get("gradient_policy"))
        if pair not in expected or pair in observed:
            raise ValueError("DUPLICATED_OR_UNKNOWN_CELL")
        observed.add(pair)
        code=("literal" if pair[0]==PARA[0] else "typed")+"-"+("accum" if pair[1]==GRAD[0] else "reset")
        if c.get("cell_id")!=code or c.get("baseline_cell_id")!="literal-accum":
            raise ValueError("CELL_IDENTITY_MISMATCH")
        if c.get("expected_training_pairs_from_publisher")!=PAIRS[pair[0]]:
            raise ValueError("SOURCE_PAIR_COUNT_MISMATCH")
        if c.get("character_fragment_pairs")!=FRAGMENTS[pair[0]]:
            raise ValueError("CHARACTER_FRAGMENT_COUNT_MISMATCH")
        if c.get("admitted") is not False or c.get("executed") is not False or c.get("measurement") is not None:
            raise ValueError("RESULT_FABRICATION")
    return {"schema":"model-mechanisms.meg-stage1-design-receipt/v1",
            "status":"PASS_PLAN_ONLY","factorial_cells":4,
            "observations_measured":0,"provider_job_submitted":False,
            "research_claim":"SOURCE_FIDELITY_DOE_PREREGISTRATION_ONLY"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    args=p.parse_args()
    print(json.dumps(validate(json.loads(args.manifest.read_text(encoding="utf-8"))),sort_keys=True))

if __name__=="__main__":main()
