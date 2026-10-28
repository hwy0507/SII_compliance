"""Physical source-scene coverage without changing the original runtime.

Only ball initial hand position and loaded carry displacement vary. Original scene
geometry, IK, task transition gates, launch physics and safety limits remain.
Offsets are environment configuration, never additional actor observations.
"""
import ast
import importlib.util
import os
from pathlib import Path
import sys

import numpy as np


def settings(environ):
    initial = np.array([float(environ.get('VMC_COVERAGE_INITIAL_X_M','0')),
                        float(environ.get('VMC_COVERAGE_INITIAL_Y_M','0')),
                        float(environ.get('VMC_COVERAGE_INITIAL_Z_M','0'))])
    carry = np.array([float(environ.get('VMC_COVERAGE_CARRY_X_M','.085')),
                      float(environ.get('VMC_COVERAGE_CARRY_Y_M','.035')),0.])
    angle = float(environ.get('VMC_BALL_ANGLE_RAD','0'))
    if not np.isfinite(np.r_[initial,carry,angle]).all():
        raise ValueError('Nonfinite coverage configuration')
    if np.linalg.norm(initial) > .08 or not .04 <= np.linalg.norm(carry) <= .10:
        raise ValueError('Coverage outside initial80mm/carry40..100mm development bounds')
    if abs(angle) > np.pi/3:
        raise ValueError('Original ballistic launcher requires positive cos(angle), bounded to +/-60deg')
    return initial,carry


def install(module, initial, carry):
    layout, constructor = module.task_layout, module.BlindTask.__init__

    def task_layout(spec):
        start,goal = layout(spec)
        if spec.kind != 'ball':
            raise ValueError('This finite coverage adapter is ball-only')
        return start+initial,goal.copy()

    def initialize(self,*args,**kwargs):
        constructor(self,*args,**kwargs)
        if len(self.goals) == 6:
            self.goals[4] = self.goals[3]+carry
        elif len(self.goals) != 1:
            raise ValueError('Unexpected original ball task structure')

    module.task_layout = task_layout
    module.BlindTask.__init__ = initialize


def main():
    initial,carry = settings(os.environ)
    source = Path(__file__).with_name('run_primitive_teacher_v7_20260917.py')
    spec = importlib.util.spec_from_file_location('coverage_primitive_original',source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    install(module,initial,carry)
    tree = ast.parse(source.read_text())
    guard = tree.body[-1]
    assert isinstance(guard,ast.If)
    # Execute the original argument parser and run() without modifying its file.
    exec(compile(ast.Module(body=guard.body,type_ignores=[]),str(source),'exec'),module.__dict__)


if __name__ == '__main__':
    main()
