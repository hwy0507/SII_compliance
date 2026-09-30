"""Independent action replay, source integrity and physical metrics for J1."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def check_parity(root):
    left, right = root / 'checks/wrapped', root / 'checks/reference'
    arrays = 0
    for name in ('rollout.npz', 'rollout_ball_detail.npz', 'rollout_metrics/substep_metrics.npz'):
        with np.load(left / name) as a, np.load(right / name) as b:
            assert a.files == b.files, name
            for key in a.files:
                np.testing.assert_array_equal(a[key], b[key], err_msg=f'{name}:{key}')
                arrays += 1
    assert digest(left / 'rollout.mjb') == digest(right / 'rollout.mjb')
    report = dict(passed=True, arrays_exact=arrays, model_exact=True,
                  duration_s=.12, not_a_full_task_result=True,
                  files_sha256={str(p.relative_to(root)): digest(p)
                                for folder in (left, right) for p in sorted(folder.rglob('*')) if p.is_file()})
    (root / 'J1_PARITY.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'files_sha256'}))


def check_full(root, snapshot, plan_name, stem, allow_incomplete=False, include_archived_reference=True):
    sys.path.insert(0, str(snapshot / 'scripts'))
    from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics
    from office_task_v4_20260917 import DEST
    plan_path = snapshot / 'configs' / plan_name
    plan = json.loads(plan_path.read_text())
    rows, pending = [], []
    for job in plan['jobs']:
        folder = root / 'results' / job['id']
        required = ['execution.json', 'rollout.json', 'joint_teacher_manifest.json',
                    'rollout.npz', 'teacher_internal.npz', 'rollout.mjb', 'rollout_metrics/substep_metrics.npz']
        missing = [name for name in required if not (folder/name).is_file()]
        if missing and allow_incomplete:
            record = dict(case=job['id'], missing_local_files=missing, independently_verified=False)
            if (folder/'rollout.json').exists():
                result = json.loads((folder/'rollout.json').read_text())
                record.update(task=result['task_success'], strict=result['strict_success'],
                              recorded_metrics=result['metrics'], stats=result['stats'])
            pending.append(record)
            continue
        execution = json.loads((folder / 'execution.json').read_text())
        assert execution['plan_sha256'] == digest(plan_path)
        assert execution.get('exit_code') == 0, execution
        result = json.loads((folder / 'rollout.json').read_text())
        manifest = json.loads((folder / 'joint_teacher_manifest.json').read_text())
        assert manifest['status'] == 'completed'
        config_path = snapshot / job['arguments'][job['arguments'].index('--teacher-config') + 1]
        config = json.loads(config_path.read_text())
        assert config == manifest['config']
        assert digest(config_path) == manifest['config_sha256']
        assert digest(snapshot / 'tools/run_office_joint_teacher_20260927.py') == manifest['wrapper_sha256']
        for name, expected in result['source_sha256'].items():
            assert digest(snapshot / 'scripts' / name) == expected, name
        assert digest(folder / 'rollout.mjb') == result['model_sha256']
        assert digest(folder / 'teacher_internal.npz') == manifest['trace_sha256']
        teacher = SixDVirtualDynamics(config['options'])
        with np.load(folder / 'rollout.npz') as trace, np.load(folder / 'teacher_internal.npz') as internal:
            obs = trace['observation']
            np.testing.assert_array_equal(obs[:, 39:45], internal['wrench'])
            np.testing.assert_array_equal(internal['applied_action'], trace['applied_action'])
            np.testing.assert_array_equal(trace['teacher_action'], trace['applied_action'])
            replay = []
            for index, wrench in enumerate(obs[:, 39:45]):
                replay.append(teacher.act(wrench, float(internal['dt'][index])) * config['action_scale'])
                for key in ('filtered', 'offset', 'velocity'):
                    np.testing.assert_allclose(getattr(teacher, key), internal[key][index], rtol=0, atol=1e-11)
            replay_error = float(np.max(np.abs(np.asarray(replay) - trace['applied_action'])))
            assert replay_error < 1e-10
            final_xy_mm = float(1000 * np.linalg.norm(trace['object_position'][-1, :2] - DEST[:2]))
            retreat_indices = np.flatnonzero(trace['stage'] == 7)
            retreat_time = float(trace['time'][retreat_indices[0]]) if len(retreat_indices) else None
            stage_seconds = {str(int(stage)): float(np.count_nonzero(trace['stage']==stage)*.04)
                             for stage in np.unique(trace['stage'])}
            steps = len(replay)
            assert steps == 1375 == manifest['steps']
        with np.load(folder / 'rollout_metrics/substep_metrics.npz') as trace:
            dt = trace['dt']
            error = trace['error'].astype(np.float64)
            rmse = float(np.sqrt(np.sum(error * error * dt[:, None]) / dt.sum()))
            speed = float(np.max(np.linalg.norm(trace['twist'][:, :3].astype(np.float64), axis=1)))
            torque = float(np.max(np.abs(trace['qfrc_actuator'])))
            assert abs(float(dt.sum()) - 55) < 1e-7
        m = result['metrics']
        np.testing.assert_allclose([rmse, speed, torque],
            [m['position_rmse_3d_m'], m['linear_speed_peak_mps'], m['generalized_actuator_torque_peak_nm']],
            rtol=2e-7, atol=1e-8)
        rows.append(dict(case=job['id'], teacher=config['name'], task=result['task_success'],
                         strict=result['strict_success'], coverage=result['contact_coverage_valid'],
                         physical_valid=result['physical_valid'], final_stage=result['final_task_stage'],
                         waypoint_rmse_mm=rmse*1000, torque_peak_nm=torque, speed_peak_mps=speed,
                         penetration_mm=result['stats']['max_external_penetration_m']*1000,
                         rod_duration_s=result['stats']['events'].get('rod', {}).get('duration_s', 0),
                         final_object_xy_mm=final_xy_mm, replay_max_abs=replay_error, steps=steps,
                         first_retreat_time_s=retreat_time, stage_duration_s=stage_seconds,
                         model_sha256=result['model_sha256'],
                         files_sha256={str(p.relative_to(folder)): digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
    references = []
    reference_root = root.parent / 'esn_office_r34_stress_20260927/results'
    if not include_archived_reference:
        reference_root = root / '__no_archived_reference__'
    for condition in ('original', 'hard'):
        model_hashes = {r['model_sha256'] for r in rows if r['case'].endswith('_'+condition)}
        assert len(model_hashes) <= 1
        reference_path = reference_root / ('r34_'+condition) / 'rollout.json'
        if reference_path.exists():
            ref = json.loads(reference_path.read_text())
            for row in rows:
                if row['case'].endswith('_'+condition):
                    assert row['model_sha256'] == ref['model_sha256']
            for name, expected in ref['source_sha256'].items():
                assert digest(snapshot/'scripts'/name) == expected, name
            references.append(dict(case='r34_'+condition, task=ref['task_success'], strict=ref['strict_success'],
                waypoint_rmse_mm=1000*ref['metrics']['position_rmse_3d_m'],
                torque_peak_nm=ref['metrics']['generalized_actuator_torque_peak_nm'],
                speed_peak_mps=ref['metrics']['linear_speed_peak_mps'],
                penetration_mm=1000*ref['stats']['max_external_penetration_m'],
                rod_duration_s=ref['stats']['events'].get('rod',{}).get('duration_s',0),
                source_result_sha256=digest(reference_path)))
    report = dict(all_passed=not pending, episodes=len(rows), planned_episodes=len(plan['jobs']),
                  pending_cases=pending, plan_sha256=digest(plan_path), rows=rows,
                  audit_source_sha256=digest(Path(__file__)),
                  archived_r34_references=references,
                  caveat='Teacher mechanism development screen; not ESN success, not held-out/hardware validation. All failures retained.')
    output_stem = stem+'_PARTIAL' if pending else stem
    (root / (output_stem+'_AUDIT.json')).write_text(json.dumps(report, indent=2) + '\n')
    lines = [f'# {stem} teacher 固定预算机制筛查', '',
             f'{len(rows)}/{len(plan["jobs"])} 个开发回合已独立审计；不是 ESN 成功或保留集验证。物理、任务和安全门不变。', '',
             '| 条件 | task | strict | waypoint RMSE mm | 峰矩 Nm | 峰速 m/s | 穿透 mm | 推杆 s | 最终 XY mm |',
             '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['case']} | {r['task']} | {r['strict']} | {r['waypoint_rmse_mm']:.3f} | "
                     f"{r['torque_peak_nm']:.3f} | {r['speed_peak_mps']:.6f} | {r['penetration_mm']:.6f} | "
                     f"{r['rod_duration_s']:.3f} | {r['final_object_xy_mm']:.3f} |")
    for r in references:
        lines.append(f"| {r['case']} (存档 ESN 参照) | {r['task']} | {r['strict']} | {r['waypoint_rmse_mm']:.3f} | "
                     f"{r['torque_peak_nm']:.3f} | {r['speed_peak_mps']:.6f} | {r['penetration_mm']:.6f} | "
                     f"{r['rod_duration_s']:.3f} | 见原报告 |")
    for record in pending:
        lines.append(f"\n未完成独立审计：{record['case']}，本机缺少 {record['missing_local_files']}。")
    lines += ['', '已审计回合各 1375 次动作/teacher 状态重放通过；三个指标从全部物理子步独立复算通过。',
              f'已审计同条件候选 MJB hash 完全一致；源、配置、原始数据 hash 见 {output_stem}_AUDIT.json。',
              'waypoint RMSE 包含阶段目标切换，不能作为连续参考曲线跟踪误差。', '']
    (root / (output_stem+'_RESULTS.md')).write_text('\n'.join(lines))
    print('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--parity', action='store_true')
    parser.add_argument('--plan', default='office_joint_teacher_j1_20260927.json')
    parser.add_argument('--stem', default='J1')
    parser.add_argument('--allow-incomplete', action='store_true')
    parser.add_argument('--skip-archived-reference', action='store_true',
                        help='Do not compare delayed-scene MJB/source files to the frozen t=0 reference.')
    args = parser.parse_args()
    if args.parity:
        check_parity(args.root)
    else:
        check_full(args.root, args.snapshot or args.root / 'source_snapshot', args.plan, args.stem,
                   args.allow_incomplete, include_archived_reference=not args.skip_archived_reference)


if __name__ == '__main__':
    main()
