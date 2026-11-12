#!/usr/bin/env python3
"""Actual tiny random BERT contrastive training on CPU, no pretrained assets.

An independent *mechanical* smoke of the released MeG Stage1 gradient policy,
not a numerical reproduction of the author's pretrained BERT, data, or scores.
All embeddings, tokens and model weights are synthetic, initialized in memory.
"""
from __future__ import annotations

import json
import math

import torch
import torch.nn.functional as F
from transformers import BertConfig, BertModel

SEED=1729
STEPS=3
EMBED=32

def contrastive(q:torch.Tensor,p:torch.Tensor,temperature:float=1.0)->torch.Tensor:
    """Replicate the stage-one paired-positive / diagonal-masked InfoNCE math."""
    q=F.normalize(q,p=2,dim=-1)
    p=F.normalize(p,p=2,dim=-1)
    positive=F.cosine_similarity(q,p,dim=-1).unsqueeze(1)
    negatives=q@p.T
    negatives=negatives.masked_fill(torch.eye(q.shape[0],dtype=torch.bool,device=q.device),float("-inf"))
    logits=torch.cat([positive,negatives],dim=1)/temperature
    return F.cross_entropy(logits,torch.zeros(q.shape[0],dtype=torch.long,device=q.device))

def _tiny_model():
    cfg=BertConfig(vocab_size=96,hidden_size=EMBED,num_hidden_layers=2,
                   num_attention_heads=4,intermediate_size=64,
                   max_position_embeddings=32,type_vocab_size=2,
                   hidden_dropout_prob=0.0,attention_probs_dropout_prob=0.0)
    model=BertModel(cfg,add_pooling_layer=False)
    # Exactly one transformer block trainable; in this deliberately tiny
    # 2-layer model its final block is index 1 (not real BERT's index 11).
    for name,p in model.named_parameters():
        p.requires_grad=name.startswith("encoder.layer.1.")
    trainable=[p for p in model.parameters() if p.requires_grad]
    if not trainable or len(trainable)==len(list(model.parameters())):
        raise ValueError("BAD_FREEZE_POLICY")
    return model,trainable

def _tokens(step:int)->tuple[torch.Tensor,torch.Tensor]:
    base=[
        [1,10+step,11+step,12,13,14,15,2],
        [1,40+step,41+step,42,43,44,45,2],
    ]
    para=[
        [1,10+step,11+step,16,13,14,15,2],
        [1,40+step,41+step,46,43,44,45,2],
    ]
    return torch.tensor(base,dtype=torch.long),torch.tensor(para,dtype=torch.long)

def train_policy(policy:str)->dict:
    if policy not in ("as_published_accumulated_gradients","reset_gradients_each_batch"):
        raise ValueError("UNAPPROVED_POLICY")
    torch.manual_seed(SEED)
    torch.set_num_threads(1)
    model,params=_tiny_model()
    model.train()
    opt=torch.optim.AdamW(params,lr=1e-4)
    losses=[]
    grad_norms=[]
    first_grad=None
    for step in range(STEPS):
        if policy=="reset_gradients_each_batch":
            opt.zero_grad(set_to_none=True)
        ids,positive_ids=_tokens(step)
        q=model(input_ids=ids).last_hidden_state[:,0,:]
        p=model(input_ids=positive_ids).last_hidden_state[:,0,:]
        loss=contrastive(p,q,temperature=1.0)
        if not bool(torch.isfinite(loss)):
            raise ValueError("NONFINITE_LOSS")
        loss.backward()
        grad=torch.cat([param.grad.detach().reshape(-1) for param in params])
        norm=float(torch.linalg.vector_norm(grad))
        if not math.isfinite(norm) or norm<=0:
            raise ValueError("MISSING_OR_NONFINITE_GRADIENT")
        if first_grad is None:
            first_grad=grad.clone()
        grad_norms.append(norm)
        losses.append(float(loss.detach()))
        opt.step()
    assert first_grad is not None
    return {
        "policy":policy,
        "losses":losses,
        "gradient_norms":grad_norms,
        "second_step_retained_prior_gradient":policy=="as_published_accumulated_gradients",
        "trainable_tensors":len(params),
        "tiny_transformer_blocks":2,
        "tiny_hidden_size":EMBED,
        "synthetic_training_pairs_per_step":2,
    }

def run()->dict:
    literal=train_policy("as_published_accumulated_gradients")
    corrected=train_policy("reset_gradients_each_batch")
    if abs(literal["gradient_norms"][1]-corrected["gradient_norms"][1])<1e-12:
        raise ValueError("POLICY_DIFFERENCE_NOT_OBSERVED")
    return {
        "schema":"model-mechanisms.meg-stage1-tiny-bert-smoke/v1",
        "status":"ACTUAL_SYNTHETIC_TORCH_CPU_TRAINING",
        "original_stage1_reference":"https://github.com/RodeWayne/MeG-for-Knowledge-Editing/tree/9fa8ae10cf33c82dd2200057f70dfcb73388cd74",
        "torch_version":torch.__version__,
        "transformers_bert":"BertModel",
        "random_seed":SEED,
        "policies":[literal,corrected],
        "second_step_gradient_norm_diff_abs":abs(literal["gradient_norms"][1]-corrected["gradient_norms"][1]),
        "pretrained_BERT_weights_loaded":False,
        "original_dataset_loaded":False,
        "trainable_final_block_only":True,
        "original_author_training_executed":False,
        "scientific_meg_reproduction":False,
        "measured_model_editing_performance":False,
        "checkpoint_published":False,
    }

def main():
    result=run()
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":main()
