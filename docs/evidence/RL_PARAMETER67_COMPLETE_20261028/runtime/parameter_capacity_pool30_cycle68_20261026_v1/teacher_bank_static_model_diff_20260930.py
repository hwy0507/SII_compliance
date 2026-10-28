"""Reproduce static compiled-model differences; never integrate either model.

Array differences, including BVH permutations, do not by themselves establish
different physical scenarios, hardware faults, or closed-loop nonequivalence.
"""
import argparse
import json
from pathlib import Path
import platform

from teacher_bank_asset_audit_20260930 import model_differences, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',type=Path,required=True)
    p.add_argument('--rebuilt',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError('Refusing to replace existing evidence')
    import mujoco
    rejected=[]
    def forbid(*args,**kwargs):
        rejected.append('integration_attempt')
        raise RuntimeError('Integration is prohibited in static model comparison')
    mujoco.mj_step=mujoco.mj_step1=mujoco.mj_step2=forbid
    original=mujoco.MjModel.from_binary_path(str(a.original))
    rebuilt=mujoco.MjModel.from_binary_path(str(a.rebuilt))
    differences=model_differences(original,rebuilt)
    value=dict(scope=__doc__,host=platform.node(),architecture=platform.machine(),
        mujoco_version=mujoco.__version__,original_path=str(a.original.resolve()),
        rebuilt_path=str(a.rebuilt.resolve()),original_sha256=sha(a.original),
        rebuilt_sha256=sha(a.rebuilt),differences=differences,different_fields=len(differences),
        no_dynamic_steps=True,integration_calls_rejected=rejected,script_sha256=sha(__file__),
        collection_authorized_by_this_report=False)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
