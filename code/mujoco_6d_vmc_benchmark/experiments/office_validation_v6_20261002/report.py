"""Native metric and protocol audit for the registered v6 validation."""
import csv,hashlib,html,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002')
REPO=Path('/home/arm1/SII_compliance_baseline')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    protocol=read(ROOT/'PROTOCOL.json')
    model=sha(ROOT/'construction/rollout.mjb')
    rows=[];series={};audits=[];common=None
    ids=[c['id'] for c in protocol['cases']]+['clear_zero']
    for ident in ids:
        p=ROOT/ident
        s=read(p/'rollout.json');exe=read(p/'EXECUTION.json')
        assert exe['status']=='complete'
        full=s['full_task_horizon_completed']
        assert full or s['abort_reason'], 'Unexplained truncated trajectory'
        assert exe['protocol_sha256']==sha(ROOT/'PROTOCOL.json')
        actual_model=sha(p/'rollout.mjb');expected=sha(ROOT/('construction_clear' if ident=='clear_zero' else 'construction')/'rollout.mjb')
        assert s['model_sha256']==actual_model==expected
        args={k:v for k,v in s['arguments'].items() if k!='output'}
        if ident!='clear_zero':
            if common is None:common=args
            assert args==common
        metric=p/'rollout_metrics/substep_metrics.npz'
        with np.load(metric) as z:
            t=z['time'];dt=z['dt'].astype(float);e=z['error'].astype(float);torque=z['qfrc_actuator'].astype(float);twist=z['twist'].astype(float);stage=z['stage']
        assert len(dt)==s['metrics']['samples'] and np.allclose(dt,1e-4,rtol=0,atol=1e-12)
        assert (len(dt)==550000) if full else (len(dt)<550000)
        assert all(np.isfinite(x).all() for x in [e,torque,twist])
        metrics=dict(position_rmse_3d_m=float(np.sqrt(np.sum(e*e*dt[:,None])/dt.sum())),generalized_actuator_torque_peak_nm=float(abs(torque).max()),linear_speed_peak_mps=float(np.linalg.norm(twist[:,:3],axis=1).max()))
        errors={k:abs(v-s['metrics'][k]) for k,v in metrics.items()}
        assert errors['position_rmse_3d_m']<1e-5 and errors['generalized_actuator_torque_peak_nm']<1e-5 and errors['linear_speed_peak_mps']<1e-7
        events=s['stats']['events'];edge=s['stats']['unexpected_edge']
        row=dict(id=ident,full_horizon=full,abort_reason=s['abort_reason'],rmse_mm=metrics['position_rmse_3d_m']*1000,peak_torque_nm=metrics['generalized_actuator_torque_peak_nm'],peak_speed_mps=metrics['linear_speed_peak_mps'],task=s['task_success'],strict=s['strict_success'],stage=s['final_task_stage'],penetration_mm=s['stats']['max_external_penetration_m']*1000,edge_penetration_mm=edge['max_penetration_m']*1000,placement_error_xy_mm=s['placement_error_xy_m']*1000,max_lift_mm=s['max_lift_m']*1000,duration_s=float(dt.sum()),ball_contact_s=events.get('ball',{}).get('duration_s',0),person_contact_s=events.get('person_hand',{}).get('duration_s',0),rod_contact_s=events.get('rod',{}).get('duration_s',0),edge_contact_s=edge['duration_s'],physical_valid=s['physical_valid'])
        rows.append(row)
        with np.load(p/'baseline_policy.npz') as z:
            assert z['observation'].shape==(s['baseline_policy']['steps'],48) and z['action'].shape==(s['baseline_policy']['steps'],7)
            assert s['baseline_policy']['steps']*400==len(dt)
            if ident in ['zero','clear_zero']:assert np.all(z['action']==0)
        bins=np.floor((t-1e-9)/.04).astype(int);start=np.r_[0,np.flatnonzero(np.diff(bins))+1];end=np.r_[start[1:]-1,len(t)-1]
        series[ident]=dict(time=t[end],error=np.maximum.reduceat(np.linalg.norm(e,axis=1)*1000,start),speed=np.maximum.reduceat(np.linalg.norm(twist[:,:3],axis=1),start),torque=np.maximum.reduceat(abs(torque).max(axis=1),start))
        audits.append(dict(id=ident,substeps=len(dt),metrics_sha256=sha(metric),model_sha256=actual_model,execution_sha256=sha(p/'EXECUTION.json'),metric_errors=errors,policy=s['baseline_policy'],events=events,edge=edge))
    out=ROOT/'report';out.mkdir(exist_ok=True)
    dump(out/'SUMMARY.json',dict(protocol_sha256=sha(ROOT/'PROTOCOL.json'),model_sha256=model,rows=rows))
    dump(out/'AUDIT.json',dict(status='passed',total_episodes=len(rows),total_full_episodes=sum(r['full_horizon'] for r in rows),total_substeps=sum(r['substeps'] for r in audits),rows=audits))
    with (out/'METRICS.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lookup={r['id']:r for r in rows}
    order=['esn_original_v2','esn_reference_context','esn_dagger_drift','parameter_admittance','parameter_impedance','parameter_vmc','direct_metric_74001','direct_metric_74002','direct_office_task_74001','direct_office_task_74002','fixed_admittance','fixed_impedance','fixed_vmc','zero']
    fig,axs=plt.subplots(1,3,figsize=(14,8),sharey=True,layout='constrained')
    for ax,key,title in zip(axs,['rmse_mm','peak_torque_nm','peak_speed_mps'],['Position RMSE (mm)','Peak actual torque (Nm)','Peak hand speed (m/s)']):
        values=[lookup[i][key] if lookup[i]['full_horizon'] else 0 for i in order]
        colors=['#326ca8' if i.startswith('esn') else '#c87a2e' if i.startswith(('direct','parameter')) else '#777777' for i in order]
        ax.barh(range(len(order)),values,color=colors,height=.65)
        for n,v in enumerate(values):ax.text(v,n,f' {v:.3f}' if lookup[order[n]]['full_horizon'] else ' ABORT 16.36s (excluded)',va='center',fontsize=8)
        ax.set_title(title);ax.set_xlim(0,max(values)*1.25);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    axs[0].set_yticks(range(len(order)),order,fontsize=9);axs[0].invert_yaxis()
    fig.suptitle('New v6 validation | frozen checkpoints | 55 s | dt=0.0001 s\nTask/strict and actual contact coverage are reported separately',fontsize=12)
    for ext in ['png','pdf']:fig.savefig(out/('comparison.'+ext),dpi=150)
    fig.savefig(out/'preview.jpg',dpi=100);plt.close(fig)
    fig,axs=plt.subplots(3,1,figsize=(11,9),sharex=True,layout='constrained')
    for ident in ['zero','esn_original_v2','parameter_impedance','direct_metric_74001']:
        for ax,key in zip(axs,['error','torque','speed']):ax.plot(series[ident]['time'],series[ident][key],label=ident,lw=.9)
    for ax,label in zip(axs,['Position error (mm)','Peak torque (Nm)','Hand speed (m/s)']):
        ax.set_ylabel(label);ax.grid(alpha=.2);ax.axvline(2,ls=':',color='red');ax.axvspan(4,11,alpha=.08,color='orange');ax.axvspan(13,22.5,alpha=.08,color='green')
    axs[0].legend(fontsize=8);axs[-1].set_xlabel('Physical time (s)');fig.suptitle('40 ms bin maxima retain short physical peaks')
    fig.savefig(out/'time_traces.png',dpi=150);plt.close(fig)
    old=read(Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/esn_rl_comparison_20261002/COMPARISON.json'))['rows']
    mapping={'esn_original_v2':'esn_first_three/esn_original_v2','esn_reference_context':'esn_context_pair/esn_reference_context','esn_dagger_drift':'esn_dagger_pair/esn_dagger_drift'}
    old={r['id']:r for r in old};changes=[]
    for r in rows:
        if r['id']=='clear_zero':continue
        if not r['full_horizon']:
            changes.append(dict(id=r['id'],excluded='Truncated at safety abort; not duration matched'));continue
        previous=old[mapping.get(r['id'],r['id'])]
        changes.append(dict(id=r['id'],relative_change_percent={k:100*(r[k]/previous[k]-1) for k in ['rmse_mm','peak_torque_nm','peak_speed_mps']}))
    dump(out/'OLD_NEW_DESCRIPTIVE.json',changes)
    lines=['| Method | RMSE mm | Peak torque Nm | Peak speed m/s | task / strict | Penetration mm | Final stage | Duration s |','|---|---:|---:|---:|---|---:|---|---:|']
    for ident in order+['clear_zero']:
        r=lookup[ident];lines.append(f"| {ident} | {r['rmse_mm']:.3f} | {r['peak_torque_nm']:.3f} | {r['peak_speed_mps']:.6f} | {r['task']} / {r['strict']} | {r['penetration_mm']:.6f} | {r['stage']} | {r['duration_s']:.2f} |")
    contacts=['| Method | Ball s | Human s | Rod s | Unknown edge s |','|---|---:|---:|---:|---:|']
    for r in rows:contacts.append(f"| {r['id']} | {r['ball_contact_s']:.4f} | {r['person_contact_s']:.4f} | {r['rod_contact_s']:.4f} | {r['edge_contact_s']:.4f} |")
    report="""# 新独立验证场景 office-validation-v6（2026-10-02）

用户授权重新设置验证场景。预登记PROTOCOL.json后冻结场景、权重和评估名单，无再训练、无按结果调场景。
保留抓取/搬运/放置、球撞、人手推、棍推及先验地图遗漏凸边的结构；名义规划/WBC、canonical48输入、动作接口和任务/0.2mm穿透门槛保留。

## 主要发现

- 关闭主动扰动并移除未知凸边的名义参照task/strict均成功，最终XY误差6.821mm；14个有扰动方法全部失败。
- 基础蒸馏ESN29.492/42.808/.3543；context36.686/38.734/.3599；后期DAgger50.286/37.712/.3539。原VMC蒸馏版在三种ESN中RMSE最低，峰矩较高。
- RL调导纳27.772/38.826/.3945、调阻抗26.260/36.311/.3881、调VMC36.996/37.721/.3658。ESN对参数RL没有全面优势。
- 固定/在线阻抗未实际接触棍；两个metric直接RL也未接触棍。DAgger未接触未知凸边，不能将其结果解释为处理该凸边的能力。
- 基础ESN、Zero及导纳/VMC类都有球、人手、棍与凸边的实际受力接触，仍未恢复放置。完整视频保留停滞尾段。
- 三个跑满回合的直接RL RMSE为188.992、768.911、258.250mm；第四个16.36s安全终止，不能按其较短轨迹RMSE排名。

## 新设置

- 球：1kg、半径60mm、位置[.540,-.430,.610]m、2s发射、速度1.45m/s；旧位置x=.535、速度1.7。
- 人手：4–11s，旧3–10s；驱动/行程保留。
- 棍：中心[.770,-.120,.635]m，13–14.5s推进、14.5–20.5s保持、20.5–22.5s撤回，14N驱动；旧高度.640m、12s启动、10s保持。
- 未知凸边：中心[.625,-.250,.540]m、全尺寸20×90×40mm；旧中心[.610,-.250,.555]m、20×90×70mm。两者底部均z=.520m。
- 共同任务目标[.690,-.310,.545]m，55s，seed2026091751，开发dt1e-4，公共策略25Hz。
- 新模型在Spark编译一次后归档，14方法使用完全相同MJB；质量/惯量、摩擦/接触材料、关节阻尼与执行器限制核验不变。
- clear_zero是额外可行性参照：球发射/人手及棍主动扰动关闭、未知凸边移至地下；它不属于14方法同场景排名。

## 结果（含保留的安全终止失败）

带16.36秒时长的行只描述失败前轨迹，其余行均55秒。

"""+'\n'.join(lines)+"""

## 实际受力接触覆盖

未发生接触不能算抗该干扰成功。edge统计包含机器人或所搬物块的受力接触。
"""+'\n'.join(contacts)+f"""

## 验证及解释边界

15条预登记评估已结束，其中14条跑满55秒、1条16.36秒安全终止，共7,863,600子步独立复算三指标。模型hash/公共参数/48维观测及7维公共动作形状核对通过。
office_task第二seed在16.36秒触发global_penetration_exceeded_2mm，记录最大外穿透7.077491mm。原始失败保留；其表中指标仅描述终止前轨迹，图和旧新百分比排除该短回合，不与55秒结果直接排名。
ESN动作/储备池精确重放通过；RL推理归一化冻结由桥验证。无重新训练或修改checkpoint。
低RMSE/低峰速可能来自任务停滞，需同时看task/strict/最终阶段与实际接触。峰矩是真实qfrc_actuator，峰速为手部线速度范数。
新场景是一个预登记的变化条件，不是多场景统计泛化；ESN/RL历史训练数据和预算仍不同。
旧新结果的变化仅作描述，不将不同难度当同场景算法提升。开发dt1e-4不能当正式dt5e-5。
本轮2条80ms构建探针不纳入结果表；构建和失败日志均保留。所有完整比较回合在同一Spark/Python3.12/MuJoCo3.11.0运行。
clear_zero也保留原柱子/桌面及静止人体/棍布局；仍记录到与静止人手的3.3ms偶发受力接触，因此不是全世界零接触回合。其成功只说明本轮名义无额外干扰条件可行，不证明障碍下任务可达。

服务器根：arm1@192.168.31.70:{ROOT}
模型SHA256：{model}
原始轨迹/指标/执行信息按方法目录保存；report含CSV、JSON、物理复算审计、旧新描述性差异、三指标图和时间轨迹。
代码：code/mujoco_6d_vmc_benchmark/experiments/office_validation_v6_20261002；实际运行使用服务器source冻结副本。
"""
    (out/'REPORT.md').write_text(report)
    (REPO/'code/mujoco_6d_vmc_benchmark/docs/OFFICE_VALIDATION_V6_RESULTS_20261002.md').write_text(report)
    cards=''
    for ident in ['zero','esn_original_v2','parameter_impedance','direct_metric_74001']:
        if (ROOT/ident/'media/manifest.json').exists():
            cards+=f'<h2>{ident}</h2><video controls preload="metadata" src="../{ident}/media/replay_threeview.mp4"></video>'
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Office v6 validation</title><style>body{font:16px/1.6 system-ui;margin:24px;max-width:1500px}img,video{width:100%}pre{white-space:pre-wrap}</style><h1>新独立验证场景 v6</h1><p>冻结策略；14条55秒完整回合、1条16.36秒安全终止；开发步长0.1ms。参见task/strict及实际接触。</p><img src="comparison.png"><p><a href="METRICS.csv">CSV</a> · <a href="comparison.pdf">PDF</a> · <a href="AUDIT.json">物理复算</a></p>'+cards+'<pre>'+html.escape(report)+'</pre>')
    web=Path('/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/office_validation_v6_20261002')
    if not web.exists():web.symlink_to(ROOT,target_is_directory=True)
    else:assert web.resolve()==ROOT
    print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
