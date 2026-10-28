"""Check actual original-task invariants and refuse an in-flight108 launch."""
import argparse
import ast
import importlib.util
from pathlib import Path
import subprocess
import sys

import numpy as np

from collect_special_scene_actions_20261028 import ROOT,sha,read,write
import run_primitive_coverage_20261029 as coverage
from primitive_contact_scene_v7_20260917 import SceneSpec
from prepare_special_frozen_test_20261028 import validate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    source=ROOT/'scripts/run_primitive_teacher_v7_20260917.py'
    spec=importlib.util.spec_from_file_location('coverage_check_original',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    start,goal=np.array([.54,0,.66]),np.array([.54,0,.425])
    constructor_args=(start,goal,np.diag([-1.,1.,-1.]),0,[7,8],[7,8])
    original=module.BlindTask(*constructor_args)
    functions=[module.BlindTask.update,module.BlindTask.sample,module.BlindTask.advance_gripper]
    layout=module.task_layout
    initial,carry=coverage.settings({});coverage.install(module,initial,carry)
    adapted=module.BlindTask(*constructor_args)
    for name,value in original.__dict__.items():
        if name=='goals':
            for a,b in zip(value,adapted.goals):np.testing.assert_array_equal(a,b)
        elif isinstance(value,np.ndarray):np.testing.assert_array_equal(value,adapted.__dict__[name])
        else:assert value==adapted.__dict__[name]
    assert functions==[module.BlindTask.update,module.BlindTask.sample,module.BlindTask.advance_gripper]
    for a,b in zip(layout(SceneSpec(kind='ball')),module.task_layout(SceneSpec(kind='ball'))):
        np.testing.assert_array_equal(a,b)
    for invalid in ({'VMC_COVERAGE_INITIAL_X_M':'.09'},
                    {'VMC_COVERAGE_CARRY_X_M':'0','VMC_COVERAGE_CARRY_Y_M':'0'},
                    {'VMC_BALL_ANGLE_RAD':'2'},{'VMC_COVERAGE_INITIAL_Z_M':'nan'}):
        try:coverage.settings(invalid)
        except ValueError:pass
        else:raise AssertionError(invalid)
    reg=read(args.probe/'REGISTRATION.json')
    assert len(reg['cases'])==reg['maximum_episodes']==8
    for case in reg['cases']:
        initial,carry=coverage.settings({k:str(v) for k,v in case['parameters'].items()})
        delta=goal+np.array([0,0,.175])-(start+initial)
        direction=delta/np.linalg.norm(delta)
        assert abs(np.abs(direction[:2]).max()-1)<1e-12 and abs(direction[2])<1e-12
        np.testing.assert_allclose(carry/np.linalg.norm(carry),direction,atol=1e-12,rtol=0)
    old=(ROOT/'tools/qualify_special_scene_demo_20261028.py').read_text()
    new=(ROOT/'tools/qualify_ball_coverage_demo_20261029.py').read_text()
    assert new==old.replace("wrapper = 'tools/run_video_reference_vmc_20261028.py'",
                            "wrapper = 'tools/run_video_reference_coverage_20261029.py'")
    for n,h in reg['source_sha256'].items():assert sha(ROOT/n)==h,n
    validate(ROOT/'outputs/special_scene_frozen108_preparation_20261029_v8')
    assert read(Path(reg['prerequisite_matrix'])/'execution.json')['status']=='running'
    refused=subprocess.run([sys.executable,str(ROOT/'tools/prepare_ball_coverage_probe_20261029.py'),
                            '--root',str(args.probe),'--run'],capture_output=True,text=True)
    assert refused.returncode!=0 and 'Original108 must finish first' in refused.stderr
    assert not (args.probe/'execution.json').exists()
    write(args.output,dict(status='static_invariants_and_actual_inflight_refusal_passed',
        registration_sha256=sha(args.probe/'REGISTRATION.json'),checker_sha256=sha(Path(__file__)),
        default_task_and_layout_exact=True,original_gate_functions_unchanged=True,
        qualification_only_wrapper_literal_changed=True,cardinal_cases=8,invalid_configs_rejected=4,
        original108_bindings_unchanged=True,refusal_stderr=refused.stderr,
        physical_steps=0,limitation='Static/default equivalence and launch refusal only. No physical reachability, ball-hand contact, qualification, training or success claim.'))
    print('static_invariants_and_actual_inflight_refusal_passed')


if __name__=='__main__':main()
