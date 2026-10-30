from pathlib import Path
import ast,datetime,hashlib,json,socket,subprocess,tarfile,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY82_PREFIX83_PREPARATION_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG;RUN=B/'runs/parameter_partial75_recovery_cycle82_20261029_v1';DEC=B/'runtime/recovery83_completion_preparation_20261030_v1';PREFIX=B/'runs/parameter_recovery82_first5000_20261030_v1';CHANGES=B/'runs/recovery81_old_terminal_changes_20261030_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
assert read(D/'OBSERVATION_FINISHED.json')['passed']
assert read(PREFIX/'REVIEW.json')['passed'] and read(PREFIX/'SAVED_REVIEW.json')['passed'] and read(PREFIX/'PLOT_INSPECTION.json')['actual_image_viewed']
assert read(CHANGES/'REVIEW.json')['passed']
for n in ['DRIVER_SOURCE_REVIEW.json','CONTRACT_REVIEW.json','FINAL_SOURCE_REVIEW.json','HEALTH_DEPENDENCY_IMPORT_REVIEW.json']:assert read(D/n)['passed']
assert live(read(D/'LAUNCH.json')) and not (D/'FAILURE.json').exists()
assert not (DEC/'DECISION83.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle83_20261029_v1/LAUNCH.json').exists()
progress={}
for j in read(RUN/'LAUNCH.json')['jobs']:
 assert live(j);p=RUN/j['controller']/'train';assert not (p/'FAILURE.json').exists();progress[j['controller']]=read(p/'PROGRESS.json')
previous=read(B/'runtime/recovery81_full_review_20261030_v1/SAVE_SNAPSHOT.json')['time'];g=Path('/tmp/sii_gpu_util_guard_20261030_v7');samples=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];samples=[v for v in samples if v['time']>previous];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in samples));guard=dict(samples=len(samples),minimum=[min(v['gpus'][i]['utilization'] for v in samples) for i in range(4)],below50=[sum(v['gpus'][i]['utilization']<50 for v in samples) for i in range(4)],last=[v['utilization'] for v in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False)
snap=dict(time=time.time(),host=socket.gethostname(),cycle82=progress,guard=guard,goal='active',direct34=False,actual83_training=False,actual83_restore_complete=(D/'FINISHED.json').exists());put(D/'SAVE_SNAPSHOT.json',snap)
folders=[D,DEC,B/'runtime/recovery83_followups_20261030_v1',PREFIX,CHANGES,B/'runs/parameter_partial75_recovery_cycle83_review_20261029_v1',B/'runs/parameter_recovery83_loss_20261029_v1'];files=set()
for folder in folders:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.json','.jsonl','.py','.diff','.txt','.log','.png','.npz'} and p.stat().st_size<10_000_000:files.add(p)
for n in ['LAUNCH.json','MONITOR_LAUNCH.json','startup/REVIEW.json']:files.add(RUN/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,active_logs_are_snapshots=True,prior_package='RL_RECOVERY81_COMPLETE82_FROZEN_LOSS_20261030',large_assets='Original shared SSD paths; not full HDD/arm1 backup'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_hashes_and_ast_verified=True,host=snap['host'],main_inspected='784af219157ccbc5bc965e8bce41eeb0186e5152',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',large_assets='Shared SSD; not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps={m:p['steps'] for m,p in progress.items()};changes=read(CHANGES/'REVIEW.json');obs=read(D/'OBSERVATION_FINISHED.json');prior_refs=read(DEC/'LAUNCH_SOURCE_REVIEW.json')['prior82_evidence_count']
doc=f'''# 第82轮固定前缀、旧终端变化分解与第83轮恢复准备

{datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat()}。Goal active。原82三路继续，steps `{steps}`。83仅恢复等待器PID `{read(D/'LAUNCH.json')['pid']}`已部署，实际恢复完成 `{snap['actual83_restore_complete']}`；没有DECISION83、CONTINUATION_REASON或83训练，没有Direct34。

主机 `{snap['host']}`，解释器 `{B}/env/bin/python`，checkpoint/replay/raw及既有冻结诊断268MB索引仍在共享SSD `{B}`。开工/发布前fetch/read main784af219、baselinef6e8f8c；其他主机非RL工作保持独立。不是HDD/arm1完整备份。

## 固定最早5000记录

事后登记的描述性前缀，保存原optimizer日志最早5000完整行；三路原字节一致、连续step、所有数值有限、独立标量算术及实际六图核验。不是挑选平稳区间，也不等于完整周期健康验证。

|方法|critic首1000→末1000均值|最大|actor首→末1000|
|---|---|---:|---|
|阻抗|2.520469→2.425130|20.336224|23.204442→23.171939|
|导纳|1.673723→1.574762|19.328390|−8.593291→−8.661899|
|VMC|0.789073→1.066072|14.582568|−12.504310→−12.502212|

I/A重复有限尖峰、actor略降；V早期尖峰及末段簇、actor近似平坦。既有冻结诊断已显示采样可产生有限尖峰，不能增设“每个有限尖峰都是异常”的门槛；前缀不证明收敛，原82全loss/health/reward/标签/终端及82–84窗口继续。

## 完整81旧记录误差变化的事后分解

使用已经审过的完整80/81 CPU Q、reward和mask，对两路所有2394旧terminal逐行用标量重算，保留新旧两个replay分母，汇总与原跟踪收据一致。登记明确发生在top5初看之后，没有新forward、optimizer、replay写入或物理轨迹。

VMC1539条SSE增加、855条减少；正变化合计4586.019531、负变化−4114.635227、净增471.384304，top5占正变化48.8196%。最大增幅是原78成功short0200，index3230938、SSE0.979073→1523.175248；原78成功short0100为8.540407→302.126984；原78失败short0600为330.591440→461.838760；原78成功long0400也变差。原80失败short0600改善不能代表全部旧样本改善。

导纳1579条增加、814条减少、1条不变；正变化2034.923754、负变化−526.699584、净增1508.224170，top5占正变化16.2748%。已映射的高增幅记录包括原72失败short0600和原80成功short0200/short0300/long0300。

身份映射限定完整49–74、76–80，每路930条；更早记录及partial75未映射，但全部2394仍纳入算术。V top5中的443508、A top5中的1509338身份未补造。不能据此断言遗忘的具体因果、历史minibatch尖峰原因或新的健康阈值。所有逐行记录、Q前后值、mask/reward及映射原件SHA在 `runs/recovery81_old_terminal_changes_20261030_v1/REVIEW.json`。

## 第83轮准备

`runtime/prepare_recovery83_20261030_v1` 的科学trainer与82逐字一致，五metadata添加可逆回原75；原partial75、23/47容量marker、4m append-only、terminal128、batch65536、UTD1、LR/reward/masks/physics/filter/gates保持。三路协议/父边界正fixture及每路19协议+8边界拒绝通过；真实未完整82拒绝，无83输出。仅恢复等待绑定原82 learner/monitor身份，须完整82审查和原learner退出后才校验full state/replay/next65536，不训练。

生成器初次宽泛轮次替换误改负例预算82500→83500，被数字AST检查抓到；显式保留82500后重建/全部复测通过，原失败脚本、初始fixture及收据保留，无科学重启。future83 startup/archive/fullreview源码、两个health依赖实际导入及完整loss历史49–74/76–82路径核验通过，75仍拒绝。

`runtime/recovery83_completion_preparation_20261030_v1` 绑定完整82全审/四实际图/准确恢复、原76–78及完整原79–81结果/图、原82–84精确PLAN `{sha(B/'runs/parameter_recovery82_84_reward_stability_20261030_v1/PLAN.json')}`。继承DECISION82的{prior_refs}证据重核，launcher parent82/driver82引用验证；缺完整82、缺DECISION83、缺LAUNCH83三项实际拒绝。辅助build首次hash函数没有把str转换为Path，修正及失败源保留；没有改科学文件或运行。

83 labels及两终端followup helper仅准备，预期完整82锚点2454→完整83终端2484；缺实际83 LAUNCH在产生输出前拒绝。未部署83锚点/后续，无自动83或84。

## 连续运行与保存

{obs['samples']}样本/{obs['elapsed']:.3f}s，原82训练/后续、82–84窗口、83仅恢复等待及GPU共15身份持续核验，保存观察逐行回读相同；观察器自然结束，原训练继续。

GPU本轮{guard['samples']}样本最低{guard['minimum']}%、低于50次数{guard['below50']}，最后{guard['last']}%。含合成保载，不是科学吞吐；完成科研后仍保持，原v6低谷/v7预热0保留，guard不是重启自启服务。

SSD证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，全部成员字节/hash/源码AST核验；嵌套ignored runs须force-add并核index/commit blobs。254字节HDD LATEST原位更新，实际发布看本目录PUBLICATION.json。

下次检查原82及所有等待器PID/start/终态和guard年龄；完成82完整审计后基于实际结果决定83。原79–81 I reward描述性5%通过但loss健康未证，A/V失败；原74–76不完整、原76–78各结论及79阻抗安全失败保持。Direct33数值接受、冻结30 Task/Strict0/0和旧28最终内存不变证明缺失保持，不启动34；指定ESN仍缺，最终公平冻结比较待完成。Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(doc)
entry=f'''## 2026-10-30 — 原82前5000与旧终端变化已审；83仅恢复及派发准备

- [交接](docs/{TAG}.md)。82最早5000原字节/独立算术/实际图通过；critic首→末I2.520469→2.425130、A1.673723→1.574762、V0.789073→1.066072，有限尖峰保留、非收敛。旧2394完整标量分解V1539增/855减、A1579增/814减/1不变，部分原成功条件误差变大，非因果结论。
- 83科学trainer与82逐字相同、每路19协议+8边界拒绝及未完整82拒绝通过；仅恢复等待{read(D/'LAUNCH.json')['pid']}部署、准确恢复={snap['actual83_restore_complete']}。完整83审查/决策/helper准备，继承{prior_refs}证据及精确82–84PLAN；生成数字负例/Path错误修正保留，无83训练/Direct34，Goal active。
- 原82steps{steps}；16样本/{obs['elapsed']:.3f}s共15身份保持。GPU{guard['samples']}样本min{guard['minimum']}%、低于50{guard['below50']}，科研完成仍合成保载。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}已核，非HDD/arm1全备份；main784af219/baselinef6e8f8c已fetch/read，发布见SSD收据，无子agent。

'''
for n in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/n;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';s=p.read_text();first,rest=s.split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('](docs/','](')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');assert p.stat().st_size==254;v=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert len(v)<=254
with p.open('r+b') as f:f.write(v+b' '*(254-len(v)));f.flush()
assert p.stat().st_size==254 and p.read_bytes().startswith(v)
print(json.dumps(receipt))
