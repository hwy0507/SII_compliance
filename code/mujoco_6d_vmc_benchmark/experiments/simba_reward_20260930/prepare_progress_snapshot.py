"""Reproducibly overlay opt-in reward-potential diagnostic onto frozen_v3.

Copies the complete original snapshot (including base source.tar and MANIFEST).
Only the Office reward-side Hooks.potential path changes. No training is started.
Enable with STUDY_DENSE_PROGRESS=1 in the diagnostic campaign.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

REL=Path("code/mujoco_6d_vmc_benchmark/experiments/simba_reward_20260930")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    if a.output.exists():raise ValueError("Preserve existing snapshot; output must be new")
    base_manifest=hashlib.sha256((a.source/"MANIFEST.json").read_bytes()).hexdigest()
    shutil.copytree(a.source,a.output)
    source=Path(__file__).resolve().parent
    updated={}
    for name in ("office_env.py","progress_potential.py","test_progress_potential.py"):
        target=a.output/REL/name
        shutil.copy2(source/name,target)
        updated[str(REL/name)]=hashlib.sha256(target.read_bytes()).hexdigest()
    protocol=dict(classification="training_coverage_diagnostic_not_primary_campaign_result",
        base_snapshot=str(a.source.resolve()),snapshot=str(a.output.resolve()),
        source_manifest_sha256=base_manifest,updated_files_sha256=updated,
        enable_environment={"STUDY_DENSE_PROGRESS":"1",
            "STUDY_CANONICAL_ROOT":str((a.output/"code/mujoco_6d_vmc_benchmark").resolve())},
        formula="Phi=(stage + .5*route_projection + .5*exp(-(ep/.048)^2-(eR/.48)^2-(v/.1)^2))/N",
        projection_zero_length=0,readiness_timer_used=False,
        scales=dict(position_m=.048,rotation_rad=.48,linear_speed_mps=.1,threshold_multiplier=4.),
        planned_training=dict(steps_per_run=40000,utd=2,seeds=[41001,41002],
            reward_modes=["office_task","metric"],from_scratch=True,resume=False),
        unchanged="task gates, physical scene, actor input, filters, network and terminal-zero shaping",
        original_MANIFEST_and_source_tar="retained verbatim as base provenance; apply this overlay record",
        reproduction="Run prepare_progress_snapshot.py --source FROZEN_V3 --output NEW_DIRECTORY")
    (a.output/"PROGRESS_DIAGNOSTIC_PATCH.json").write_text(json.dumps(protocol,indent=2)+"\n")
    (a.output/"FROZEN_DIAGNOSTIC_PROTOCOL.json").write_text(json.dumps(protocol,indent=2)+"\n")
    print(json.dumps(protocol,indent=2))


if __name__=="__main__":
    main()
