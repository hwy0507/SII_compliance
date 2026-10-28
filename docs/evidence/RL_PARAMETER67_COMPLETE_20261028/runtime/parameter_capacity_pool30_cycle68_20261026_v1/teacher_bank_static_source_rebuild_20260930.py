"""Rebuild one frozen training model through real initialization, never step it.

All MuJoCo integration entrypoints fail-fast. First model save is intercepted
after the original initialization and ends execution before any episode step.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys
import traceback

from teacher_bank_asset_audit_20260930 import collect_robot_assets, sha


class FirstModelSaved(BaseException):pass


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--category',choices=('passive_corner','active_short','active_long'),required=True)
    parser.add_argument('--anchor',type=int,choices=(0,337,671),required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root,output=args.run.resolve(),args.output.resolve()
    if output.exists() or output==root or root in output.parents:
        raise ValueError('Require new external output directory')
    folder=root/f'search/{args.category}/vmc/c00/{args.anchor}'
    plan=json.loads((root/'plan.json').read_text())
    request=json.loads((folder/'request.json').read_text())
    audit=json.loads((folder/'audit.json').read_text())
    if request['fixture']['split']!='train' or request['fixture']['category']!=args.category:
        raise AssertionError('Only training anchors permitted')
    if request['plan_sha256']!=sha(root/'plan.json'):
        raise AssertionError('Plan hash mismatch')
    for name,digest in plan['sources'].items():
        if sha(root/'source'/name)!=digest:raise AssertionError('Frozen source drift: '+name)
    for name in ('request.json','rollout.mjb'):
        if sha(folder/name)!=audit['files_sha256'][name]:raise AssertionError('Original artifact drift: '+name)
    manifest=collect_robot_assets(args.assets)
    output.mkdir(parents=True)
    os.environ['MUJOCO_MENAGERIE_PATH']=str(args.assets.resolve())
    sys.path.insert(0,str(root/'source/tools'))
    sys.path.insert(0,str(root/'source/scripts'))
    import mujoco
    if mujoco.__version__!=plan['mujoco_version']:raise RuntimeError('MuJoCo version mismatch')
    report=dict(scope='Frozen runner true initialization; no integration allowed; first save terminates before episode',
        source_run=str(root),original_folder=str(folder),category=args.category,anchor=args.anchor,
        request_sha256=sha(folder/'request.json'),plan_sha256=sha(root/'plan.json'),
        original_mjb_sha256=sha(folder/'rollout.mjb'),complete_asset_manifest=manifest,
        mujoco_version=mujoco.__version__,python=sys.executable,
        script_sha256=sha(Path(__file__)),integration_calls_rejected=[],resource_override_requests=[],
        actual_as_limit_bytes=resource.getrlimit(resource.RLIMIT_AS),initialization_complete=False,
        explicit_model_overrides='None added by review; only frozen source initialization is executed')
    def reject(name):
        def forbidden(*unused,**kwargs):
            report['integration_calls_rejected'].append(name)
            raise RuntimeError('Forbidden integration during static rebuild: '+name)
        return forbidden
    for name in ('mj_step','mj_step1','mj_step2'):
        setattr(mujoco,name,reject(name))
    original_setrlimit=resource.setrlimit
    def limits(which,value):
        if which==resource.RLIMIT_AS:
            report['resource_override_requests'].append(list(value))
            # Frozen runner asks for 3 GiB; keep this audit's stricter host limit.
            return
        return original_setrlimit(which,value)
    resource.setrlimit=limits
    original_save=mujoco.mj_saveModel
    def capture(model,path,buffer):
        if Path(path).resolve()!=output/'rollout.mjb':raise AssertionError('Unexpected model output')
        original_save(model,path,buffer)
        report['rebuilt_mjb_sha256']=sha(Path(path))
        report['byte_identical']=report['rebuilt_mjb_sha256']==report['original_mjb_sha256']
        report['initialization_complete']=True
        raise FirstModelSaved()
    mujoco.mj_saveModel=capture
    try:
        spec=importlib.util.spec_from_file_location('frozen_static_runner',root/'source/tools/teacher_bank_rollout_20260930.py')
        runner=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        runner.rollout(root,request,output)
        raise AssertionError('Runner returned without reaching first model save')
    except FirstModelSaved:
        report['status']='matched' if report['byte_identical'] else 'model_mismatch'
    except Exception as error:
        report['status']='initialization_failed'
        report['error_type']=type(error).__name__
        report['error']=str(error)
        report['traceback']=traceback.format_exc()
    report['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (output/'review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (output/'files_sha256.json').write_text(json.dumps({p.name:sha(p) for p in output.iterdir() if p.is_file()},indent=2)+'\n')
    print(json.dumps({k:report.get(k) for k in ('status','error','byte_identical','integration_calls_rejected','peak_rss_kib')}),flush=True)
    if report['status']!='matched':sys.exit(1)


if __name__=='__main__':main()
