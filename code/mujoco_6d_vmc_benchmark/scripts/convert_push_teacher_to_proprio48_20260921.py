"""Losslessly upgrade accepted 6-D push VMC traces from 45D to 48D.

The historical rollout already stored the exact encoder-derived six-axis
wrench used by the teacher.  Its observation contained only wrench[:3].  This
script inserts the recorded moment components before the path direction,
without rerunning MuJoCo or changing any teacher action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np


SPLIT_BY_PHYSICAL_FIXTURE = {
    "rod": "train",
    "rear": "train",
    "combined": "train",
    "front": "validation",
    "rear_combined": "test",
}


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--search",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    state=json.loads((args.search/"state.json").read_text())
    accepted=[row for row in state["history"] if row.get("accepted")]
    manifest=[];content_hashes=set();counts={s:0 for s in ("train","validation","test")}
    groups={s:set() for s in counts};fixtures={s:set() for s in counts}
    maximum_force_channel_mismatch=0.
    for source_row in accepted:
        fixture=source_row["group"]
        if fixture not in SPLIT_BY_PHYSICAL_FIXTURE:continue
        split=SPLIT_BY_PHYSICAL_FIXTURE[fixture]
        source_result=Path(source_row["result_file"])
        source_trace=source_result.parent/"rollout.npz"
        result=json.loads((source_result.parent/"rollout.json").read_text())
        if not result.get("success") or result.get("invalid_physics"):continue
        with np.load(source_trace,allow_pickle=False) as data:
            observation=np.asarray(data["observation"],dtype=np.float32)
            teacher_action=np.asarray(data["teacher_action"],dtype=np.float32)
            teacher_wrench=np.asarray(data["teacher_force"],dtype=np.float32)
            time_s=np.asarray(data["time"],dtype=np.float64)
        if observation.ndim!=2 or observation.shape[1]!=45 or teacher_wrench.shape!=(len(observation),6) or teacher_action.shape!=(len(observation),7):
            raise ValueError(f"schema mismatch: {source_trace}")
        mismatch=float(np.max(np.abs(observation[:,39:42]-teacher_wrench[:,:3])))
        maximum_force_channel_mismatch=max(maximum_force_channel_mismatch,mismatch)
        if mismatch>1e-6:raise ValueError(f"recorded wrench does not match old observation: {source_trace}: {mismatch}")
        upgraded=np.concatenate((observation[:,:39],teacher_wrench,observation[:,42:45]),axis=1)
        if upgraded.shape!=(len(observation),48) or not np.isfinite(upgraded).all() or not np.isfinite(teacher_action).all():raise ValueError(source_trace)
        content=hashlib.sha256(upgraded.tobytes()+teacher_action.tobytes()).hexdigest()
        if content in content_hashes:raise RuntimeError(f"duplicate upgraded content: {source_trace}")
        content_hashes.add(content)
        config=source_row["config"];parameter_group=digest(config)
        ident=f"push_{len(manifest):04d}";relative=Path("dataset")/"episodes"/"push"/(ident+".npz")
        destination=args.output/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(destination,observation=upgraded,teacher_action=teacher_action,
            teacher_wrench=teacher_wrench,command_time_s=time_s,dt_s=np.float64(.04))
        record=dict(id=ident,scene="push",split=split,physical_fixture=fixture,
            fixture_hash=digest({"campaign":"vmc_auto_search_20260920","group":fixture}),
            parameter_group=parameter_group,config=config,trace=str(relative),samples=len(upgraded),
            source_trace=str(source_trace),source_result=str(source_result.parent/"rollout.json"),
            source_search_result=str(source_result),content_hash=content,
            conversion="insert exact recorded teacher_wrench[:,3:6] between legacy force3 and path_direction3",
            teacher_family="six_d_saturated_virtual_model_controller",teacher_force="estimated_proprioceptive_wrench")
        manifest.append(record);counts[split]+=1;groups[split].add(parameter_group);fixtures[split].add(fixture)
    if not manifest:raise RuntimeError("No accepted traces")
    for a,b in (("train","validation"),("train","test"),("validation","test")):
        if groups[a]&groups[b]:raise RuntimeError(f"parameter leakage {a}/{b}")
        if fixtures[a]&fixtures[b]:raise RuntimeError(f"fixture leakage {a}/{b}")
    # Train-only normalization, accumulated without loading the complete bank.
    total=0;sum_x=np.zeros(48,dtype=np.float64);sum_x2=np.zeros(48,dtype=np.float64)
    for row in manifest:
        if row["split"]!="train":continue
        with np.load(args.output/row["trace"],allow_pickle=False) as data:x=data["observation"].astype(np.float64)
        total+=len(x);sum_x+=x.sum(0);sum_x2+=(x*x).sum(0)
    mean=sum_x/total;std=np.sqrt(np.maximum(sum_x2/total-mean*mean,0.)).clip(min=.03)
    np.savez_compressed(args.output/"normalization_train_only.npz",mean=mean.astype(np.float32),std=std.astype(np.float32),samples=np.int64(total))
    payload=dict(version="unified_6d_push_proprio48_20260921",contract="proprio48_action7_6d_v1",
        source_search=str(args.search),split_policy="whole physical fixture groups; no fixture or VMC parameter group crosses splits",
        counts=counts,physical_fixtures={s:sorted(fixtures[s]) for s in fixtures},
        rows=manifest,train=[r for r in manifest if r["split"]=="train"],train_clean=[r for r in manifest if r["split"]=="train"],
        validation=[r for r in manifest if r["split"]=="validation"],test=[r for r in manifest if r["split"]=="test"])
    (args.output/"manifest.json").write_text(json.dumps(payload,indent=2))
    certificate=dict(ready=True,episodes=len(manifest),counts=counts,unique_content_hashes=len(content_hashes),
        maximum_force_channel_mismatch=maximum_force_channel_mismatch,observation_dim=48,action_dim=7,
        exact_teacher_action_preserved=True,simulation_rerun=False,fixture_disjoint=True,parameter_group_disjoint=True)
    (args.output/"quality_certificate.json").write_text(json.dumps(certificate,indent=2))
    (args.output/"READY.json").write_text(json.dumps(dict(ready=True,student_training_started=False,
        manifest_sha256=hashlib.sha256((args.output/"manifest.json").read_bytes()).hexdigest(),certificate=certificate),indent=2))
    shutil.copy2(args.search/"state.json",args.output/"source_search_state.json")
    print(json.dumps(certificate,indent=2))


if __name__=="__main__":main()
