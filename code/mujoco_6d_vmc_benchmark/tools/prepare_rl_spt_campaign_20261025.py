"""Prepare, check and launch bounded local/server SPT-surrogate RL segments.

No work runs without the explicit run subcommand. Preparation freezes source,
parameter adapters, reward and parent conditions in a new directory. The
systemd child acquires compute leases, then starts one trainer. Server jobs
may share the legacy locks, but have exclusive GPU, CPU and five-slot leases.
"""
import argparse
import ast
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys

from spt_rl_reward_20261025 import CONFIG, validate_config
import spt_server_resources_20261025 as server

BENCH = Path(__file__).resolve().parents[1]
FORMAL = 'd4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3'
V6_BINARY_HASH = '173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11'
FAMILIES = {'direct': None, 'impedance': 'impedance', 'admittance': 'admittance', 'vmc': 'vmc'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def now():
    return datetime.now(timezone.utc)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def relocated_adapter(path, upstream):
    """Change only UPSTREAM in the new snapshot; preserve original adapter."""
    source = path.read_text()
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == 'UPSTREAM' for t in n.targets)]
    require(len(nodes) == 1, 'Adapter needs exactly one UPSTREAM assignment')
    node = nodes[0]; lines = source.splitlines(keepends=True)
    lines[node.lineno-1:node.end_lineno] = ['UPSTREAM = Path('+repr(str(upstream))+')\n']
    return ''.join(lines)


def prepare(a):
    root, parent, parameter, runtime = (p.resolve(strict=True) if i else p.resolve()
        for i, p in enumerate((a.root, a.parent, a.parameter_source, a.runtime)))
    require(not root.exists(), 'New run directory required; never overwrite receipts')
    require(1375 <= a.steps <= 1_000_000 and 1 <= a.dispatch_hours <= 168, 'Invalid finite budget')
    old = read(parent/'PROTOCOL.json')
    require(old['formal_model_sha256'] == FORMAL and old['physics_dt_s'] == .00005,
            'Parent physical contract differs')
    require(sha(parent/'CONDITIONS.json') == old['condition_file_sha256'], 'Parent conditions hash mismatch')
    conditions = read(parent/'CONDITIONS.json')['conditions']
    require(len([c for c in conditions if c['role']=='train']) == 32, 'Need registered 32 train identities')
    require(len({c['id'] for c in conditions}) == len(conditions), 'Duplicate condition identities')
    for path in (parent/'teacher.json', parameter/'PRIORS.json', parameter/'official_parameter_agent.py',
                 runtime/'v6/PROTOCOL.json', runtime/'v6/esn_original_v2/rollout.json',
                 runtime/'v6/construction/rollout.mjb',
                 runtime/'simba_reward_20260930/rewards.py'):
        require(path.is_file(), 'Missing runtime artifact: '+str(path))
    require(sha(runtime/'v6/construction/rollout.mjb') == V6_BINARY_HASH,
            'Frozen v6 binary hash mismatch (worker additionally checks formal dt model)')
    require((runtime/'menagerie').is_dir() and (runtime/'SimbaV2').is_dir(), 'Missing local assets/upstream')
    resources = dict(simulators=1,threads=1,memory_max_bytes=3*1024**3,swap_max_bytes=0,
                     cpu=a.cpu,server_compute=False,learning_backend='cpu',utd=1)
    if getattr(a, 'server_gpu', None) is not None:
        require(a.cpus is not None, 'Server mode requires explicit disjoint --cpus IDs')
        resources = server.register(a.server_gpu, a.cpus, a.memory_gib)
    adapter = relocated_adapter(parameter/'official_parameter_agent.py', runtime/'SimbaV2')
    root.mkdir(parents=True)
    for folder in ('scripts', 'tools', 'assets'):
        shutil.copytree(BENCH/folder, root/'source'/folder,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(parameter, root/'parameter', ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (root/'parameter/official_parameter_agent.py').write_text(adapter)
    for name in ('CONDITIONS.json','teacher.json'):
        shutil.copy2(parent/name, root/name)
    write(root/'REWARD_SPEC.json', CONFIG)
    cfg = read(BENCH/'configs/rl_spt_training_20261025.json')
    cfg['registered_resources'] = resources
    cfg['training_seeds'] = [a.seed]
    write(root/'TRAINING_PLAN.json', cfg)
    commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=BENCH, text=True).strip()
    # Capture dirty contents by hashes too; never label an uncommitted snapshot as clean.
    dirty = subprocess.check_output(['git','status','--porcelain'],cwd=BENCH,text=True)
    p = dict(schema='sii-baseline-strengthening-v1', campaign='spt_surrogate_v1',
        registered_utc=now().isoformat(), source_base_commit=commit, source_dirty=bool(dirty),
        parent_protocol_sha256=sha(parent/'PROTOCOL.json'), formal_model_sha256=FORMAL,
        physics_dt_s=.00005, duration_s=55., condition_file_sha256=sha(root/'CONDITIONS.json'),
        reward_spec_sha256=sha(root/'REWARD_SPEC.json'), reward_variants=['spt_v1'],
        budgets=dict(training_seeds=[a.seed],rl_steps_per_family_seed=a.steps),
        rl_hyperparameters={'spt_start':dict(entropy_coef=-.5, initial_temperature=.01)},
        training_dispatch_deadline_utc=(now()+timedelta(hours=a.dispatch_hours)).isoformat(),
        cooperative_stop_file=str(root/'STOP_REQUESTED'), min_free_disk_bytes=20*1024**3,
        runtime=str(runtime), python=str(Path(sys.executable).absolute()), host=platform.node(),
        source=str(root/'source'), parameter_source=str(root/'parameter'),
        resources=resources,
        adapter_relocation=dict(original_sha256=sha(parameter/'official_parameter_agent.py'),
                                snapshot_sha256=sha(root/'parameter/official_parameter_agent.py'),
                                only_change='UPSTREAM runtime path; algorithm unchanged'),
        dispatch_locks=[str(BENCH/'outputs/.v4_recovery_dispatch.lock'),
                        str(BENCH/'outputs/baseline_local_rl_20261009/.local-rl-compute.lock')],
        scope='Fresh pure online SimbaV2, no teacher labels/BC/old replay. Training surrogate only.',
        formal_evaluation_ready=False,
        outstanding=['gate-matched task completion timestamp','registered T_ref per condition',
                     'human comfort threshold calibration','physical telemetry parity preflight'])
    write(root/'PROTOCOL.json', p)
    tracked = [root/'PROTOCOL.json',root/'CONDITIONS.json',root/'teacher.json',
               root/'REWARD_SPEC.json',root/'TRAINING_PLAN.json']
    for folder in (root/'source',root/'parameter',runtime/'simba_reward_20260930',runtime/'v6',runtime/'SimbaV2'):
        tracked += [f for f in folder.rglob('*') if f.is_file() and f.suffix in ('.py','.json','.mjb','.yaml','.yml')]
    write(root/'INPUT_HASHES.json',{str(f):sha(f) for f in sorted(set(tracked))})
    write(root/'execution.json',dict(status='prepared_no_training',created_utc=now().isoformat()))
    print(json.dumps(dict(root=str(root),protocol_sha256=sha(root/'PROTOCOL.json'),status='prepared_no_training')))


def verify(root):
    p = read(root/'PROTOCOL.json')
    require(p['campaign']=='spt_surrogate_v1', 'Wrong campaign')
    validate_config(read(root/'REWARD_SPEC.json'))
    for name, digest in read(root/'INPUT_HASHES.json').items():
        require(sha(name)==digest, 'Input changed: '+name)
    require(p['host']==platform.node(), 'Prepare a fresh snapshot on the actual compute host')
    require(Path(p['python']).is_file(), 'Registered interpreter missing')
    return p


def command(root, p, family, limit, resume=None):
    require(family in FAMILIES, 'Unknown family')
    require(1375 <= limit <= p['budgets']['rl_steps_per_family_seed'], 'Invalid segment limit')
    output = root/family/f'segment_{limit:07d}'
    require(not output.exists(), 'Existing attempt must be preserved; use a new run/segment')
    argv = [p['python'],str(Path(p['source'])/'tools/train_v4_recovery_rl_20261016.py'),
        '--root',str(root),'--output',str(output),'--parameter-source',p['parameter_source'],
        '--reward','office_task' if family=='direct' else 'metric','--reward-variant','spt_v1',
        '--hyperparameter-id','spt_start','--seed',str(p['budgets']['training_seeds'][0]),
        '--steps',str(p['budgets']['rl_steps_per_family_seed']),'--stop-at-step',str(limit)]
    if FAMILIES[family]:
        argv += ['--controller',family]
    if resume:
        resume = resume.resolve(strict=True)
        require(resume.is_relative_to(root/family), 'Resume must be same family/cohort')
        require(read(resume.parent/'PROTOCOL.json')['spt_reward_spec']==CONFIG, 'Reward mismatch')
        argv += ['--resume-checkpoint',str(resume)]
    elif (root/family).exists():
        require(not any((root/family).glob('segment_*')), 'Existing family requires explicit checkpoint resume')
    return argv, output


def active_workers():
    require(len(list(Path('/proc').glob('[0-9]*')))>20, 'Host process view required')
    found=[]
    for d in Path('/proc').glob('[0-9]*'):
        try:
            args=(d/'cmdline').read_bytes().split(b'\0')
        except (OSError, ProcessLookupError):
            continue
        names=[Path(x.decode(errors='replace')).name for x in args[1:]]
        if any(n.startswith(('train_v4_recovery','train_baseline_repair','research72_train_rl',
                             'baseline_repair_worker','paper_office_worker','paper_classical_worker',
                             'research72_online_worker','validate_office_v5')) and n.endswith('.py') for n in names):
            found.append(int(d.name))
    return found


def dispatch(a):
    root=a.root.resolve();p=verify(root)
    require(now()<datetime.fromisoformat(p['training_dispatch_deadline_utc']), 'Dispatch deadline expired')
    require(not (root/'STOP_REQUESTED').exists(), 'Stop requested')
    locks=[]; stack=ExitStack()
    try:
        for path in p['dispatch_locks']:
            Path(path).parent.mkdir(parents=True,exist_ok=True)
            stream=Path(path).open('a');locks.append(stream)
            mode=fcntl.LOCK_SH if p['resources']['server_compute'] else fcntl.LOCK_EX
            fcntl.flock(stream,mode|fcntl.LOCK_NB)
        family_lock=(root/(a.family+'.lock')).open('a');locks.append(family_lock)
        fcntl.flock(family_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if p['resources']['server_compute']:
            locks += stack.enter_context(server.lease(p['resources'],root,a.family))
        else:
            require(not active_workers(), 'Existing worker(s): do not duplicate training')
        available=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()
                       if x.startswith('MemAvailable:'))
        require(available>=4*1024**3, 'Need at least 4 GiB available for one 3 GiB worker')
        require(shutil.disk_usage(root).free>=p['min_free_disk_bytes'], 'Disk reserve insufficient')
        argv,output=command(root,p,a.family,a.stop_at_step,a.resume_checkpoint)
        receipt=root/(a.family+f'_{a.stop_at_step:07d}.dispatch.json')
        require(not receipt.exists(), 'Dispatch receipt already exists; preserve failed attempt')
        state=dict(status='running',argv=argv,started_utc=now().isoformat(),output=str(output))
        write(receipt,state)
        with receipt.with_suffix('.log').open('x') as log:
            result=subprocess.run(argv,cwd=p['source'],stdout=log,stderr=subprocess.STDOUT,
                                  pass_fds=tuple(s.fileno() for s in locks))
        state.update(returncode=result.returncode,status='failed_preserved' if result.returncode else 'segment_closed',
                     ended_utc=now().isoformat())
        write(receipt,state)
        raise SystemExit(result.returncode)
    finally:
        stack.close()
        for stream in locks:stream.close()


def launch(a):
    root=a.root.resolve();p=verify(root)
    command(root,p,a.family,a.stop_at_step,a.resume_checkpoint)
    unit='sii-spt-'+hashlib.sha256(str(root).encode()).hexdigest()[:12]+'-'+a.family+f'-{a.stop_at_step}'
    env=dict(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
        MUJOCO_GL='egl',
        SII_LOCAL_RUNTIME=p['runtime'],MUJOCO_MENAGERIE_PATH=str(Path(p['runtime'])/'menagerie'),
        SII_RL_UTD='1',SII_REWARD_PAYLOAD_TELEMETRY='1',SII_SPT_REWARD_TELEMETRY='1',
        SII_SOURCE_BASE_COMMIT=p['source_base_commit'])
    env.update(server.environment(p['resources']))
    cpus=p['resources'].get('cpus',[p['resources'].get('cpu')])
    argv=['systemd-run','--user','--wait','--collect','--pipe','--unit='+unit,
          '--property=MemoryMax='+str(p['resources']['memory_max_bytes']),
          '--property=MemorySwapMax=0','--property=TasksMax=256',
          '--property=CPUAffinity='+' '.join(map(str,cpus)),'--working-directory='+p['source']]
    argv += ['--setenv='+k+'='+v for k,v in env.items()]
    argv += [p['python'],str(Path(p['source'])/'tools'/Path(__file__).name),'_dispatch',
             '--root',str(root),'--family',a.family,'--stop-at-step',str(a.stop_at_step)]
    if a.resume_checkpoint:argv+=['--resume-checkpoint',str(a.resume_checkpoint.resolve())]
    print(shlex.join(argv),flush=True)
    if not a.dry_run:raise SystemExit(subprocess.call(argv))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','matrix'):
        q=sub.add_parser(mode)
        for name in ('root','parent','parameter-source','runtime'):q.add_argument('--'+name,type=Path,required=True)
        q.add_argument('--steps',type=int,default=1_000_000);q.add_argument('--seed',type=int,default=20261025)
        q.add_argument('--dispatch-hours',type=int,default=72);q.add_argument('--cpu',type=int,default=1)
        q.add_argument('--server-gpu',help='Server GPU index or UUID, resolved to UUID at preparation')
        q.add_argument('--cpus',help='Server job CPU IDs, comma-separated, disjoint across concurrent jobs')
        q.add_argument('--memory-gib',type=int,default=8,help='Server job hard RAM limit; local remains 3 GiB')
        if mode=='matrix':
            q.add_argument('--gpu-devices',default='0,1,2,3,4')
            q.add_argument('--cpu-lanes',required=True,help='Semicolon-separated CPU lists, one per GPU')
            q.add_argument('--seeds',default='20261025,20261026,20261027')
    q=sub.add_parser('check');q.add_argument('--root',type=Path,required=True)
    for mode in ('run','_dispatch'):
        q=sub.add_parser(mode);q.add_argument('--root',type=Path,required=True)
        q.add_argument('--family',choices=FAMILIES,required=True)
        q.add_argument('--stop-at-step',type=int,default=11000)
        q.add_argument('--resume-checkpoint',type=Path);q.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    if a.mode=='prepare':prepare(a)
    elif a.mode=='matrix':
        from copy import copy
        base=a.root.resolve();require(not base.exists(),'New matrix directory required')
        devices=a.gpu_devices.split(',');cpus=a.cpu_lanes.split(';');seeds=[int(x) for x in a.seeds.split(',')]
        require(1<=len(devices)<=5 and len(cpus)==len(devices),'Need 1..5 GPUs with matching CPU lanes')
        require(1<=len(seeds)<=8 and len(set(seeds))==len(seeds),'Need 1..8 distinct seeds')
        resources=[server.register(d,c,a.memory_gib) for d,c in zip(devices,cpus)]
        require(len({r['gpu_uuid'] for r in resources})==len(resources),'Duplicate GPU')
        all_cpus=[c for r in resources for c in r['cpus']]
        require(len(set(all_cpus))==len(all_cpus),'CPU lanes overlap')
        base.mkdir(parents=True);jobs=[]
        for seed in seeds:
            for family in FAMILIES:
                lane=len(jobs)%len(devices);job=copy(a)
                job.root=base/f'{family}_seed{seed}';job.seed=seed
                job.server_gpu=resources[lane]['gpu_uuid'];job.cpus=cpus[lane]
                prepare(job)
                jobs.append(dict(root=str(job.root),family=family,stop_at_step=1375))
        write(base/'PILOT_JOBS.json',jobs)
        print('Prepared only; no training. Pilot jobs: '+str(base/'PILOT_JOBS.json'))
    elif a.mode=='check':verify(a.root.resolve());print('Input hashes valid; no simulation/gradient executed')
    elif a.mode=='run':launch(a)
    else:dispatch(a)


if __name__=='__main__':main()
