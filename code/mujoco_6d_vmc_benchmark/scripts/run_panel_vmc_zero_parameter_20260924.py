"""Nominal-VMC-equivalent zero parameter policy; no learned RL policy here."""
import argparse
import json
import os
from pathlib import Path
import sys
import numpy as np
from canonical48_vmc_tuning_20260924 import Canonical48VMCTuning


class ZeroParameterPolicy:
    kind='vmc_zero_parameter6'
    def __init__(self):
        self.controller=Canonical48VMCTuning(json.loads(os.environ['CORE_VMC_CONFIG']))
        self.controller.reset()
        self.log={k:[] for k in ('observation','parameter_request','log_scale','stiffness','damping','action')}
    def act(self,observation):
        parameter=np.zeros(6)
        action=self.controller.act(observation,parameter)
        values=dict(observation=observation,parameter_request=parameter,
            log_scale=self.controller.log_scale,stiffness=self.controller.base.k,
            damping=self.controller.base.b,action=action)
        for key,value in values.items():self.log[key].append(np.asarray(value).copy())
        return action


def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mixture',type=float,default=0.)
    args,remaining=parser.parse_known_args()
    if args.mixture!=0 or '--model' in remaining or '--settle-only' in remaining:
        raise ValueError('Zero-parameter parity requires original task and pure policy path')
    if os.environ.get('UNIFIED_6D_TEACHER')!='1':raise ValueError('Requires canonical48')
    import current_student_policy_20260921 as loader
    policy=ZeroParameterPolicy();original=loader.load_current
    loader.load_current=lambda _:policy
    sys.argv=[sys.argv[0],*remaining,'--output',str(args.output),'--mixture','0','--model','zero_parameter_vmc_in_memory']
    try:
        from run_panel_push_20260920 import main as run
        run()
    finally:
        loader.load_current=original
        args.output.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(args.output.parent/'vmc_parameter_trace.npz',
            **{key:np.asarray(value) for key,value in policy.log.items()})


if __name__=='__main__':main()
