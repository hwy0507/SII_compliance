"""Validate frozen contact sidecar evidence and inspect captured peak states."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import mujoco
import numpy as np


def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def peak_event(directory,summary,peak):
    event_id=peak['event_id']
    part=next(c for c in summary['event_chunks'] if c['first_event_id']<=event_id<c['first_event_id']+c['events'])
    i=event_id-part['first_event_id'];metadata=read(directory/(part['file']+'.json'))[i]
    with np.load(directory/(part['file']+'.npz'),allow_pickle=False) as z:states={k:z[k][i].copy() for k in z.files}
    if metadata['index']!=peak['sample_index']:raise ValueError('Peak event index mismatch')
    contact=min([c for c in metadata['contacts'] if (c['geom1'],c['geom2'])==(peak['geom1'],peak['geom2'])],key=lambda c:c['dist_m'])
    if -contact['dist_m']!=peak['depth_m']:raise ValueError('Peak contact depth mismatch')
    return metadata,states,contact


def query_peak(model_path,summary,states,contact):
    model=mujoco.MjModel.from_binary_path(str(model_path));rod=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'push_rod_geom')
    saved_mask=dict(contype=int(model.geom_contype[rod]),conaffinity=int(model.geom_conaffinity[rod]))
    model.geom_contype[rod]=8;model.geom_conaffinity[rod]=15
    output={}
    for name in ('pre_state','post_state'):
        data=mujoco.MjData(model);mujoco.mj_setState(model,data,states[name],summary['state_spec'])
        qpos=data.qpos.copy();time=float(data.time);mujoco.mj_kinematics(model,data);mujoco.mj_collision(model,data)
        pair={contact['geom1'],contact['geom2']}
        matching=[float(c.dist) for c in data.contact if {int(c.geom1),int(c.geom2)}==pair]
        transform_delta=max(float(np.abs(data.geom_xpos[contact[f'geom{i}']]-contact[f'geom{i}_xpos']).max()) for i in (1,2))
        rotation_delta=max(float(np.abs(data.geom_xmat[contact[f'geom{i}']]-contact[f'geom{i}_xmat']).max()) for i in (1,2))
        assert np.array_equal(data.qpos,qpos) and data.time==time
        output[name]=dict(state_time_s=time,pair_min_distance_m=min(matching) if matching else None,
            matching_contacts=len(matching),largest_geom_position_difference_from_live_m=transform_delta,
            largest_geom_rotation_element_difference_from_live=rotation_delta,
            qpos=qpos.tolist(),qvel=data.qvel.tolist(),ctrl=data.ctrl.tolist())
    return dict(engine=mujoco.__version__,architecture=platform.machine(),server_architecture='aarch64',
        original_collision_flags_only=True,simulation_steps=0,queries=output,
        original_disableflags=int(model.opt.disableflags),model_sha256=sha(model_path),
        runtime_mask_restore=dict(geom_id=rod,saved=saved_mask,restored=dict(contype=8,conaffinity=15),
            source='frozen audited_velocity_env._physics_step assigns push rod masks8/15; auxiliary rod masks set before MJB saving'),
        limitation='offline cross-architecture fixed-state query, not a dynamics replay or proof that the original contact depth was erroneous')


def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if mujoco.__version__!='3.11.0':raise ValueError('Matching MuJoCo 3.11.0 required')
    root=a.archive;complete=read(root/'COMPLETE.json');final=read(root/'FINAL_RESULT.json');protocol=read(root/'protocol.json')
    assert complete['all_arrays_exact'] and len(final['pairs'])==3
    assert sha(root/'protocol.json')==read(root/'READY.json')['protocol_sha256']
    for section,directory in (('source_sha256',root/'source_snapshot'),('audit_tools_sha256',root/'audit_tools')):
        for name,expected in protocol[section].items():
            if sha(directory/name)!=expected:raise ValueError('Frozen source hash mismatch '+name)
    reports=[]
    for pair in final['pairs']:
        method,seed=pair['pair']['method'],pair['pair']['seed'];job=root/'jobs'/f'{method}_{seed}_on';directory=job/'contact/episode_0'
        summary=read(directory/'summary.json');assert summary==pair['contact_summary']
        depths=[];stages=[];times=[]
        for part in summary['raw_chunks']:
            with np.load(directory/part['file'],allow_pickle=False) as raw:
                assert np.isfinite(raw['depth_m']).all()
                np.testing.assert_allclose(raw['time_after_s']-raw['time_before_s'],5e-5,rtol=0,atol=1e-10)
                depths.append(raw['depth_m']);stages.append(raw['stage']);times.append(raw['time_after_s'])
        depths=np.concatenate(depths);stages=np.concatenate(stages);times=np.concatenate(times)
        assert len(depths)==480000 and np.all(np.diff(times)>0)
        assert np.array_equal(depths.max(axis=0),summary['max_depth_m'])
        column=int(np.argmax(summary['max_depth_m']));peak=summary['peak_records'][column]
        metadata,states,contact=peak_event(directory,summary,peak)
        assert states['pre_state'][0]==metadata['time_before_s'] and states['post_state'][0]==metadata['time_after_s']
        assert depths[peak['sample_index'],column]==peak['depth_m']
        query=query_peak(job/'rollout/rollout.mjb',summary,states,contact)
        global_depth=depths.max(axis=1);thresholds=[]
        captured=[]
        for part in summary['event_chunks']:
            event_metadata=read(directory/(part['file']+'.json'))
            with np.load(directory/(part['file']+'.npz'),allow_pickle=False) as z:
                assert all(np.isfinite(z[k]).all() for k in z.files)
                assert len(z['pre_state'])==len(event_metadata)==part['events']
                for i,e in enumerate(event_metadata):
                    index=e['index'];captured.append(index)
                    assert z['pre_state'][i,0]==e['time_before_s'] and z['post_state'][i,0]==e['time_after_s']==times[index]
                    assert e['threshold_0p19mm']==bool(global_depth[index]>=.00019)
        assert len(captured)==len(set(captured))==summary['event_count']
        assert set(np.flatnonzero(global_depth>=.00019)).issubset(captured)
        for threshold in summary['thresholds_m']:
            mask=global_depth>=threshold;run=best=0
            for active in mask:run=(run+1) if active else 0;best=max(best,run)
            thresholds.append(dict(threshold_mm=threshold*1000,samples=int(mask.sum()),duration_ms=float(mask.sum()*.05),longest_ms=best*.05,
                first_step_end_s=float(times[np.flatnonzero(mask)[0]]) if mask.any() else None,
                last_step_end_s=float(times[np.flatnonzero(mask)[-1]]) if mask.any() else None,
                stage_counts={str(s):int(np.sum(mask&(stages==s))) for s in np.unique(stages)}))
        assert [r['samples'] for r in thresholds]==summary['global_thresholds']['steps_at_or_above'][0]
        rod=read(job/'rollout/rollout.json')['panel_audit']['contacts']['push_rod_geom']
        record=dict(method=method,seed=seed,task_success=pair['task_success'],accepted_panel_demo=pair['accepted_panel_demo'],
            obstacle=summary['obstacle_names'][column],peak=peak,peak_geom1=summary['geometry'][str(peak['geom1'])],
            peak_geom2=summary['geometry'][str(peak['geom2'])],margin_um=200-1e6*peak['depth_m'],thresholds=thresholds,
            peak_contact=contact,peak_solver_niter=metadata['solver_niter'],peak_solver_stats=metadata['solver_first_island_stats'],
            fixed_state_query=query,event_count=summary['event_count'],invariance=pair['invariance'],
            all_threshold_events_have_finite_pre_post_state=True,rod_first_contact_s=rod['first_s'],rod_contact_duration_s=rod['duration_s'],
            peak_after_first_rod_contact_ms=1000*(peak['time_after_s']-rod['first_s']),
            evidence_sha256={str(p.relative_to(root)):sha(p) for p in sorted(job.rglob('*')) if p.is_file()})
        reports.append(record)
    output=dict(protocol_sha256=sha(root/'protocol.json'),complete=complete,reports=reports,archive=str(root.resolve()),
        elapsed_s=final['elapsed_s'],scope='frozen three diagnostic pairs; no new method ranking or gate adjustment',
        reused_first_pair=protocol.get('reused_first_pair_root'),new_simulations=protocol.get('new_simulations',6),
        comparator_correction=protocol.get('comparison_correction'))
    a.output.with_suffix('.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    lines=['# 接触sidecar：三组不变性验证与峰时证据','',
        '3组ON/OFF共6条24秒完成，新增接触测量与关闭测量、原历史回合的18个rollout数组、contact_samples、physics_states、原物理子步数组逐元素完全一致；MJB、原gate和contact统计一致。每条ON有480000个完整float64接触样本。未改变原源码、模型、验收、dt或碰撞算法。','',
        '三组是为解释门附近峰值事后指定的诊断样例，不是新的泛化成绩。','',
        'r1在首对结束后因contact内明确由set序列化的列表顺序误报failed，原状态/源码/结果均保留。r2只规范化pairs、robot_geoms、robot_bodies、other_contacts四个无序键；全部数值和其他序列仍精确比较。首对按hash复用，r2只新运行余下4条；接触测量实现未改动。','',
        '| 方法/条件 | 峰对 | 峰深度 mm | 门余量 μm | 原求值输入～输出时刻 s | stage | 峰对法向力 N | ≥0.2mm累计 ms | 最长连续 ms |',
        '|---|---|---:|---:|---|---:|---:|---:|---:|']
    for r in reports:
        t=r['thresholds'][2];k=r['peak'];pair=r['peak_geom1']['name']+' × '+r['peak_geom2']['name']
        lines.append(f"| {r['method']} / {r['seed']} | {pair} | {k['depth_m']*1000:.9f} | {r['margin_um']:+.6f} | {k['time_before_s']:.8f} ～ {k['time_after_s']:.8f} | {k['stage']} | {k['normal_force_n']:.6f} | {t['duration_ms']:.4f} | {t['longest_ms']:.4f} |")
    lines+=['','三个峰均出现在首次有力杆接触后的约1.40–1.45ms，位于loaded-lift阶段3；MLP和ESN分别连续越过0.2mm达0.25ms、1.00ms。这是已采集到的碰撞起始短瞬态，不能用后面数秒的累计接触时长替代越门持续，也不能因瞬态短而豁免原门。','',
        '完整阈值邻域统计（所有非目标外部障碍按每步最大值合并，避免重复计数）：','',
        '| 方法/条件 | 深度阈值 mm | 物理步数 | 累计 ms | 最长连续 ms | 首次～最后越阈值步末 s |','|---|---:|---:|---:|---:|---|']
    for r in reports:
        for t in r['thresholds']:
            span='—' if t['first_step_end_s'] is None else f"{t['first_step_end_s']:.5f} ～ {t['last_step_end_s']:.5f}"
            lines.append(f"| {r['method']} / {r['seed']} | {t['threshold_mm']:.2f} | {t['samples']} | {t['duration_ms']:.4f} | {t['longest_ms']:.4f} | {span} |")
    lines+=['','## 状态时序与碰撞查询','',
        '原contact几何和力来自mj_step完成后保留的动力学求值；步后qpos已积分。sidecar直接复制该live contact，并保存该步mjSTATE_INTEGRATION输入/输出状态及求值时geom变换，没有重新计算或改写live state。下面仅用保存状态在同版本本机scratch中查询原碰撞算法，不积分、不切换CCD；原服务器aarch64、本机x86_64，查询差异不能直接证明原在线峰错误。恢复冻结源码在运行期设置的杆contype=8/conaffinity=15，其他模型/碰撞flag不变；原保存mask、恢复值与模型hash见JSON。','',
        '| 方法/条件 | 步前状态查询深度 mm | 步后状态查询深度 mm | 步前geom位置与原求值最大差 m | solver迭代数 |','|---|---:|---:|---:|---|']
    for r in reports:
        q=r['fixed_state_query']['queries']
        def depth(k):
            v=q[k]['pair_min_distance_m'];return '无该对contact' if v is None else f'{max(0.,-v)*1000:.9f}'
        lines.append(f"| {r['method']} / {r['seed']} | {depth('pre_state')} | {depth('post_state')} | {q['pre_state']['largest_geom_position_difference_from_live_m']:.3g} | 第一island {r['peak_solver_niter'][0]}，其余0 |")
    lines+=['','VMC/MLP步前重查与原深度之差分别约9.0e−16m、2.8e−17m；ESN差1.13e−8m（0.0113μm），远小于该例12.809μm越门量。三例步前geom位置与原求值差不超过1.12e−16m。结合逐步深度序列，说明本次峰与原碰撞几何一致，不能解释成单纯日志时间错位或25Hz显示误差。它仍是当前接触模型中的穿透，不等于已经证明真实硬件穿透或步长无关性。','',
        'solver计数/gradient等是求解诊断，不是物理穿透误差上界。短越门事件仍按原严格门失败，不能用持续时间短豁免；缺少步长收敛证据时也不能称为数值伪影。所有其他任务/接触门原样保留。','',
        '## 证据','',f'- 完整归档：`{root.resolve()}`。',
        '- 同名JSON包含事件contact frame/力、求值geom变换、峰时solver、原/历史不变性hash及ON目录全部文件SHA256。完整pre/post integration state在归档events_*.npz中。',
        '- 已逐条校验全部≥0.19mm样本都有完整有限的pre/post integration state事件，时间与全步raw精确对应，无重复事件；不是只存3个最终峰。',
        '- [归档证书](evidence/classical_20260923/contact_sidecar_20260924/ARCHIVE_VERIFICATION.json)：r1/r2完整目录分别通过服务器/本机只读checksum比对。',
        '- [预声明小协议](CONTACT_SIDECAR_PROTOCOL_20260924.md)；[此前只读穿透诊断](CONTACT_MARGIN_HISTORY_DIAGNOSIS_20260924.md)。','']
    a.output.write_text('\n'.join(lines))
    print(json.dumps([{k:r[k] for k in ('method','seed','margin_um','thresholds')} for r in reports],indent=2))


if __name__=='__main__':main()
