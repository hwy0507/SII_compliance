from pathlib import Path
import json,hashlib,ast,tarfile,time,datetime,socket,math,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';O=B/'runtime/parameter74_verified_wait_0156_20261029_v1';P=B/'runtime/parameter75_loss_preparation_20261029_v1';D=B/'runtime/parameter74_completion_preparation_20261029_v1';W=B/'runs/parameter_capacity74_76_reward_stability_20261029_v1';TAG='RL_PARAMETER74_WAIT75_PREP_20261029'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
finished=read(O/'FINISHED.json');assert finished['samples']==21 and finished['all_original_identities_live']
rows=[json.loads(l) for l in (O/'SAMPLES.jsonl').read_text().splitlines()]
assert len(rows)==21
for m in ['impedance','admittance','vmc']:assert all(b['progress'][m]['steps']>a['progress'][m]['steps'] for a,b in zip(rows,rows[1:]))
for j in read(O/'REGISTRATION.json')['jobs']:
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
assert read(P/'INDEPENDENT_STATIC_REVIEW.json')['passed'] and read(D/'SOURCE_REVIEW.json')['passed']
assert read(B/'runtime/parameter71_73_condition_churn_20261029_v1/SAVED_REVIEW.json')['passed']
assert not (B/'runtime/prepare_parameter75_20261029_v1/DECISION75.json').exists() and not (B/'runs/parameter75_loss_20261028_v1').exists() and not (D/'CONTINUATION_REASON.txt').exists()
g=Path('/tmp/sii_gpu_util_guard_20261028_v5');assert not (g/'STOP').exists() and not (g/'FAILURE.json').exists()
raw=[l for l in (g/'samples.jsonl').read_bytes().splitlines(keepends=True) if l.endswith(b'\n') and rows[0]['time']<=json.loads(l)['time']<=rows[-1]['time']];(O/'GUARD_SAMPLES.jsonl').write_bytes(b''.join(raw));samples=[json.loads(l) for l in raw];assert len(samples)>50
stats=[]
for i in range(4):
 vals=[next(g['utilization'] for g in r['gpus'] if g['gpu']==i) for r in samples];stats.append(dict(gpu=i,minimum=min(vals),mean=math.fsum(vals)/len(vals),below50=sum(x<50 for x in vals)))
guard=dict(time=time.time(),samples=len(samples),start=samples[0]['time'],end=samples[-1]['time'],stats=stats,max_gap=max(b['time']-a['time'] for a,b in zip(samples,samples[1:])),synthetic_guard_included=True,instantaneous_guarantee=False,continue_after_science=True);write(O/'GUARD_REVIEW.json',guard)
utc=lambda t:datetime.datetime.fromtimestamp(t,datetime.timezone.utc).strftime('%H:%M:%S')
pointer=f'''# RL 2026-10-29 {utc(rows[-1]['time'])} UTC
ACTIVE.74 running;75 prepared only. GPU guard on.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{TAG}.md
Receipt docs/{TAG}_SAVE.json
Large data SSD. No reboot service.
'''
hdd=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');assert len(pointer.encode())<=hdd.stat().st_size
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
def copy(p,rel):
 data=p.read_bytes();d=E/rel;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(data);assert d.read_bytes()==data
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(relative=str(rel),source=str(p),bytes=len(data),sha256=sha(d)))
for folder in [O,P,D,B/'runtime/parameter71_73_condition_churn_20261029_v1']:
 for p in sorted(folder.iterdir()):
  if p.is_file() and p.suffix in ['.py','.json','.jsonl','.diff']:copy(p,folder.relative_to(B)/p.name)
for name in ['PLAN.json','LAUNCH.json']:copy(W/name,W.relative_to(B)/name)
for name in ['sii_prepare75_loss_20261029.py','sii_review75_loss_preparation_20261029.py','sii_prepare75_decision_helper_20261029.py','sii_observe74_0156_20261029.py','sii_save74_wait75_preparation_20261029.py','sii_audit71_73_condition_churn_20261029.py','sii_review71_73_condition_churn_20261029.py']:copy(Path('/tmp')/name,Path('helpers')/name)
old=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1'
for name in ['PLAN.json','REVIEW.json','SAVED_ARITHMETIC_REVIEW.json','PLOT_INSPECTION.json']:copy(old/name,old.relative_to(B)/name)
write(E/'MANIFEST.json',dict(time=time.time(),files=manifest,all_bytes_and_python_ast_verified=True))
A=B/'repository'/(TAG+'_'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S'));A.mkdir();archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 for member in t.getmembers():assert t.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,members=len(manifest)+1,member_bytes_and_python_ast_verified=True,compute_host=socket.gethostname(),source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),large_artifacts='Original shared SSD; not a full HDD or arm1 backup');write(R/'docs'/(TAG+'_SAVE.json'),receipt);write(A/'RECEIPT.json',receipt)
steps='/'.join(str(finished['last_steps'][m]) for m in ['impedance','admittance','vmc']);mins='/'.join(str(s['minimum']) for s in stats);below=[s['below50'] for s in stats]
doc=f'''# 第74轮十分钟核验与75全loss准备

2026-10-29 UTC，Goal active。承接[74早期loss与75仅恢复](RL_PARAMETER74_EARLY_ANCHOR_20261029.md)。完整74尚未结束，整体收敛未证明；Direct33原训练条件数值结论与Task/Strict0/0保持，不启动34。

{utc(rows[0]['time'])}–{utc(rows[-1]['time'])} UTC，21次/600秒/30秒间隔核验，原74三learner/archive/六等待器/五guard均按PID/start ticks持续live；三路步数每次严格增加，末次I/A/V {steps}。观察器自然结束，原科学继续，无重启或结束训练。原I539354/A539357/V539358同start43374907；原全74loss541866、74–76窗口541941、标签808985、V/A终端922511/922520、75仅恢复860042保持。

75全loss四个审查源码及deploy.py位于`runtime/parameter75_loss_preparation_20261029_v1`，保持完整49–74历史并追加75，配对74→75；父/新hash、逆映射、AST及独立静态审查通过。真实缺DECISION75部署被拒绝，未创建runs/parameter75_loss_20261028_v1或新训练。正向部署必须等完整74 loss/全标签/health/终端及实际图、准确恢复和实际75启动。

入口保留原65–67、68–70及原71–73完整审查/独立算术/实际图和准确PLAN，同时绑定正在执行的原74–76 PLAN `{sha(W/'PLAN.json')}`。不提前要求未来74–76完整结果，亦不替换窗口或更改5%/近零1/seed2026102855/5000 bootstrap/anchor55。原71–73完整不稳定结论保持。

另准备了`runtime/parameter74_completion_preparation_20261029_v1/sii_decide_launch75_20261029.py`：仅静态准备，尚未执行。它映射当前74审查/75精确恢复/73→74标签/全2214终端，保留原窗口与历史bootstrap；实际全74结果未齐，CONTINUATION_REASON.txt尚未写入，DECISION75不存在，没有预先决定续训。若全审后仍需有限75，先根据实际结果写续训理由，再调用该工具；它绑定完整证据并要求原learner退出，只派发一轮，不自动76。

对原71–73全部270回合/540个Task与Strict标签另做条件切换复核，原episodes hash/逐值和旧完整标签审查切换集合一致；独立NumPy算术最大差2.84e−14，0新物理/更新，不新增统计门。

- I71→73整体均值−.060768，long0000恢复Task/Strict的单条件reward变化+50.892132，与short0600丢Strict的−54.025455抵消；两切换条件均值贡献−.104444，其余+.043676。首尾Strict总数17/17相同不等于相同条件成功。
- A71→73整体均值−.146820，long0200恢复的+50.374153与short0600丢Strict的−51.458785抵消；short0000在71/73均Strict true，但72为false。72→73的均值恢复+1.728715中，该条件贡献+1.747966，其余−.019250。
- V71→73整体均值−1.781454，其中short0600丢Strict贡献−1.750215，其余−.031239。72→73虽均值变化仅+.000922、无标签切换，仍不能抹去71→72退化。

这些只是完整保存回报和标签的算术分解，不证明随机性与策略漂移的因果份额，不改变原5%窗口判据。准确表见runtime/parameter71_73_condition_churn_20261029_v1/REVIEW.json及SAVED_REVIEW.json。

固定30条件×55秒/41250新增/4m append/markers23/47/terminal128/batch65536/UTD1及原LR/masks/reward/物理/gates保持。近零保护是统计解释限制，不是将reward推离零的新目标。

同期{len(samples)}个guard样本，四卡最低{mins}%，均值{[round(s['mean'],6) for s in stats]}%，低于50计数{below}，最大间隔{guard['max_gap']:.6f}秒。原v5五进程保持，STOP/FAILURE不存在；含合成负载，非纯科学吞吐或每瞬时保证。科研完成后也继续保载，非跨重启服务。

实际主机 `{socket.gethostname()}`；共享SSD `{B}`；解释器env/bin/python。开工实际fetch/read main8a41d38314671798d4ce80a91ca96114b3c8431b/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，保存源码基线{receipt['source_base_commit']}；保存前再次fetch/read maindf742e42及baseline未变，阅读非RL第四条件全审与原108到37/108进度，安全fast-forward保留双方记录，未操作其他主机科学进程。遵循sii-research-sync，保留并行非RL工作，无子agent。

共享SSD包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/Python AST已核。[收据]({TAG}_SAVE.json)。大checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份；既有HDD入口重写回读。

下一步继续原74，收齐全loss/标签/health/全2214终端审查，独立复算并实际看图，再结合原窗口判断。原74–76窗口仍需后续完整周期，不因观察时限重启科学。Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 第74轮十分钟核验与75全loss准备

- [交接](docs/{TAG}.md)：{utc(rows[0]['time'])}–{utc(rows[-1]['time'])}UTC共21次原74三learner/archive/六等待器/五guard身份live，steps严格增至{steps}，观察自然结束、科学继续，无重启。
- 75全loss四源/deploy静态就绪，完整49–74保留追加75、配对74→75；原65–67/68–70/71–73完整审查与原74–76准确PLAN保持。逆映射/AST/hash/独立静态通过，真实缺DECISION75拒绝，无75loss run/waiter或训练，不要求未来窗口结果。
- 原71–73全270回合/540标签及独立算术复核通过：I/A首尾均值接近包含成功/失败条件抵消，A short0000中途失Strict后恢复；V保留short0600失Strict退化。仅保存结果算术分解，非因果或新阈值。
- 有限75决定工具仅静态准备，绑定全74/75恢复/完整标签/全2214终端与原窗口；未写续训理由、未执行工具，无DECISION75，不自动76。原74及74–76等待保持，阈值不变。
- {len(samples)}guard样本min{mins}%、低于50{below}，含合成负载，科研完成仍保载。SSD包{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份；开工main8a41d383/baselinef6e8f8c实际fetch/read，无子agent，Goal active、Direct34false。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[74十分钟核验与75准备](docs/{TAG}.md)。原74/74–76继续，无75训练；GPU科研完成后仍保载，Goal active。**\n\n'+p.read_text())
hdd.write_text(pointer);assert hdd.read_text()==pointer;print(json.dumps(receipt,indent=2))
