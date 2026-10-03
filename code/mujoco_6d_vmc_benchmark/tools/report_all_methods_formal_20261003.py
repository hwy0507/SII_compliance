"""Report newly executed all-method formal anchor, keeping every failure."""
import argparse
import json
from pathlib import Path
from optimize_tool_contact_20261002 import sha, write, now
from build_unified_compliance_matrix_20261003 import METHODS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=root/'report';out.mkdir(exist_ok=False)
    lock=json.loads((root/'VALIDATION_LOCK.json').read_text())
    protocol=json.loads((root/'PROTOCOL.json').read_text())
    assert json.loads((root/'COMMON_COHORT.json').read_text())['passed']
    candidates={c['name']:c for c in lock['candidates']};rows=[]
    for phase in sorted(root.glob('queue_[0-3]')):
        state=json.loads((phase/'execution.json').read_text());assert state['status']=='complete'
        analysis=root/(phase.name+'_analysis')
        assert json.loads((analysis/'execution.json').read_text())['status']=='complete'
        independent=json.loads((analysis/'INDEPENDENT_AUDIT.json').read_text())
        assert not independent['pending']
        for physical in independent['rows']:
            run=Path(physical['run']);name=run.name;c=candidates[name]
            s=json.loads((run/'rollout.json').read_text());ex=json.loads((run/'execution.json').read_text())
            metrics=json.loads((analysis/(name+'.metrics.json')).read_text())
            dev=Path(next(e['development_run'] for e in lock['development_evidence'] if e['name']==name))
            old=json.loads((dev/'execution.json').read_text())
            assert ex['config']==old['config']==c.get('config',{})
            assert ex['checkpoint_sha256']==old['checkpoint_sha256']==c.get('checkpoint_sha256')
            if c.get('rl_case'):
                for key in ('case','bridge_sha256','policy_source_sha256'):
                    assert ex['runtime_provenance'][key]==old['runtime_provenance'][key]
                old_policy=json.loads((dev/'rollout.json').read_text())['baseline_policy']
                assert s['baseline_policy']['normalization_hash']==old_policy['normalization_hash']
                assert s['baseline_policy']['normalizers_unchanged'] and s['baseline_policy']['training'] is False
            elif c.get('controller'):
                for key in ('parameter_prior','parameter_source_sha256','controller'):
                    assert ex['runtime_provenance'][key]==old['runtime_provenance'][key]
            elif c.get('checkpoint'):
                assert s['arguments']['teacher']=='none' and s['arguments']['esn_mode']=='control'
            assert sha(run/'rollout.npz')==physical['trace_sha256']==metrics['trace_sha256']
            assert physical['frozen_source_hashes_verified'] and physical['actuator_amplitude_and_command_slew_valid']
            xyz=physical['object_final_position'];failures=[]
            if not physical['task_success']:
                if xyz[2]<0: failures.append('物块掉落至地面')
                elif physical['stage']=='carry': failures.append('停在搬运阶段')
                elif physical['stage']=='approach': failures.append('停在接近阶段')
                if physical['placement_error_xy_m']>=.025: failures.append('放置XY超25mm')
                if abs(xyz[2]-.545)>=.015: failures.append('放置高度超15mm')
                if not failures: failures.append('未满足真实释放/稳定支撑保持')
            if physical['penetration_mm']>.2:failures.append('外部穿透超0.2mm')
            if physical['edge_penetration_mm']>.2:failures.append('桌角穿透超0.2mm')
            if physical['abort_reason']:failures.append(physical['abort_reason'])
            rows.append(dict(name=name,tier='all_models_formal_anchor',condition='anchor',run=str(run),
                **{k:physical[k] for k in ('task_success','strict_success','full_horizon','stage','abort_reason',
                    'rmse_mm','peak_torque_nm','peak_speed_mps','penetration_mm','edge_penetration_mm',
                    'trace_sha256','model_sha256')},duration_s=metrics['duration_s'],
                final_xy_mm=physical['placement_error_xy_m']*1000,object_final_position=xyz,
                placement_hold_s=s['placement_hold_s'],failure_reasons=failures,
                contact=metrics['contact'],recovery=metrics['recovery'],
                **{k:metrics[k] for k in ('position_error_integral_m_s','time_above_25mm_s','absolute_joint_mechanical_work_j')},
                torque_total_variation_nm=sum(metrics['torque_total_variation_nm_by_joint']),
                execution_sha256=sha(run/'execution.json'),metrics_sha256=sha(analysis/(name+'.metrics.json')),
                independent_audit_sha256=sha(analysis/'INDEPENDENT_AUDIT.json'),frozen_model_configuration_verified=True))
    assert len(rows)==26 and {r['name'] for r in rows}==set(candidates)
    index={r['name']:r for r in rows};rows=[index[n] for n,_ in METHODS]
    result=dict(created_utc=now(),source_sha256=sha(Path(__file__)),protocol_sha256=sha(root/'PROTOCOL.json'),
                validation_lock_sha256=sha(root/'VALIDATION_LOCK.json'),rows=rows,
                task_successes=sum(r['task_success'] for r in rows),strict_successes=sum(r['strict_success'] for r in rows),
                note='Single known anchor, not a success-rate estimate. Includes every frozen model regardless of development qualification.')
    write(out/'results.json',result)
    # Seven historical formal runs are a reproducibility diagnostic, not extra trials.
    frozen=Path(protocol['frozen_root']);previous={}
    for phase in sorted(frozen.glob('formal_[1-4]')):
        for r in json.loads((phase/'execution.json').read_text())['rows']:previous[r['name']]=r['audit']
    repeat=[]
    for name,old in previous.items():
        current=index[name]
        repeat.append(dict(name=name,task_same=current['task_success']==old['task_success'],
            strict_same=current['strict_success']==old['strict_success'],
            differences={k:current[k]-old[k] for k in ('rmse_mm','peak_torque_nm','peak_speed_mps','penetration_mm')},
            previous_trace_sha256=old['trace_sha256'],new_trace_sha256=current['trace_sha256']))
    write(out/'REPEAT_CHECK.json',dict(rows=repeat,note='Known repeated anchor; do not count as independent conditions.'))
    def fmt(v,d=2):return 'NA' if v is None else f'{v:.{d}f}'
    def force(r,e,k='contact_p95_force_n',d=1):
        return fmt(r['contact'][e][k],d) if r['contact'][e]['exposure'] else '未接触'
    lines=['# 全26方法在同一正式步长最终测试场景的实际重跑', '',
        '本表每行是一条新运行，非旧表推测。相同v6锚点/初态/seed/规划/执行器限制/门槛，dt=5e-5、55秒；'
        '球2秒、人手4–11秒、杆13–22.5秒、同一桌角及目标。所有权重冻结、无重训、无开发资格筛选。', '',
        '任务成功和严格成功分列“是/否”，避免0/0歧义。严格成功要求任务成功及原穿透门槛；'
        '接触力为对应事件窗口接触子步P95，未接触不是零力。每模型仅一回合，不能估计泛化成功率。', '',
        '| 方法 | 任务成功 | 严格成功 | RMSE mm | 峰矩 Nm | 峰速 m/s | 人手P95 N | 杆P95 N | 桌角P95 N | 末态/失败征象 |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|---|']
    for name,label in METHODS:
        r=index[name]
        cells=[label,'是' if r['task_success'] else '否','是' if r['strict_success'] else '否',
               fmt(r['rmse_mm']),fmt(r['peak_torque_nm']),fmt(r['peak_speed_mps'],3),
               force(r,'human'),force(r,'rod'),force(r,'unknown_edge'),'; '.join(r['failure_reasons']) or '真实稳定放置通过']
        lines.append('| '+' | '.join(cells)+' |')
    lines+=['', '## 接触累计负担与恢复覆盖', '',
        '以下包含失败回合。积分为接触力模之和的时间积分，不是净动量。恢复未观察到时标注删失，'
        '不是零秒或无穷大；不能按未接触或更早失败来判定柔顺性最佳。', '',
        '| 方法 | 球峰力 N | 人手积分 N·s | 杆积分 N·s | 桌角积分 N·s | 人手恢复 | 杆恢复 |',
        '|---|---:|---:|---:|---:|---|---|']
    for name,label in METHODS:
        r=index[name];cells=[label,force(r,'ball','peak_force_n')]+[force(r,e,'impulse_ns') for e in ('human','rod','unknown_edge')]
        for e in ('human','rod'):
            v=r['recovery'][e];t=v['settled_rejoin_time_s']
            cells.append('未接触' if not v['exposed'] else (fmt(t)+' s' if t is not None else '未观察到（删失）'))
        lines.append('| '+' | '.join(cells)+' |')
    lines+=['', '## 证据与边界', '',
        '- 共享归档：`arm1@192.168.31.70:'+str(root)+'`；每条原始轨迹、源/配置/模型hash、命令、checkpoint与失败均保留。',
        '- `COMMON_COHORT.json`核验所有模型同世界、初始观测、运行库与公共配置；各queue分析核验物理子步、动作过滤及执行器约束。',
        '- `results.json`保留逐回合接触/恢复/失败来源，`REPEAT_CHECK.json`核对7个已有正式结果的重复一致性。',
        '- `CONTACT_WINDOWS.json`提供全任务/窗口外接触覆盖补充；`placement_audits/`独立重建25Hz原放置门槛。',
        '- 既有RL是冻结迁移评估，历史训练曝光与office teacher蒸馏不同。此轮未替RL重新训练，不把失败推广为RL算法不适用。',
        '- 球瞬态峰力对刚性接触求解/步长敏感，不作为真实人体安全结论。原门槛不因结果变动。', '']
    (out/'MATRIX.md').write_text('\n'.join(lines))
    print(json.dumps(dict(models=26,task=result['task_successes'],strict=result['strict_successes'])))


if __name__=='__main__':main()
