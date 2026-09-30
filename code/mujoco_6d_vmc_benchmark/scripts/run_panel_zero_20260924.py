"""Zero action7 reference using original task (never settle_only)."""
import os
import numpy as np


class ZeroPolicy:
    kind='zero_action7'
    def reset(self):pass
    def act(self,observation):
        observation=np.asarray(observation)
        if observation.shape!=(48,) or not np.isfinite(observation).all():
            raise ValueError('Expected finite canonical48')
        return np.zeros(7)


def main():
    import sys
    import current_student_policy_20260921 as loader
    if os.environ.get('UNIFIED_6D_TEACHER')!='1':raise ValueError('Requires canonical48')
    if '--model' in sys.argv or '--settle-only' in sys.argv:raise ValueError('Zero baseline controls action only')
    if '--mixture' in sys.argv and float(sys.argv[sys.argv.index('--mixture')+1])!=0:
        raise ValueError('Zero baseline requires mixture0')
    sys.argv.extend(['--model','zero_action7_in_memory'])
    original=loader.load_current
    loader.load_current=lambda _:ZeroPolicy()
    try:
        from run_panel_push_20260920 import main as run
        run()
    finally:loader.load_current=original


if __name__=='__main__':main()
