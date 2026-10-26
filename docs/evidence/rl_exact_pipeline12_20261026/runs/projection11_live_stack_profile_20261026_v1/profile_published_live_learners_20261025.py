"""Finite external stack sampling; does not alter live learner configuration."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(pid):
    stat=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
    return dict(start_ticks=stat[19], state=stat[0],
                cmdline=Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0',b' ').decode())


def main(registration):
    p=json.loads(registration.read_text())
    if sha(__file__)!=p['source_sha256'] or sha(p['profiler'])!=p['profiler_sha256']:
        raise ValueError('Registered profiling source drift')
    out=Path(p['output']);out.mkdir(exist_ok=False)
    os.sched_setaffinity(0,{p['cpu']});os.nice(10)
    children={};before={}
    for method,item in p['targets'].items():
        current=identity(item['pid'])
        if (current['state']=='Z' or current['start_ticks']!=item['start_ticks']
                or current['cmdline']!=item['cmdline']):
            raise ValueError('Registered live process identity changed')
        before[method]=json.loads(Path(item['progress']).read_text())
    for method,item in p['targets'].items():
        command=[p['profiler'],'record','--pid',str(item['pid']),
            '--duration',str(p['duration_s']),'--rate',str(p['rate_hz']),
            '--idle','--format','raw','--full-filenames','--output',str(out/(method+'.folded'))]
        with (out/(method+'.log')).open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        children[method]=child
    (out/'STARTED.json').write_text(json.dumps(dict(pid=os.getpid(),started_unix=time.time(),
        children={m:c.pid for m,c in children.items()},registration_sha256=sha(registration)),indent=2)+'\n')
    methods={}
    for method,child in children.items():
        code=child.wait()
        if code:
            raise RuntimeError(f'Profiler failed for {method}: {code}; retain existing jobs')
        path=out/(method+'.folded');total=0;leaves=Counter();inclusive=Counter()
        for line in path.read_text().splitlines():
            stack,n=line.rsplit(' ',1);n=int(n);frames=stack.split(';');total+=n
            leaves[frames[-1]]+=n
            for key,needles in dict(
                finite_check=['assert_finite_parameters ('],
                replay_sampling=['sample (','published_replay_device_cache'],
                backward=['backward ('],
                adam_step=['adam.py:'],
                selector_wait=['selectors.py:'],
                checkpoint=['checkpoint_now ('],
                learner_update=['update (','published_compliance_learner'],
                policy_action=['act (','published_compliance_learner']).items():
                if all(needle in stack for needle in needles):inclusive[key]+=n
        if not total:raise ValueError('Empty profiler sample set')
        item=p['targets'][method];current=identity(item['pid'])
        if current['start_ticks']!=item['start_ticks'] or current['state']=='Z':
            raise ValueError('Target did not remain the same live learner')
        after=json.loads(Path(item['progress']).read_text())
        methods[method]=dict(total_samples=total,raw_sha256=sha(path),
            top_leaf_frames=[dict(frame=f,samples=n,fraction=n/total) for f,n in leaves.most_common(20)],
            inclusive_fractions={k:n/total for k,n in inclusive.items()},
            before=before[method],after=after,
            observed_new_steps=after['steps']-before[method]['steps'],
            observed_new_updates=after['updates']-before[method]['updates'],
            target_identity_verified=True)
    (out/'SUMMARY.json').write_text(json.dumps(dict(methods=methods,
        registration_sha256=sha(registration),completed_unix=time.time(),
        diagnostic_optimizer_updates=0,new_physics_processes=0,training_configuration_changed=False,
        scope='External Python-stack sampling including idle threads; inclusive categories overlap. '
              'Frame presence is not CUDA kernel timing or proof of a throughput optimization. '
              'Sampling overhead and shared workload limit timing interpretation.'),indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True)
    main(parser.parse_args().registration)
