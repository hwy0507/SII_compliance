"""Execute an unchanged controller runner with optional read-only audit hooks."""
from __future__ import annotations
import argparse
from contextlib import nullcontext
import hashlib
import importlib
import json
from pathlib import Path
import runpy
import sys
import time
from physics_substep_metrics_20260923 import Instrumentation


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--runner',type=Path,required=True)
    p.add_argument('--metrics-output',type=Path,required=True)
    p.add_argument('--disable-audit',action='store_true')
    p.add_argument('--policy-transform')
    p.add_argument('--teacher-transform')
    p.add_argument('runner_args',nargs=argparse.REMAINDER)
    args=p.parse_args()
    if args.metrics_output.exists():raise FileExistsError('Metrics directory must be fresh')
    runner_args=args.runner_args[1:] if args.runner_args[:1]==['--'] else args.runner_args
    import current_student_policy_20260921 as loader
    original_load=loader.load_current
    import run_vmc_6d_constrained_push_20260918 as teacher_module
    original_teacher=teacher_module.CoreTeacher
    if args.policy_transform:
        module_name, function_name=args.policy_transform.split(':',1)
        transform=getattr(importlib.import_module(module_name),function_name)
        loader.load_current=lambda path:transform(original_load(path))
    if args.teacher_transform:
        module_name,function_name=args.teacher_transform.split(':',1)
        teacher_transform=getattr(importlib.import_module(module_name),function_name)
        teacher_module.CoreTeacher=lambda *a,**kw:teacher_transform(original_teacher(*a,**kw))
    previous=sys.argv
    started=time.monotonic()
    context=nullcontext() if args.disable_audit else Instrumentation()
    error=None
    try:
        sys.argv=[str(args.runner),*runner_args]
        with context:
            runpy.run_path(str(args.runner),run_name='__main__')
    except BaseException as exc:
        error=f'{type(exc).__name__}: {exc}'
        raise
    finally:
        sys.argv=previous
        loader.load_current=original_load
        teacher_module.CoreTeacher=original_teacher
        args.metrics_output.mkdir(parents=True,exist_ok=True)
        summaries=[]
        if not args.disable_audit:
            for i,episode in enumerate(context.episodes):
                summaries.append(episode.save(args.metrics_output/f'episode_{i}'))
        metadata=dict(runner=str(args.runner),runner_args=runner_args,enabled=not args.disable_audit,
                      error=error,wall_s=time.monotonic()-started,policy_transform=args.policy_transform,
                      teacher_transform=args.teacher_transform,
                      source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                     (Path(__file__),Path(__file__).with_name('physics_substep_metrics_20260923.py'),args.runner)},
                      episodes=summaries)
        (args.metrics_output/'audit_manifest.json').write_text(json.dumps(metadata,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
