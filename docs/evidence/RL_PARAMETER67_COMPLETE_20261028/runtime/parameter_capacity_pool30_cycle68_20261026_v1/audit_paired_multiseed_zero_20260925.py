"""Compare new seed zero controls with the same-mode original seed zero episodes."""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path
import traceback

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('frozen-source','reference-run','current-run','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--mode',choices=('parameter6','direct7'),required=True)
    p.add_argument('--seed',type=int,choices=(20260924,20260925),required=True)
    args=p.parse_args()
    entry=args.frozen_source/'tools/run_canonical48_paired_ppo_20260924.py'
    spec=importlib.util.spec_from_file_location('original_frozen_comparator',entry)
    frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
    report=dict(mode=args.mode,seed=args.seed,reference_seed=20260923,
        reference_run=str(args.reference_run),current_run=str(args.current_run),
        observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        audit_tool_sha256=frozen.sha(__file__),frozen_comparator_sha256=frozen.sha(entry),
        comparisons={},input_sha256={})
    try:
        for run,expected in ((args.reference_run,20260923),(args.current_run,args.seed)):
            manifest=json.loads((run/'manifest.json').read_text())
            complete=json.loads((run/'COMPLETE.json').read_text())
            if manifest['training']['seed']!=expected or manifest['mode']!=args.mode or complete['status']!='complete' or (run/'FAILED.json').exists():
                raise ValueError('Wrong/incomplete training branch or seed')
            for name in ('manifest.json','COMPLETE.json'):report['input_sha256'][str(run/name)]=frozen.sha(run/name)
        for split in ('train','validation'):
            reference=args.reference_run/'eval'/split/'zero/episode_00000'
            current=args.current_run/'eval'/split/'zero/episode_00000'
            # The original comparator's direct7 branch is the strict same-log
            # path: compare actor_trace as well and allow only output-path drift.
            # It does not reinterpret a6 as a7: both transitions are also compared
            # key-by-key below, including their true shape and parameter state.
            result=frozen.compare_episode(reference,current,'direct7')
            with frozen.np.load(reference/'transitions.npz',allow_pickle=False) as a,frozen.np.load(current/'transitions.npz',allow_pickle=False) as b:
                if set(a.files)!=set(b.files):raise ValueError('Transition keys differ')
                result['transition_arrays']={key:frozen.finite_exact(a[key],b[key],split+':'+key) for key in a.files}
                expected_dim=6 if args.mode=='parameter6' else 7
                if b['policy_action'].shape!=(600,expected_dim):raise ValueError('Wrong zero policy dimension')
                if args.mode=='parameter6' and frozen.np.any(b['log_scale']):raise ValueError('Zero6 nominal gain drift')
            for folder in (reference,current):
                for f in sorted(folder.iterdir()):
                    if f.is_file():report['input_sha256'][str(f)]=frozen.sha(f)
            report['comparisons'][split]=result
        report['passed']=True
        report['all_zero_episodes_full600']=True
        report['same_mode_zero_comparison']=True
    except BaseException as error:
        report.update(passed=False,error=repr(error),traceback=traceback.format_exc())
        raise
    finally:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
        print(json.dumps({k:report[k] for k in ('passed','seed','mode')}))

if __name__=='__main__':main()
