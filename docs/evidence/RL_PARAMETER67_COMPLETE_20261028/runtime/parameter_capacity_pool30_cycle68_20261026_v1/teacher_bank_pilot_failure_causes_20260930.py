"""Offline v8 pilot attribution; never simulates or revises admission gates.

Uses saved task transitions for impact phase and saved 4 ms hand positions for
macro person displacement. The latter is diagnostic, not schema2 certification.
Writes once outside the immutable source run; hashes every audited raw artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text())


def phase_at(events, time):
    return next((event['stage'] for event in reversed(events)
                 if event['time_s'] <= time), 'approach')


def analyze_case(folder):
    audit, request, meta = (read(folder/name) for name in
                            ('audit.json', 'request.json', 'rollout.json'))
    names = set(audit['files_sha256']) | {'audit.json', 'request.json', 'execution.json'}
    hashes = {name: sha(folder/name) for name in sorted(names)}
    mismatches = [name for name, value in audit['files_sha256'].items()
                  if hashes[name] != value]
    if mismatches:
        raise ValueError(f'{folder}: raw hash mismatch {mismatches}')
    result = dict(fixture=request['fixture'], method=request['method'],
                  controller=request.get('teacher'), audit=audit,
                  hashes_sha256=hashes, all_audited_hashes_verified=True,
                  task_events=meta['task_events'], final_stage=meta['final_task_stage'],
                  abort_reason=meta['abort_reason'], release_supported=meta['release_supported'])
    xml = ET.parse(folder/'rollout.xml')
    result['xml_geometry'] = {name: dict(xml.find(f".//geom[@name='{name}']").attrib)
                              for name in ('office_v5_corner_top', 'target_object_geom')}
    with np.load(folder/'rollout_metrics/substep_metrics.npz', allow_pickle=False) as physical:
        dt = physical['dt'].astype(float)
        measured = dict(rmse_m=float(np.sqrt(np.sum(
            np.sum(physical['error'].astype(float)**2, axis=1)*dt)/dt.sum())),
            peak_torque_nm=float(np.max(np.abs(physical['qfrc_actuator']))),
            peak_speed_mps=float(np.max(np.linalg.norm(
                physical['twist'][:, :3].astype(float), axis=1))),
            physical_sample_count=len(dt), physical_duration_s=float(dt.sum()))
        result['raw_physical_metrics'] = measured
        result['metric_minus_saved_audit'] = {
            key: measured[key]-audit[key]
            for key in ('rmse_m', 'peak_torque_nm', 'peak_speed_mps')}
    with np.load(folder/'rollout.npz', allow_pickle=False) as raw, np.load(
            folder/'exposure.npz', allow_pickle=False) as exposure:
        times = raw['time']
        def sample(t):
            index = int(np.argmin(abs(times-t)))
            obj, hand = raw['object_position'][index], raw['hand'][index]
            return dict(requested_time_s=float(t), time_s=float(times[index]),
                        post_sample_stage=int(raw['stage'][index]),
                        task_position_error_m=float(raw['task_position_error_m'][index]),
                        object_xyz_m=obj.tolist(), hand_xyz_m=hand.tolist(),
                        object_hand_distance_m=float(np.linalg.norm(obj-hand)),
                        object_destination_xy_error_m=float(np.linalg.norm(
                            obj[:2]-np.array(meta['placement_destination'])[:2])))
        first = audit['exposure']['diagnostics']['first_contact_s']
        result['exposure_schema'] = int(exposure['schema'])
        result['first_contact_phase_from_events'] = phase_at(meta['task_events'], first)
        result['samples'] = [sample(t) for t in
            (first-.08, first+.08, first+1, 15, 25, 40, 42.32, 42.84, 43.48, 55)]
        result['transition_samples'] = {e['stage']: sample(e['time_s'])
                                        for e in meta['task_events']}
        late = (times >= 15) & (times <= 55+1e-6)
        result['late_min_task_position_error_m'] = float(
            raw['task_position_error_m'][late].min())
        if request['fixture']['category'] == 'active_short':
            mask = (times >= first) & (times <= first+.5)
            result['post_impact_half_second_object_z_range_m'] = [
                float(raw['object_position'][mask, 2].min()),
                float(raw['object_position'][mask, 2].max())]
            result['ball_rebound'] = meta['ball_rebound']
            result['ball_launch_time_s'] = meta['ball_launch_time_s']
        if request['fixture']['category'] == 'active_long':
            if request['fixture']['apparatus'] != 'person':
                raise ValueError('This attribution only implements person diagnostics')
            fixture = request['fixture']
            retract = fixture['start_s']+fixture['press_s']+fixture['hold_s']
            # Use last 4 ms sample strictly before first force-bearing contact.
            before = np.flatnonzero(exposure['time'] < first)
            origin = exposure['hand'][before[-1]]
            mask = (exposure['time'] >= first) & (exposure['time'] <= retract)
            delta = exposure['hand'][mask]-origin
            push = -np.array(fixture['axis'], dtype=float)
            push /= np.linalg.norm(push)
            signed = delta@push
            tangent = np.linalg.norm(delta-signed[:, None]*push, axis=1)
            runs = exposure['contact_runs']
            in_window = runs[(runs[:, 0] >= fixture['start_s']) & (runs[:, 1] <= retract)]
            gaps = in_window[1:, 0]-in_window[:-1, 1]
            result['person_macro_diagnostic_not_gate'] = dict(
                resolution_s=.004, origin_time_s=float(exposure['time'][before[-1]]),
                end_window_s=retract, actual_push_axis=push.tolist(),
                max_signed_yield_m=float(signed.max()), net_signed_yield_m=float(signed[-1]),
                max_tangent_m=float(tangent.max()), fully_in_window_contact_runs=len(in_window),
                median_force_predicate_gap_s=float(np.median(gaps)),
                p90_force_predicate_gap_s=float(np.quantile(gaps, .9)),
                fraction_gaps_le_1ms=float(np.mean(gaps <= .001+1e-10)),
                schema2_certified=False,
                caveat='Macro across intermittent contact; no no-push counterfactual; not acceptance')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root, output = args.run.resolve(), args.output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Output must be outside the immutable run')
    if output.exists():
        raise FileExistsError(output)
    categories = ('passive_corner', 'active_short', 'active_long')
    methods = ('vmc', 'admittance', 'impedance')
    cases = {category+'/'+method: analyze_case(root/'pilot'/category/method)
             for category in categories for method in methods}
    source_names = (
        'tools/teacher_bank_rollout_20260930.py',
        'tools/teacher_bank_exposure_20260930.py',
        'tools/teacher_bank_classical_20260930.py',
        'scripts/validate_office_apparatus_v5_20260917.py',
        'scripts/physics_substep_metrics_20260923.py',
        'scripts/office_task_v4_20260917.py')
    result = dict(schema=1, scope='v8 train fixture 0 only; development dt=1e-4; no generalization claim',
                  run=str(root), server_run='arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/'+root.name,
                  server_verification='Recorded archive receipt; no fresh network verification in this analysis',
                  script_sha256=sha(Path(__file__)),
                  metadata_sha256={name: sha(root/name) for name in ('plan.json', 'fixtures.json')},
                  frozen_source_sha256={name: sha(root/'source'/name) for name in source_names},
                  cases=cases)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(output), sha256=sha(output), cases=len(cases))))


if __name__ == '__main__':
    main()
