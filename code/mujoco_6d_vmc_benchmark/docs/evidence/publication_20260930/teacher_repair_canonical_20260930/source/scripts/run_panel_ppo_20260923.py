"""Independent loader wrapper for PPO; delegates physics to original panel main."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')


def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--ppo-normalizer',required=True,type=Path)
    parser.add_argument('--model',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--mixture',type=float,default=0.)
    args,remaining=parser.parse_known_args()
    if os.environ.get('UNIFIED_6D_TEACHER')!='1':
        raise ValueError('PPO deployment requires UNIFIED_6D_TEACHER=1 canonical48 observation')
    # teacher mixing must not silently convert the direct PPO baseline.
    if args.mixture!=0.:
        raise ValueError('Direct PPO requires mixture0')
    from canonical48_ppo_policy_20260923 import Canonical48PPO
    import current_student_policy_20260921 as loader
    policy=Canonical48PPO(args.model,args.ppo_normalizer)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fingerprint=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    metadata=dict(contract='proprio48_action7_6d_v1',policy='frozen SB3 PPO CPU',
        checkpoint=str(args.model.resolve()),checkpoint_sha256=fingerprint(args.model),
        normalizer=str(args.ppo_normalizer.resolve()),normalizer_sha256=fingerprint(args.ppo_normalizer),
        trained_timesteps=policy.model.num_timesteps,training_updates=policy.model._n_updates,
        normalization_frozen=True,observation_clip=policy.normalizer.clip_obs,
        actor_privileged_fields=[],teacher_mixture=0.,
        source_sha256={Path(__file__).name:fingerprint(__file__),
            'canonical48_ppo_policy_20260923.py':fingerprint(Path(__file__).with_name('canonical48_ppo_policy_20260923.py'))})
    args.output.with_suffix('.ppo_deployment.json').write_text(json.dumps(metadata,indent=2)+'\n')
    original_loader=loader.load_current
    def load(path):
        if Path(path).resolve()!=args.model.resolve():raise ValueError('Unexpected PPO checkpoint path')
        return policy
    loader.load_current=load
    sys.argv=[sys.argv[0],*remaining,'--model',str(args.model),'--output',str(args.output),'--mixture','0']
    try:
        from run_panel_push_20260920 import main as run
        run()
    finally:
        loader.load_current=original_loader
        policy.close()


if __name__=='__main__':main()
