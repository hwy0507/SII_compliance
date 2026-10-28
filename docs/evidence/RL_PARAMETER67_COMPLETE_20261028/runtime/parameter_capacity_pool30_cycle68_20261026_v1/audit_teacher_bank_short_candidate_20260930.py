"""Read-only paired c03/c00 short-impact training search audit. No simulation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys

import numpy as np

from teacher_bank_pilot_failure_causes_20260930 import analyze_case, sha


def read(path):
    return json.loads(path.read_text())


def json_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def rebound_evidence(folder, fixture, meta):
    axis=np.asarray(fixture['axis'],dtype=float)
    with np.load(folder/'rollout_ball_detail.npz',allow_pickle=False) as data:
        times,velocity,contact=data['time'],data['velocity'],data['contact'].astype(bool)
        if not contact.any():
            raise AssertionError('No recorded ball contact')
        last=float(times[contact].max())
        mask=(~contact)&(times>last)&(times<last+.12)
        if not mask.any():
            raise AssertionError('No saved outgoing velocity')
        incoming=float(np.asarray(meta['ball_incoming_velocity'])@axis)
        outgoing=float((velocity[mask]@axis).min())
        return dict(first_saved_contact_s=float(times[contact].min()),last_saved_contact_s=last,
            incoming_metadata_projected_mps=incoming,min_outgoing_saved_projected_mps=outgoing,
            reversal_witness=bool(incoming>.05 and outgoing<-.05),
            scope='Outgoing velocity reversal from saved sampled detail, incoming from evaluator metadata; not resimulated')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root,output=args.run.resolve(),args.output.resolve()
    if output.exists() or output==root or root in output.parents:
        raise ValueError('Require new output directory outside immutable run')
    plan=read(root/'plan.json')
    plan_hash=sha(root/'plan.json')
    if sha(root/'fixtures.json')!=plan['fixtures_sha256']:
        raise AssertionError('Fixture manifest hash mismatch')
    source_hashes={name:sha(root/'source'/name) for name in plan['sources']}
    if source_hashes!=plan['sources']:
        raise AssertionError('Frozen source snapshot drift')
    fixtures={f['id']:f for f in read(root/'fixtures.json') if f['split']=='train'}
    sys.path.insert(0,str(root/'source/tools'))
    spec=importlib.util.spec_from_file_location('frozen_short_candidate_runner',root/'source/tools/teacher_bank_rollout_20260930.py')
    runner=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    from teacher_bank_design_20260930 import decode, digest
    output.mkdir(parents=True)
    results={}
    paired={}
    for candidate in ('c00','c03'):
        base=root/'search/active_short/vmc'/candidate
        decision=read(base/'decision.json')
        cases={}
        teacher=None
        for anchor in (0,337,671):
            folder=base/str(anchor)
            request,execution,meta=map(read,(folder/'request.json',folder/'execution.json',folder/'rollout.json'))
            fixture=request['fixture']
            if (decode(decision['x'])!=request['teacher']
                    or digest(fixture['active_physical_parameters'])!=fixture['physical_config_sha256']):
                raise AssertionError('Decoded teacher or physical config hash mismatch')
            if (request['x']!=decision['x'] or request['plan_sha256']!=plan_hash
                    or execution['plan_sha256']!=plan_hash or execution['status']!='completed'
                    or execution['returncode']!=0 or fixture!=fixtures.get(fixture['id'])
                    or fixture['category']!='active_short' or request['method']!='vmc'
                    or request['phase']!='search'):
                raise AssertionError('Candidate/request/fixture/execution binding mismatch')
            if teacher is not None and teacher!=request['teacher']:
                raise AssertionError('Teacher differs across candidate anchors')
            teacher=request['teacher']
            original_hash=sha(folder/'audit.json')
            independent=analyze_case(folder)
            audit=independent['audit']
            repeated=runner.audit(root,request,folder,output_path=output/f'{candidate}_{anchor}_replay_audit.json')
            for key in ('eligible','failure_reasons','substeps','model_sha256'):
                if repeated[key]!=audit[key]:
                    raise AssertionError('Replayed audit disagreement: '+key)
            for key in ('rmse_m','peak_torque_nm','peak_speed_mps'):
                np.testing.assert_allclose(independent['raw_physical_metrics'][key],audit[key],rtol=2e-7,atol=1e-8)
            if audit['model_sha256']!=sha(folder/'rollout.mjb'):
                raise AssertionError('Compiled model hash mismatch')
            pair=(fixture,audit['model_sha256'])
            if candidate=='c00':paired[anchor]=pair
            elif paired[anchor]!=pair:raise AssertionError('Candidate environments not paired')
            with np.load(folder/'exposure.npz',allow_pickle=False) as exposure:
                force=exposure['force'].astype(float)
                dt=exposure['dt'].astype(float)
                peaks=exposure['force_peak'].astype(float)
            contact_load=dict(peak_of_saved_sum_force_n=float(peaks.max()),
                    impulse_from_saved_force_integral_ns=float(np.sum(force*dt)),
                    source='exposure.npz: max(force_peak), sum(force*dt)',
                    scope='Independent aggregation of preserved physical-substep peak/integral buckets; not contact-force reconstruction from dynamics. Sum of thresholded obstacle-robot contact magnitudes may differ from evaluator per-event definitions.')
            penetration=float(meta['stats']['max_external_penetration_m'])*1000
            if penetration!=audit['penetration_mm']:
                raise AssertionError('Penetration metadata mismatch')
            rebound=rebound_evidence(folder,fixture,meta)
            if candidate=='c03' and not (audit['eligible'] and repeated['eligible'] and rebound['reversal_witness']):
                raise AssertionError('c03 admitted/rebound claim not supported')
            if sha(folder/'audit.json')!=original_hash:
                raise AssertionError('Original audit changed')
            cases[str(anchor)]=dict(fixture_id=fixture['id'],fixture_seed=fixture['seed'],shape=fixture['object_shape'],
                request_sha256=sha(folder/'request.json'),controller_config_canonical_sha256=json_sha(request['teacher']),
                physical_config_sha256=fixture['physical_config_sha256'],independent=independent,
                frozen_runner_replay=repeated,rebound_evidence=rebound,contact_load=contact_load,
                evaluator_ball_event=meta['stats']['events']['ball'],
                penetration=dict(external_mm=penetration,source='hash-verified rollout.stats',
                    independently_recomputed=False,
                    limitation='Raw trace lacks every-substep contact distances and full state; cannot independently recompute maximum penetration without a new dynamics/kinematics replay.'),
                original_audit_sha256=original_hash,original_audit_unchanged=True)
            print(json.dumps(dict(candidate=candidate,anchor=anchor,eligible=audit['eligible'],peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
        results[candidate]=dict(decision=decision,decision_sha256=sha(base/'decision.json'),teacher=teacher,
            eligible_count=sum(c['independent']['audit']['eligible'] for c in cases.values()),total=3,cases=cases)
    result=dict(scope='Paired c00 initial and c03 single-parameter training search on exactly three anchors; no validation accessed, no generalization or locked-bank claim. Development dt from frozen plan; not formal dt=5e-5 certification.',
        metric_scope='Independent stage-waypoint RMSE / actuator torque peak / endpoint speed peak from saved physical substeps. Shared frozen implementation independently replays VMC action/filter/state; penetration is metadata-only verification.',
        run=str(root),plan_sha256=plan_hash,fixtures_sha256=plan['fixtures_sha256'],
        frozen_source_sha256=source_hashes,base_git_commit=plan['base_git_commit'],
        script_sha256=sha(Path(__file__)),independent_helper_sha256=sha(Path(__file__).with_name('teacher_bank_pilot_failure_causes_20260930.py')),
        compute_python=sys.executable,frozen_execution_python=plan['python'],dt=plan['dt'],formal=plan['formal'],
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        candidates=results)
    path=output/'review.json'
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    manifest={p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    (output/'files_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(output=str(path),sha256=sha(path),peak_rss_kib=result['peak_rss_kib'])))


if __name__=='__main__':main()
