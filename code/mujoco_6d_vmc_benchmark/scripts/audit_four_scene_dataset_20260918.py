"""Independent export checks and an honest source-domain dataset report."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import numpy as np

SCENES=('ball','push','corner','table_corner')
NAMES=dict(ball='球撞',push='持续棍推',corner='抓取前桌角',table_corner='持物厚桌角放置')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,required=True);a=parser.parse_args();root=a.folder
    manifest=json.loads((root/'manifest.json').read_text());summary=json.loads((root/'complete.json').read_text())
    anchors=json.loads((root/'anchors.json').read_text());failures=[];checks={};hashes={};groups={};physics={};stats={}
    for split in ('train','validation','test'):
        hashes[split]=set();groups[split]=set();physics[split]=set()
        for row in manifest[split]:
            with np.load(row['trace'],allow_pickle=False)as z:
                x=z['observation'];y=z['teacher_action'];t=z['command_time_s']
            if x.shape!=(len(y),45)or y.shape!=(len(x),7)or not np.isfinite(x).all()or not np.isfinite(y).all():failures.append('schema '+row['trace'])
            if np.any(y[:,0]<-1e-6)or np.any(y[:,0]>1+1e-6)or np.any(np.abs(y[:,1:])>1+1e-6):failures.append('action bounds '+row['trace'])
            if len(t)>1 and not np.allclose(np.diff(t),.04,atol=1e-7,rtol=0):failures.append('time alignment '+row['trace'])
            if abs(t[0])>1e-7:failures.append('initial time '+row['trace'])
            if row.get('augmentation'):
                if split!='train':failures.append('augmentation outside train')
                with np.load(row['origin'])as original:
                    if not np.array_equal(y,original['teacher_action']):failures.append('augmentation altered action')
                    if not np.array_equal(x[:,:32],original['observation'][:,:32])or not np.array_equal(x[:,42:],original['observation'][:,42:]):failures.append('unexpected augmentation channel')
            else:
                log=Path(row['result']).parent/'execution.log'
                if log.exists()and re.search(r'Nan, Inf|unstable simulation|huge value in Q',log.read_text(errors='replace'),re.I):failures.append('physics warning '+str(log))
                if not row['accepted']or not all(row['checks'].values()):failures.append('unqualified episode in manifest')
            hashes[split].add(hashlib.sha256(x.tobytes()+y.tobytes()).hexdigest())
            groups[split].add(row['parent_group']);physics[split].add(row['fixture_hash'])
        stats[split]=dict(episodes=len(manifest[split]),samples=sum(r['samples']for r in manifest[split]),physical_groups=len(groups[split]))
    for first,second in (('train','validation'),('train','test'),('validation','test')):
        if hashes[first]&hashes[second]:failures.append('duplicate episode across splits')
        if groups[first]&groups[second]:failures.append('parent fixture across splits')
        if physics[first]&physics[second]:failures.append('physical fixture across splits')
    frozen=root/'frozen_runtime/scripts';expected=json.loads((root/'source_hashes.json').read_text())
    for name,sha in expected.items():
        if hashlib.sha256((frozen/name).read_bytes()).hexdigest()!=sha:failures.append('frozen source changed: '+name)
    # Recompute the Pareto front independently for each parent fixture.
    audit=json.loads((root/'audit.json').read_text());declared=json.loads((root/'pareto_final.json').read_text())
    names=('tracking_rmse_m','peak_force_n','peak_torque_nm','completion_time_s','acceleration_p95_mps2')
    reference=set()
    for fid in {r['id']for r in audit}:
        candidates=[r for r in audit if r['id']==fid and r.get('accepted')]
        for row in candidates:
            v=np.array([row['metrics'][k]for k in names])
            dominated=False
            for other in candidates:
                w=np.array([other['metrics'][k]for k in names])
                if np.all(w<=v)and np.any(w<v):dominated=True;break
            if not dominated:reference.add((fid,row['candidate']))
    if reference!={(r['id'],r['candidate'])for r in declared}:failures.append('Pareto frontier mismatch')
    original_train=manifest['train_clean'];samples=sum(r['samples']for r in original_train)
    total=np.zeros(45)
    for row in original_train:
        with np.load(row['trace'])as z:total+=z['observation'].sum(axis=0,dtype=np.float64)
    with np.load(root/'dataset/normalization_train_only.npz')as z:
        if int(z['samples'])!=samples:failures.append('normalization sample count')
        if not np.allclose(z['mean'],total/max(samples,1),rtol=0,atol=1e-11):failures.append('normalization includes non-training data or wrong means')
    ready=bool(summary['complete']and not failures)
    result=dict(ready=ready,failures=failures,stats=stats,physics_groups_disjoint=True if not any('fixture across' in f for f in failures)else False,
                empirical_pareto_verified='Pareto frontier mismatch'not in failures,source_code_frozen=True if not any('frozen source' in f for f in failures)else False,
                student_training_started=False)
    (root/'quality_certificate.json').write_text(json.dumps(result,indent=2))
    if ready:
        files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (root/'dataset').rglob('*.npz')}
        (root/'dataset_file_hashes.json').write_text(json.dumps(files,indent=2))
        (root/'READY.json').write_text(json.dumps(dict(ready=True,manifest_sha256=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),
             quality_auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),canonical_files=len(files),student_training_started=False),indent=2))
    lines=['# 四场景 VMC Teacher 数据集', '', '**状态：'+('已完成并通过独立数据审计。'if ready else '尚未达到最终验收，不能标记为最终训练集。')+'**','',
        f"真实仿真尝试：{summary['raw_simulation_trials']}；通过回合：{summary['raw_accepted']}；去重后的真实 teacher 轨迹：{summary['unique_real_episodes']}；额外训练增强轨迹：{summary['augmented_training_episodes']}。",'',
        '| 场景 | 训练原始轨迹 | 验证轨迹 | 源域留出轨迹 | 训练/验证/留出物理组 |', '|---|---:|---:|---:|---|']
    for scene in SCENES:
        nums=[sum(r['scene']==scene for r in manifest[s])for s in ('train_clean','validation','test')]
        group=summary['physical_groups'][scene]
        lines.append(f"| {NAMES[scene]} | {nums[0]} | {nums[1]} | {nums[2]} | {group['train']}/{group['validation']}/{group['test']} |")
    lines+=['','## 数据与动作约定','',
        '观测为45维本体状态及任务命令：q7、dq7、名义twist6、位姿误差6、速度误差6、估计关节负载7、估计末端力3、命令路径方向3。没有把场景ID、参数组、仿真接触真值、物块位置或事件时钟放入观测。',
        '标签是安全滤波器之前的7维动作，不是VMC参数：减速请求1维、线速度残差3维、角速度残差3维。统一线速度单位尺度0.32m/s、角速度尺度0.6rad/s、最小WBC比例0.2；旧厚桌角原生尺度单独保存，采集时验证了正反映射。',
        '**下一步训练必须支持全部7个动作通道，不能直接沿用只预测前4维的旧MLP/ESN训练入口。**',
        '训练增强仅作用于负载/力估计通道：0.9–1.1校准增益、因果相关增益扰动、0或1帧延迟。标签不变，验证及留出集不做此增强。增强样本不计入真实采集数量。', '',
        '## 筛选与划分','',
        '先检查真实接触、任务成功、物理压入、持物/放置、速度和力矩边界；棍推还检查持物后的脱离、双指夹持与终端间隙。随后在每个物理条件内求经验Pareto非支配集，目标为跟踪RMSE、峰值接触力、峰值力矩、完成时间与速度变化平稳性。它是采样范围内的经验Pareto集，不是全局最优证明。',
        '棍推还要求接触后0.5s内出现持续切向响应，并排除目标未到达时超过0.5s的位置停滞。几何间隙采用独立Native CCD查询，避免旧版CCD距离查询的误判。',
        '力峰筛选上限按已验收场景及其接触模型分别设置：球300N、棍250N、抓取前桌角650N、厚桌角850N；同时将峰值力作为Pareto最小化目标。这些是仿真数据筛选界限，不能解释为真实FR3的接触安全认证。各场景接触模型不同，不能直接据此作跨场景控制性能排名。',
        'Pareto参数再次用于轻微扰动的真实仿真重采集。所有子条件、参数变体和传感增强都继承父物理组的split。不同参数组可以跨不同物理场景复用，参数组ID永远不是学生输入。',
        '归一化仅由未增强的训练轨迹计算。重复轨迹去重，保留原始全程仿真及失败记录；训练序列仅剪去任务完成并稳定2秒之后的冗长静止尾段。', '',
        '## 教师来源与限制','']
    for scene in SCENES:
        src=anchors[scene]
        lines.append(f"- {NAMES[scene]}：`{src['family']}`；teacher力信息来源 `{src['teacher_force']}`；特权任务监督 `{src['privileged_task_supervisor']}`；遗留任务动作调度 `{src['legacy_task_action_schedule']}`。")
    lines+=['','四类已验收场景来自不同版本的VMC实现；数据保留该差异，不能在论文中描述成一个完全同构的VMC。球和抓取前桌角的teacher使用理想外力，学生观测仍仅含本体估计；厚桌角的稳定放置监督读取仿真支持状态。部署时需要对应的可实现任务接口，不能把teacher特权信息直接交给student。',
        '这里的test仅为四个基础场景的物理条件留出集，不是正式办公室泛化测试。办公室数据没有参与本轮优化。未启动MLP或ESN训练。', '',
        '## 位置','',f'- 数据manifest：`{root}/manifest.json`',f'- 独立审计：`{root}/quality_certificate.json`',f'- 原始审计：`{root}/audit.json`',f'- 源代码快照：`{root}/frozen_runtime/scripts/`']
    if failures:lines+=['','## 未通过检查','']+['- '+f for f in failures]
    (root/'DATASET_REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
