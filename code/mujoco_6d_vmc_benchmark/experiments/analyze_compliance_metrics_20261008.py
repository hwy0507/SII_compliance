import csv,json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002')
REPO=Path('/home/arm1/SII_compliance_baseline')
IDS=['zero','esn_original_v2','esn_reference_context','esn_dagger_drift','fixed_admittance','parameter_admittance','fixed_vmc','parameter_vmc']
TARGET=np.array([.69,-.31])
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for ident in IDS:
    summary=read(ROOT/ident/'rollout.json')
    with np.load(ROOT/ident/'rollout.npz') as z:
        t=z['time']; obj=z['object_position']; err=z['task_position_error_m']
    with np.load(ROOT/ident/'rollout_apparatus_trace.npz') as a:
        hand=a['hand']; rod_force=a['rod_force']
    pre=(t>=12)&(t<13); rodwin=(t>=13)&(t<=22.5); post=(t>22.5)&(t<=35)
    event=summary['stats']['events'].get('rod',{})
    contact=bool(event)
    if contact:
        active=rod_force>.05
        hand_xy=hand[active,:2] if active.any() else np.zeros((0,2))
        hand_disp=float(np.linalg.norm(hand_xy[-1]-hand_xy[0])) if len(hand_xy)>1 else 0.
        hand_path=float(np.linalg.norm(np.diff(hand_xy,axis=0),axis=1).sum()) if len(hand_xy)>1 else 0.
        impulse=float(event['impulse_ns'])
        progress=float((np.linalg.norm(obj[np.flatnonzero(pre)[-1],:2]-TARGET)-np.linalg.norm(obj[np.flatnonzero(rodwin)[-1],:2]-TARGET))*1000)
    else:
        hand_disp=hand_path=impulse=progress=0.
    rows.append(dict(id=ident,task_success=summary['task_success'],strict_success=summary['strict_success'],
        final_stage=summary['final_task_stage'],final_xy_mm=summary['placement_error_xy_m']*1000,
        rod_contact=contact,rod_duration_s=float(event.get('duration_s',0)),rod_peak_N=float(event.get('peak_n',0)),
        rod_impulse_Ns=impulse,hand_yield_net_mm=hand_disp*1000,hand_yield_path_mm=hand_path*1000,
        rod_progress_mm=progress,progress_per_impulse_mm_per_Ns=progress/impulse if impulse>0 else None,
        pre_rod_object_distance_mm=float(np.linalg.norm(obj[np.flatnonzero(pre)[-1],:2]-TARGET)*1000),
        rod_end_object_distance_mm=float(np.linalg.norm(obj[np.flatnonzero(rodwin)[-1],:2]-TARGET)*1000),
        post_rod_error_rms_mm=float(np.sqrt(np.mean(err[post]**2))*1000),source_rollout_sha256=sha(ROOT/ident/'rollout.npz')))
by={r['id']:r for r in rows}; esn=by['esn_original_v2']; zero=by['zero']
claim=dict(rod_impulse_reduction_percent=(1-esn['rod_impulse_Ns']/zero['rod_impulse_Ns'])*100,
 progress_gain_percent=(esn['rod_progress_mm']/zero['rod_progress_mm']-1)*100,
 progress_per_impulse_gain_percent=(esn['progress_per_impulse_mm_per_Ns']/zero['progress_per_impulse_mm_per_Ns']-1)*100,
 rank_by_progress_per_impulse=[r['id'] for r in sorted([r for r in rows if r['rod_contact']],key=lambda r:r['progress_per_impulse_mm_per_Ns'],reverse=True)],
 rank_by_low_impulse=[r['id'] for r in sorted([r for r in rows if r['rod_contact']],key=lambda r:r['rod_impulse_Ns'])])
out=ROOT/'compliance_metrics_exploratory'; out.mkdir(exist_ok=True)
definitions={'primary_candidate':'rod_progress_mm / rod_impulse_Ns, only when measured rod-hand contact exists',
 'rod_progress_mm':'decrease in object XY distance to fixed target from 12-13s pre-window to final sample in 13-22.5s rod window',
 'rod_impulse_Ns':'native event integral of resultant rod-hand force',
 'hand_yield_net_mm':'net hand XY displacement over apparatus samples with rod force >0.05N',
 'post_rod_error_rms_mm':'RMS task position error in fixed 22.5-35s window'}
limitations=['Exploratory after v6 scene/checkpoint freezing; not a preregistered selection criterion.',
 'Controllers without measured rod contact cannot be ranked as rod-compliance winners; absent contact is a separate coverage failure.',
 'All v6 disturbed runs fail task/strict; low impulse or low RMSE does not establish recovery.',
 'Methods start the rod window at different object states; progress-per-impulse is descriptive, not a paired causal effect.',
 'Fixed admittance has lower rod impulse than base ESN, so ESN is not best on every compliance axis.',
 'A formal claim needs a new contact-only protocol with forced common contact, moving reference, repeated seeds and task/recovery gates.']
(out/'METRICS.json').write_text(json.dumps(dict(status='exploratory_not_preregistered',definitions=definitions,rows=rows,claim=claim,limitations=limitations),indent=2,ensure_ascii=False))
with (out/'METRICS.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
order=IDS
fig,ax=plt.subplots(1,3,figsize=(14,7),layout='constrained')
for a,key,title in zip(ax,['rod_impulse_Ns','rod_progress_mm','progress_per_impulse_mm_per_Ns'],['Rod-hand contact impulse (N s)','Object progress during rod window (mm)','Progress per contact impulse (mm/(N s))']):
    vals=[by[i][key] or 0 for i in order]
    colors=['#2469a6' if i.startswith('esn') else '#c77b2b' if i.startswith(('parameter','fixed')) else '#777' for i in order]
    a.barh(range(len(order)),vals,color=colors); a.set_title(title); a.grid(axis='x',alpha=.2); a.set_axisbelow(True)
    for j,v in enumerate(vals): a.text(v,j,f' {v:.3f}',va='center',fontsize=8)
ax[0].set_yticks(range(len(order)),order); ax[0].invert_yaxis()
fig.suptitle('Exploratory contact-conditioned compliance metrics | office-validation-v6\nNo metric was used to select checkpoints or alter the scene')
for ext in ['png','pdf']: fig.savefig(out/f'compliance_metrics.{ext}',dpi=160)
fig.savefig(out/'preview.jpg',dpi=100); plt.close(fig)
report=f"""# 接触条件下的柔顺指标探索（office-validation-v6）

这份分析是在场景、checkpoint、方法名单均冻结后进行的探索性复算。它没有参与权重选择或场景修改，因此不能事后充当预注册结果。

## 当前能支持的有限结论

在确实发生棍—手受力接触的方法中，基础 VMC 蒸馏 ESN 的棍推接触冲量为 **{esn['rod_impulse_Ns']:.3f} N·s**，Zero 为 **{zero['rod_impulse_Ns']:.3f} N·s**，降低 **{claim['rod_impulse_reduction_percent']:.1f}%**。棍推窗口内物块向目标推进 **{esn['rod_progress_mm']:.3f} mm**，Zero 推进 **{zero['rod_progress_mm']:.3f} mm**；单位接触冲量推进分别为 **{esn['progress_per_impulse_mm_per_Ns']:.3f}** 和 **{zero['progress_per_impulse_mm_per_Ns']:.3f} mm/(N·s)**，ESN 相对 Zero 提高 **{claim['progress_per_impulse_gain_percent']:.1f}%**。

这说明基础 ESN 相比 Zero 具备“较少棍推冲量传递，同时在接触窗口取得更多物块推进”的线索。它比全程 RMSE 更贴近柔顺控制的目标。

但它还不能证明 ESN 是所有方法中最好的：固定导纳的棍推冲量是 **{by['fixed_admittance']['rod_impulse_Ns']:.3f} N·s**，低于 ESN；DAgger ESN 的物块推进更大但冲量和峰值力更高；固定/在线阻抗没有实际棍接触，不能与已接触方法直接做棍推柔顺排名。所有受扰动方法 task/strict 都失败。

## 建议采用的正式判据

1. **任务/安全门槛优先。** task=true、strict=true、全时域完成且最大穿透不超限；未通过的方法不能靠低 RMSE 或低冲量翻盘。
2. **接触覆盖单列。** 球、人手、棍、未知边都必须达到预设受力阈值；未发生棍接触的方法标为 coverage failure。
3. **接触传递指标。** 在相同棍推输入、相同初始物块状态、确实发生棍接触的回合，记录棍—手冲量、峰值接触力和接触持续时间。
4. **有效恢复指标。** 记录棍推窗口内物块目标距离减少量、棍推后恢复时间、最终放置成功率。建议主指标用“任务推进 / 接触冲量”，但只能在任务安全通过后作为次级指标。
5. **动作代价。** 报告峰值真实力矩、力矩平方积分和手部速度峰值，防止用超大动作换取位移。
6. **统计验证。** 在未用于训练/选权重的多个场景和多个扰动种子上预注册；用 paired bootstrap 或置信区间报告 ESN 相对每个 baseline 的差异。单一固定场景的结果只能称为趋势。

## 最小可执行验证协议

新建一个不含未知凸边的 contact-only 场景，保留球、人手或棍的受力接触，但让名义参考持续向前运动，不能因策略停滞而改变参考。棍推输入固定，确保每种方法都在相同时间窗发生至少一次棍—手接触；不满足接触覆盖的方法判失败。预先锁定三项主指标：

- task/recovery success（首要）；
- 棍—手冲量传递 / 物块目标距离减少量；
- 棍推后恢复时间与残余位置误差。

辅以峰值真实力矩、峰值手速、外穿透。这样才可以支持“ESN 在相同接触负载和任务进度下更顺从、更有效”的结论。

## 当前三指标的正确定位

RMSE、峰值力矩、峰值速度仍应保留，但它们是运动与执行代价指标。它们不能单独证明柔顺性：Zero 可以因为停滞而有小 RMSE，阻抗方法可以因为没有碰到棍而有低冲量。柔顺性需要接触实际发生、任务推进和安全恢复同时成立。

服务器产物：{out}/METRICS.csv、METRICS.json、compliance_metrics.png/pdf。原始 v6 轨迹仍在各方法目录，旧失败回合没有删除。
"""
(out/'REPORT.md').write_text(report)
(REPO/'code/mujoco_6d_vmc_benchmark/docs/COMPLIANCE_METRICS_EXPLORATORY_20261008.md').write_text(report)
