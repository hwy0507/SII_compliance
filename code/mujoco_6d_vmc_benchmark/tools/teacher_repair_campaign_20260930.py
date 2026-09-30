"""Bounded teacher repair with immutable sources, paired worlds and raw audits.

One child simulator at a time. No ESN training unless teacher validation passes.
Run under systemd MemoryMax=3G/CPUQuota=100%; child also has RLIMIT_AS=3 GiB.
"""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import runpy
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/teacher_repair_canonical_20260930'
CANDIDATES = {
    'original': {},
    'velocity025': {'velocity_weight': .25},
    'pair_average': {'pair_average': True},
    'damping2': {'options': {'damping_6d': [56., 56., 110., 5.6, 4.8, 6.]}},
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def write(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def roughness(action):
    import numpy as np
    a = np.asarray(action)[-125:, 1:]
    valid = (np.abs(a[1:]) > .01) & (np.abs(a[:-1]) > .01)
    return dict(last5s_action_delta_rms=float(np.sqrt(np.mean(np.diff(a, axis=0)**2))),
                last5s_action_std=np.std(a, axis=0).tolist(),
                last5s_sign_flip_fraction=np.mean((a[1:]*a[:-1] < 0) & valid, axis=0).tolist())


def offline(runtime):
    import numpy as np
    sys.path.insert(0, str(runtime / 'scripts'))
    from vmc_teacher_stable_readout_20260930 import StableReadoutTeacher
    source = ROOT / 'outputs/combined_thick_corner_pillar_v1_teacher_v8_dt1e4_20260929/rollout.npz'
    with np.load(source) as z:
        wrench = z['observation'][:, 39:45]
        recorded = z['teacher_action']
    report = {'source_sha256': sha(source), 'rows': {},
              'limitation': 'Fixed-history replay is not a counterfactual physical rollout.'}
    for name, config in CANDIDATES.items():
        actor = StableReadoutTeacher(**config)
        actions = np.asarray([actor.act(w) for w in wrench])
        if name == 'original':
            np.testing.assert_array_equal(actions, recorded)
        # A constant input must converge, not sustain an internal 2-cycle.
        actor.reset()
        equilibrium = np.asarray([actor.act(np.array([2., -1., 3., .1, .2, -.1])) for _ in range(2000)])
        equilibrium_delta = float(np.max(np.abs(np.diff(equilibrium[-100:], axis=0))))
        if equilibrium_delta > 1e-10:
            raise AssertionError('Internal constant-input equilibrium not stable')
        actor.reset()
        np.testing.assert_array_equal(actor.act(np.zeros(6)), np.zeros(7))
        repeat = np.asarray([actor.act(w) for w in wrench])
        np.testing.assert_array_equal(repeat, actions)
        report['rows'][name] = dict(**roughness(actions), constant_input_delta=equilibrium_delta,
                                    default_replay_max_abs=float(np.max(np.abs(actions-recorded))))
    write(OUT / 'offline_audit.json', report)
    return report


def run_child(args):
    import numpy as np
    import mujoco
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
    runtime = OUT / 'source'
    sys.path.insert(0, str(runtime / 'scripts'))
    import run_vmc_6d_constrained_push_20260918 as vmc
    from vmc_teacher_stable_readout_20260930 import StableReadoutTeacher
    from wbc_velocity_residual_core import VelocityResidualActionFilter
    folder = OUT / args.case / args.candidate
    config = CANDIDATES[args.candidate]
    records, filter_records = [], []

    class RecordedTeacher(StableReadoutTeacher):
        def __init__(self, unused):
            if unused:
                raise ValueError('Unexpected evaluator configuration')
            super().__init__(**config)

        def act(self, wrench_world, dt=.04):
            action = super().act(wrench_world, dt)
            records.append(dict(wrench=np.asarray(wrench_world).copy(),
                                effective_wrench=self.effective_wrench.copy(),
                                original_readout=self.raw_action.copy(), requested_action=action.copy(),
                                offset=self.offset.copy(), velocity=self.velocity.copy(),
                                filtered_wrench=self.filtered.copy()))
            return action

    base_filter = VelocityResidualActionFilter.filter
    def record_filter(self, action, dt):
        result = base_filter(self, action, dt)
        filter_records.append(dict(submitted_action=np.asarray(action).copy(),
                                   clipped_action=result.raw_action_clipped.copy(),
                                   yield_twist=result.cartesian_yield_twist.copy(),
                                   wbc_scale=result.wbc_scale, slew_limited=result.slew_limited))
        return result
    vmc.SixDVirtualDynamics = RecordedTeacher
    VelocityResidualActionFilter.filter = record_filter
    # Assert identity at save time, before the first step, for paired fixtures.
    base_save = mujoco.mj_saveModel
    def checked_save(model, filename, buffer):
        base_save(model, filename, buffer)
        expected = OUT / args.case / 'original/rollout.mjb'
        if args.candidate != 'original' and expected.exists() and sha(filename) != sha(expected):
            raise AssertionError('Paired environment hash mismatch')
        if args.case == 'combined_v4':
            reference = ROOT / 'outputs/combined_thick_corner_pillar_v4_full55_dt1e4_20260929/rollout.mjb'
            if sha(filename) != sha(reference):
                raise AssertionError('Frozen combined-v4 MJB changed')
    mujoco.mj_saveModel = checked_save
    argv = ['--output', str(folder / 'rollout'), '--teacher', 'vmc6d',
            '--events', 'settle' if args.case == 'corner' else 'all',
            '--task', 'pick_place', '--corner-placement', '--duration', '55',
            '--dt', '0.0001', '--seed', '2026091751', '--variant', '0',
            '--ball-speed', '1.7', '--ball-launch-time-s', '2',
            '--person-stroke', '.2', '--rod-stroke', '.235',
            '--person-start', '3', '--rod-start', '7', '--rod-hold', '6']
    if args.case == 'combined_v4':
        argv += ['--combined-thick-corner-pillar-v4']
    write(folder / 'command.json', dict(evaluator_argv=argv, teacher=config,
                                      versions=dict(python=sys.version, numpy=np.__version__, mujoco=mujoco.__version__)))
    sys.argv = [str(runtime / 'scripts/validate_office_apparatus_v5_20260917.py'), *argv]
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
    finally:
        for name, rows in [('teacher_internal', records), ('execution_chain', filter_records)]:
            if rows:
                np.savez_compressed(folder / (name + '.npz'), **{k: np.asarray([r[k] for r in rows]) for k in rows[0]})


def audit(folder):
    import numpy as np
    sys.path.insert(0, str(OUT / 'source/scripts'))
    from vmc_teacher_stable_readout_20260930 import StableReadoutTeacher
    result = json.loads((folder / 'rollout.json').read_text())
    with np.load(folder / 'rollout.npz') as z:
        actor = StableReadoutTeacher(**CANDIDATES[folder.name])
        actions = np.asarray([actor.act(w) for w in z['observation'][:,39:45]])
        np.testing.assert_array_equal(actions, z['applied_action'])
        row = dict(**roughness(actions), final_error_m=float(z['task_position_error_m'][-1]),
                   task=result['task_success'], strict=result['strict_success'], stage=result['final_task_stage'])
    with np.load(folder / 'execution_chain.npz') as z:
        np.testing.assert_array_equal(actions, z['submitted_action'])
    with np.load(folder / 'rollout_metrics/substep_metrics.npz') as z:
        dt=z['dt'].astype(float); error=z['error'].astype(float)
        values=[float(np.sqrt(np.sum(error**2*dt[:,None])/dt.sum())),
                float(np.max(np.abs(z['qfrc_actuator']))),
                float(np.max(np.linalg.norm(z['twist'][:,:3].astype(float),axis=1)))]
        np.testing.assert_allclose(dt.sum(),55.,atol=1e-7,rtol=0)
    keys=['position_rmse_3d_m','generalized_actuator_torque_peak_nm','linear_speed_peak_mps']
    np.testing.assert_allclose(values,[result['metrics'][k] for k in keys],rtol=2e-7,atol=1e-8)
    row.update(dict(zip(keys,values)))
    row.update(external_penetration_mm=1000*result['stats']['max_external_penetration_m'],
               action_replay_max_abs=0., source_sha256=result['source_sha256'],
               files_sha256={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file() and p.suffix in ('.npz','.mjb','.xml')},
               events=result['stats']['events'], contact_diagnostics=result['stats'].get('contact_diagnostics'))
    write(folder/'audit.json',row)
    return row


def campaign():
    import mujoco
    if mujoco.__version__ != '3.11.0':
        raise RuntimeError('Frozen fixture requires .venv-canonical-rl and MuJoCo 3.11.0')
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / '.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not (OUT/'plan.json').exists():
            runtime = OUT/'source'
            for p in (ROOT/'scripts').rglob('*.py'):
                if any(x in ('.venv','__pycache__') for x in p.parts):
                    continue
                target=runtime/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(p,target)
            shutil.copytree(ROOT/'assets',runtime/'assets')
            (runtime/'tools').mkdir()
            shutil.copy2(__file__,runtime/'tools'/Path(__file__).name)
            hashes={str(p.relative_to(runtime)):sha(p) for p in runtime.rglob('*') if p.is_file()}
            write(OUT/'plan.json',dict(candidates=CANDIDATES, sources=hashes, seed=2026091751,
                interpreter=sys.executable, mujoco_version=mujoco.__version__,
                cases=['corner','combined_v4'], duration=55,dt=.0001,
                promotion='Each repaired candidate needs corner task AND strict; original combined is always a reference.',
                environment_gate_input_actuator_changes=False, memory_max_bytes=3*1024**3,
                max_simulations=8, threads=1, esn_training=False))
        plan=json.loads((OUT/'plan.json').read_text())
        for name,expected in plan['sources'].items():
            if sha(OUT/'source'/name)!=expected:
                raise AssertionError('Snapshot changed: '+name)
        # Verify the archived world BEFORE spending the corner regression budget.
        os.environ['MUJOCO_MENAGERIE_PATH']=str(ROOT/'outputs/canonical_rl_assets_20260923/menagerie')
        sys.path.insert(0,str(OUT/'source/scripts'))
        from audit_office_complex_scene_v5_20260917 import make
        from office_complex_scene_v5_20260917 import fixture_flags
        flags=fixture_flags(2026091751,0,corner_placement=True,combined_thick_corner_pillar_v4=True)
        flags.update(duration=55.,nominal_speed=.06,ball_speed=1.7)
        env,_,_=make(flags)
        env.model.opt.timestep=.0001
        mujoco.mj_saveModel(env.model,str(OUT/'preflight.mjb'),None)
        env.close()
        reference=ROOT/'outputs/combined_thick_corner_pillar_v4_full55_dt1e4_20260929/rollout.mjb'
        if sha(OUT/'preflight.mjb')!=sha(reference):
            raise AssertionError('Preflight frozen world mismatch; no new rollout started')
        write(OUT/'preflight.json',dict(passed=True,mujoco_version=mujoco.__version__,
              interpreter=sys.executable,world_sha256=sha(reference)))
        offline(OUT/'source')
        summary={}
        for case in ['corner','combined_v4']:
            for candidate in CANDIDATES:
                if case=='combined_v4' and candidate!='original':
                    earlier=summary['corner/'+candidate]
                    if not earlier.get('task') or not earlier.get('strict'):
                        summary[case+'/'+candidate]={'not_run':'corner task/strict not passed'}
                        write(OUT/'summary.json',summary)
                        continue
                folder=OUT/case/candidate;folder.mkdir(parents=True,exist_ok=True)
                if (folder/'execution.json').exists() and not (folder/'rollout.json').exists():
                    raise RuntimeError('Interrupted/failed attempt preserved; inspect before resuming '+str(folder))
                if not (folder/'rollout.json').exists():
                    cmd=[sys.executable,str(Path(__file__).resolve()),'--child','--case',case,'--candidate',candidate]
                    execution=dict(command=cmd, started=time.time(),status='running',plan_sha256=sha(OUT/'plan.json'))
                    write(folder/'execution.json',execution)
                    env=os.environ.copy()
                    env.update({k:'1' for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']})
                    env['MUJOCO_MENAGERIE_PATH']=str(ROOT/'outputs/canonical_rl_assets_20260923/menagerie')
                    with (folder/'run.log').open('w') as log:
                        proc=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
                        execution['pid']=proc.pid;write(folder/'execution.json',execution)
                        rc=proc.wait(timeout=7200)
                    execution.update(returncode=rc,finished=time.time(),status='completed' if rc==0 else 'failed')
                    write(folder/'execution.json',execution)
                    if rc:
                        raise RuntimeError('Child failed; preserved '+str(folder))
                summary[case+'/'+candidate]=audit(folder)
                write(OUT/'summary.json',summary)
                print(case,candidate,json.dumps({k:v for k,v in summary[case+'/'+candidate].items() if k not in ['files_sha256','events','source_sha256','contact_diagnostics']}),flush=True)
        write(OUT/'complete.json',dict(completed=time.time(),esn_training_started=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--child',action='store_true')
    p.add_argument('--offline',action='store_true');p.add_argument('--case',choices=['corner','combined_v4'])
    p.add_argument('--candidate',choices=list(CANDIDATES));args=p.parse_args()
    if args.child: run_child(args)
    elif args.offline:
        OUT.mkdir(parents=True,exist_ok=True);offline(ROOT)
    else: campaign()
