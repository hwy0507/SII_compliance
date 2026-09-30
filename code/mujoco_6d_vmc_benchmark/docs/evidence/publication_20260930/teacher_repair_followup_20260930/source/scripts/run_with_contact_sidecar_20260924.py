"""Outer wrapper for an unchanged frozen runner, with contact audit on/off."""
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time


def main():
    p=argparse.ArgumentParser();p.add_argument('--runner',type=Path,required=True)
    p.add_argument('--contact-output',type=Path,required=True);p.add_argument('--disable-contact',action='store_true')
    p.add_argument('--frozen-scripts',type=Path,required=True);p.add_argument('runner_args',nargs=argparse.REMAINDER)
    a=p.parse_args();a.contact_output.mkdir(parents=True,exist_ok=False)
    # Import canonical environment/policy from frozen scripts, audit from this
    # separate directory. No frozen source file is edited or shadowed.
    sys.path.insert(0,str(a.frozen_scripts.resolve()))
    from contact_substep_sidecar_20260924 import ContactInstrumentation
    context=nullcontext() if a.disable_contact else ContactInstrumentation(a.contact_output)
    previous=sys.argv;error=None;started=time.monotonic()
    try:
        rest=a.runner_args[1:] if a.runner_args[:1]==['--'] else a.runner_args
        sys.argv=[str(a.runner),*rest]
        with context:runpy.run_path(str(a.runner),run_name='__main__')
    except BaseException as exc:error=f'{type(exc).__name__}: {exc}';raise
    finally:
        sys.argv=previous
        summaries=[] if a.disable_contact else [episode.save() for episode in context.episodes]
        sources=[Path(__file__),Path(__file__).with_name('contact_substep_sidecar_20260924.py'),a.runner]
        manifest=dict(enabled=not a.disable_contact,error=error,wall_s=time.monotonic()-started,episodes=summaries,
            source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
        (a.contact_output/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
