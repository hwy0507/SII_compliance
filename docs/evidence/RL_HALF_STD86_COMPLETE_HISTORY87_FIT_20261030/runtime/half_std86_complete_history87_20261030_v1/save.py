from pathlib import Path
import json,time,hashlib,ast,tarfile,socket,subprocess,os
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';P=B/'runs/parameter86_half_std_paired_20261030_v3';H=B/'runs/recovery87_history_extension_20261030_v1';F=B/'runs/recovery87_terminal_history_paired_fit_20261030_v1';OLD=B/'runtime/half_std86_completion_entropy_preparation_20261030_v1'
TAG='RL_HALF_STD86_COMPLETE_HISTORY87_FIT_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
for folder in [P,H,F]:assert read(folder/'FINISHED.json')['passed'] and not (folder/'FAILURE.json').exists()
assert read(OLD/'WAIT_FINISHED.json')['passed'] and read(P/'PLOT_INSPECTION.json')['actual_images_viewed'] and read(F/'PLOT_INSPECTION.json')['actual_image_viewed']
for j in read(P/'LAUNCH.json')['jobs']:
 d=P/j['group'];assert read(d/'FINISHED.json')['full_learner_state_unchanged'] and read(d/'FINISHED.json')['full_replay_state_unchanged']
 q=Path(f'/proc/{j["pid"]}/stat')
 if q.exists():s=q.read_text().rsplit(')',1)[1].split();assert s[19]!=j['start'] or s[0]=='Z'
for j in [read(P/'REVIEW_LAUNCH.json'),read(OLD/'WAIT_IDENTITY.json')['job']]:
 q=Path(f'/proc/{j["pid"]}/stat')
 if q.exists():s=q.read_text().rsplit(')',1)[1].split();assert s[19]!=j['start'] or s[0]=='Z'
gstates={}
for j in read(B/'runtime/recovery87_full_and_seed_review_20261030_v1/SAVE_SNAPSHOT.json')['identities']:
 if j['name'].startswith('guard'):
  s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z';gstates[j['name']]=dict(pid=j['pid'],start=s[19])
samples=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()];samples=[x for x in samples if x['time']>=read(H/'PLAN.json')['time']];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples));gpu=dict(samples=len(samples),minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],scope='Since history87 extension registration',synthetic_included=True,keep_after_science=True,historical_dips_preserved=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),guard_identities=gstates,gpu=gpu,half_std16_complete=True,history87_complete=True,paired_fit_complete=True,goal='active',automatic88=False,direct34=False))
files=set()
def collect(folder):
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.txt','.diff','.png','.npz','.log'} and p.stat().st_size<10_000_000:files.add(p)
for folder in [D,P,H,F]:collect(folder)
for k in read(P/'PLAN.json')['groups']:collect(P/k)
for n in ['HALF_STD_RAW_REVIEW.json','HALF_STD_RAW_SAVED_REVIEW.json','WAIT_FINISHED.json','WAIT_OBSERVATIONS.jsonl','WAIT_IDENTITY.json','audit_half_std_raw.py','wait_and_audit.py']:files.add(OLD/n)
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_HALF_STD86_ENTROPY_STATE_READY_20261030'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,large_artifacts='Original shared SSD; no HDD/arm1 full backup'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='80de539b27bc629b1aa0a73869dd3bed55d97843',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
pair=read(P/'PAIRED_REVIEW.json');hist=read(H/'REVIEW.json');fit=read(F/'REVIEW.json');saved=read(F/'SAVED_REVIEW.json')
pt=[];ht=[];ft=[]
for k,g in pair['groups'].items():pt.append(f"|{k}|{g['baseline_task']}→{g['half_std_task']}|{g['baseline_strict']}→{g['half_std_strict']}|{g['mean_reward_delta']:.9f}|")
for m,g in hist['methods'].items():ht.append(f"- {m}: {g['prefix_rows']}+{g['added_rows']}={g['total_rows']} rows，终端{g['actual_terminal_rows']}；sidecar `{g['sidecar']['path']}`，SHA `{g['sidecar']['sha256']}`。")
for m,g in saved['methods'].items():
 s=g['stats'];ft.append(f"|{m}|{g['terminal_rows']}|{s['initial']['control']['masked_loss']:.9f}|{s['final']['control']['masked_loss']:.9f}|{s['final']['history']['masked_loss']:.9f}|{g['history_minus_control_final_loss']:.9f}|")
text=f'''# 半标准差全16已审；完整87历史接续与配对critic拟合完成

2026-10-30，Goal active。固定86半标准差试验全部16回合完成并独立审计，改善与退化并存，不推广统一降熵训练。完整87三路历史sidecar已准确接续；新增唯一匹配预算的terminal critic拟合诊断已完成。所有科学子任务正常结束，GPU守护继续保载；没有88/Direct34训练，不宣称收敛。

主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮实际ls-remote/fetch/read main `80de539b27bc629b1aa0a73869dd3bed55d97843`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，收工main新增a62ddb87bcfeb2dc42766f652e8815e5c770eba1的非RL共同观测动作/高负载诊断，实际fetch/read日志及报告后快进保留，RL runtime不改；按sii-research-sync发布，无子agent。前轮熵状态软件准备是实质进展，但不等于科学方案已选定。

## 固定86半标准差全部配对结果

`{P}`，原PLAN0d857019，四组×seed2026102633/34/35/36，全部16×55s、22000动作/1760万子步、0optimizer/replay更新、无abort。最终全learner/optimizer/RNG/replay不变、native动作重放、原物理/filter/torque审查、全raw独立复算均通过，reward重建最大误差2.1316282072803006e−14。序列化state不变但采样分布有意改变，不写成unchanged policy。

|组合|Task原→半std /4|Strict原→半std /4|平均reward差(半std−原)|
|---|---|---|---|
{chr(10).join(pt)}

I四次外穿透0.203194–0.222372mm均超过原0.2mm，seed35/36新失Strict；A short0900 seed34新在lift失败，seed35原carry失败保留；A long0200 seed35恢复；V全部4通过但连续指标仍有增减。两张实际结果图已查看并保存hash/解释收据。完整16原始数据与配对报告交叉对齐，无挑seed/改阈值/新因子搜索。结论：不支持统一降低采样方差，且该推理干预本来就不等价训练target_entropy。前轮持久化adapter保留为软件准备，未部署为训练修订。

## 准确完整87因果历史接续

`{H}`，PLAN SHA `{sha(H/'PLAN.json')}`，登记CPU53/torch1/900秒、0physics/forward/update/replay写入。实际主审{hist['elapsed_s']:.3f}秒。逐方法加载原完整85与87，全部旧replay数组前缀按shape/dtype/原字节hash精确相同；复制已审85历史sidecar，不改变原partial75/截断cohort。

新增完整86/87每方法82500、合计247500 transition逐journal核验current50、next50、混合动作、reward/done与global step，交错episode索引恰覆盖一次。preaction历史只用本动作前已完成区间的累计外穿透；next使用下一条journal，terminal仅用于最后done行的next，不把末峰值倒灌。独立保存审查重新标量读取原日志/journal及全部追加值，旧sidecar前缀逐位一致。该字段不是79中止时global穿透，不删除79原异常；也不是独立物理子步重建或部分可观测性必然成立的证明。

{chr(10).join(ht)}

全部历史总rows10,824,948。动作前已知外穿透>.2mm的行I88075/A76552/V58224，其中86/87新增3720/1279/1279。终端行I2605、A/V2604，保留所有原终端和历史中止，不强行三方法统一删成2604。

## 相同预算的终端critic拟合诊断

`{F}`，PLAN SHA `{sha(F/'PLAN.json')}`。完整半std/独立raw/实际图、准确87历史全部审完后，明确登记唯一离线配对：三种方法各原critic clone与history clone各500步，共3000 cloned Q Adam步，CPU53/GPU1/900秒，实际{fit['elapsed_s']:.3f}秒。不更新原checkpoint、actor、alpha或target network，不保存/晋升辅助权重；无新物理或88训练。

两臂都使用完整87全部终端、原动作/reward/bootstrap mask、每步相同全batch。loss为各critic mask内MSE之和；全部dones=1所以Bellman不bootstrap，terminal128在每critic分子/分母相消。优化器从同一原Adam states/hyperparameters恢复，旧参数和moment逐位保持；history只在观测索引50插入一个有界因果峰值 `p/(p+0.0002)`，首层新权重和Adam新moment为0。actor canonical48及原正式模型完全不改。

原clone与原模型初始预测逐位相同，增加零列后允许原先登记的1e−4数值容差；全部原参数/moment插入映射检查通过，原checkpoint SHA与完整父learner/RNG最终不变。没有reset优化器或按结果挑step。保存全部501个端点、all5 SSE和所有原终端预测，独立float64/math.fsum重算首末mask分母、SSE/loss、符号错误。

|方法|原终端行|初始原loss|500步原输入loss|500步历史输入loss|历史−原|
|---|---:|---:|---:|---:|---:|
{chr(10).join(ft)}

实际六栏图已查看，所有方法/critic/500步全部保留。该比较只说明本次已见终端样本上的拟合表现；不是未见测试、在线reward改善或历史信息唯一因果。checkpoint87已经训练过这些数据，没有假称held-out。不能把离线拟合曲线当正式训练loss健康或收敛。

下一步应据完整配对结果评估是否独立登记因果history critic在线修订。若推进，须统一扩展replay/current-next观测、全state/Adam迁移、actor隔离与CHEQ不确定性接口、checkpoint版本和恢复/health/frozen-eval入口，并验证真实起步；仅凭本次离线收益不能跳过这些。父训练仍完整87，不回退诊断86，不晋升离线权重，也不自动重复原配置88。

## 保存与范围

GPU从history登记起{gpu['samples']}采样，最低 `{gpu['minimum']}`%、低于50次数 `{gpu['below50']}`，末值 `{gpu['last']}`%。原v7 supervisor97370和四worker身份保持，科学完成后仍合成保载；不以占用冒充科研吞吐，历史低谷保留、不保证采样间每瞬时，非重启自启服务。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`；tar逐成员/AST核验，Git index/commit另核，成功push和后续实际远端确认后包外PUBLICATION。大型history sidecar/checkpoint/replay/raw在上述原共享SSD，非HDD/arm1全备份。HDD LATEST原位254字节更新，原521/99成员恢复包引用保留。

完整87与85—87稳定性失败及loss末段回升保持；Direct33数值阶段接受但冻结30 Task/Strict0/0，中断28最终内存证明缺失；指定ESN不可用，不替换他主机模型、不重复追问。partial75、74—76不可判和79安全中止及其他历史窗口结论均保留。Goal active，最终仍需四方法收敛、冻结评测和指定比较。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 半std全16与87历史已审；匹配critic拟合完成

- [交接](docs/{TAG}.md)。半std原16全55s/0更新/最终全state及1760万raw子步审计通过，Strict I2→0、Ashort3→2、Along3→4、V4→4；两实际图、所有失败保留，不推广统一降熵。
- 原85全部旧replay前缀精确，新增86/87共247500行因果历史/独立标量核验，完整87共10824948行。原87三方法各两臂500步终端critic离线拟合完成，旧Adam保留、新列/矩0、原模型不变；全端点独立算术/实际图通过。仅已见终端拟合，非在线reward改善，未晋升权重/启动88或Direct34，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学全结束仍保载；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验、非HDD/arm1全备份。main80de539b/baselinef6e8f8c实际fetch/read，发布见收据，无子agent。

'''
for n in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/n;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254
if len(data)<254:data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(receipt));print('GPU',gpu)
