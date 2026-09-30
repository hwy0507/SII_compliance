"""Second, four-rollout maximum mechanism test; no environment modifications.

Uses the SHA-pinned first campaign runner. First complete that campaign before
starting this one. These candidates are declared before any follow-up outcome.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
FIRST=ROOT/'outputs/teacher_repair_canonical_20260930'
OUT=ROOT/'outputs/teacher_repair_followup_20260930'
LIBRARY=FIRST/'source/tools/teacher_repair_campaign_20260930.py'
LIBRARY_SHA='4dade206f285124e67e1a8413a2172cad33bdb556b5dc1a6fddc591dcd517c63'
CANDIDATES={
    'velocity025_stiff2': {'velocity_weight':.25,'options':{
        'stiffness_6d':[800.,800.,2400.,20.,16.,24.],
        'damping_6d':[v*math.sqrt(2.) for v in [28.,28.,55.,2.8,2.4,3.]]}},
    'pair_average_pitch035': {'pair_average':True,'options':{'axis_rotation_rpy':[0.,.35,0.]}},
}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--child',action='store_true')
    parser.add_argument('--case',choices=['corner','combined_v4'])
    parser.add_argument('--candidate',choices=list(CANDIDATES))
    args=parser.parse_args()
    if hashlib.sha256(LIBRARY.read_bytes()).hexdigest()!=LIBRARY_SHA:
        raise RuntimeError('Frozen orchestration library changed')
    if not (FIRST/'complete.json').exists():
        raise RuntimeError('First campaign not complete; never overlap simulators')
    spec=importlib.util.spec_from_file_location('frozen_teacher_runner',LIBRARY)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=ROOT;module.OUT=OUT;module.CANDIDATES=CANDIDATES
    # Child invocations must return through this same pinned configuration.
    module.__file__=__file__
    if args.child:
        module.run_child(args)
        return
    OUT.mkdir(parents=True,exist_ok=True)
    plan=OUT/'followup_plan.json'
    declaration=dict(max_new_rollouts=4,candidates=CANDIDATES,
        rationale={
            'velocity025_stiff2':'Test smaller sustained-load offset at preserved damping ratio after velocity025 missed the fixed horizon.',
            'pair_average_pitch035':'Test SPD anisotropic force-to-tangential coupling with a fixed virtual frame; no surface normal, contact or scene input.'},
        library=str(LIBRARY),library_sha256=LIBRARY_SHA,
        interpreter=sys.executable,first_campaign_plan_sha256=hashlib.sha256((FIRST/'plan.json').read_bytes()).hexdigest(),
        original_reference=str(FIRST),promotion='corner task AND strict required before combined; no ESN training',
        environment_gate_actuator_changes=False,hidden_conditions_opened=False)
    if plan.exists():
        if json.loads(plan.read_text())!=declaration:raise RuntimeError('Follow-up plan changed')
    else:module.write(plan,declaration)
    for case in ['corner','combined_v4']:
        ref=OUT/case/'original';ref.parent.mkdir(parents=True,exist_ok=True)
        target=FIRST/case/'original'
        if ref.exists():
            if not ref.is_symlink() or ref.resolve()!=target.resolve():raise RuntimeError('Reference mismatch')
        else:ref.symlink_to(target,target_is_directory=True)
    module.campaign()


if __name__=='__main__':main()
