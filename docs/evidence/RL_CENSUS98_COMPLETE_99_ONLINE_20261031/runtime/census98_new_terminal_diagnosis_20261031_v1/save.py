from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census98_new_terminal_diagnosis_20261031_v1';N=B/'runtime/census99_preparation_20261031_v1';R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle98_20261031_v1';TAG='RL_CENSUS98_TERMINAL_PREPARATION_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
for p in [O/'PREFLIGHT_REVIEW.json',O/'REPORT_CONTRACT_REVIEW.json',D/'ONLINE_OBSERVATION_REVIEW.json',D/'DIRECT33_SCOPE_RECHECK.json',N/'STATIC_SOURCE_REVIEW.json']:assert rd(p)['passed']
plan=rd(O/'WAIT_PLAN.json')
for n,h in plan['source_hashes'].items():assert sha(D/n)==h
for p,h in plan['fixed_inputs'].items():assert sha(p)==h
for n,h in plan['runtime_hashes'].items():assert sha(Path(plan['restore_runtime'])/n)==h
ob=rd(D/'ONLINE_OBSERVATION_REVIEW.json')
for j in ob['identities']:live(j)
assert not list(D.glob('*FAILURE*')) and not list(O.glob('*FAILURE*')) and not list(RUN.rglob('*FAILURE*'))
assert not (B/'runs/parameter_census_cycle99_20261031_v1').exists() and not (N/'SCIENTIFIC_DECISION.json').exists()
assert not (O/'REFERENCE_PLAN.json').exists() and not (O/'reference98').exists() and not (O/'DIAGNOSIS.json').exists()
progress={m:rd(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']};assert all(x['steps']>=ob['last_steps'][m] for m,x in progress.items())
g=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(g['root']);assert not (G/'STOP').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],formal98_running=True,complete98=False,new_terminal_inference_started=False,automatic99=False,goal='active'))
files=set()
for folder in [D,N]:files.update(p for p in folder.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.diff','.txt'})
files.update(O.glob('*.json'))
prior=B/'runs/census97_new_terminal_diagnosis_20261031_v1';files.update(prior.glob('*FAILURE*.json'))
for n in ['BIND_REPAIR_REVIEW.json','BIND_REPAIR_PLAN.json']:files.add(prior/n)
for n in ['PUBLICATION.json','RECEIPT.json','FINAL_LIVE_STATUS.json']:files.add(B/'repository/RL_CENSUS98_PREFIX_WINDOW97_20261031'/n)
files.add(B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json');files.add(B/'runs/serl_take33_frozen_combined_review_20261030_v3/REVIEW.json');files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Read-only actual98 completion/new-terminal consumer registered, original97 report schema accepted/27 corruptions rejected and missing98 rejected. Planned8803 reference/90new diagnostics not run. Static99 driver/trainer-label candidate only. Existing102 identities verified10min; original science/failures/gates/ESN requirements retained.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence; existing254-byte HDD pointer only, not full HDD/arm1 backup; live98 checkpoints/raw remain SSD');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
growth={m:ob['last_steps'][m]-ob['first_steps'][m] for m in progress};steps={m:x['steps'] for m,x in progress.items()}
body=f'''# 第98轮新终端诊断已登记，原训练继续 — 2026-10-31

Goal active，完整98、原97–99稳定性与最终公平比较未完成。原三训练、90sampler、archive、固定8713终端与全90比较等待器保持，新增一个只读完整98新终端诊断等待器。没有重启训练或99派发。

主机 `{socket.gethostname()}`；共享SSD `{B}`，Python `{B}/env/bin/python`；正式目录 `{RUN}`，本轮只读源 `{D}`，输出 `{O}`。当前LAUNCH及startticks记录原身份，恢复先核最新98进度与checkpoint，勿回退完整97。

新诊断等待原完整98核心审查、固定8713旧终端比较、全90比较及完整terminal population全部完成，然后绑定实际checkpoint/日志，构建8803终端参考（I2935/A2934/V2934）并检查所有90新增终端。原块边界、全5critic和原mask保持，旧8713预测须逐值复现既有消费者；完整learner/Adam/replay/RNG与checkpoint保持不变。随后逐条绑定transition/episode/rollout、重算masked与全5未mask SSE，保留short0600时序、所有新失败与原loss最大点。没有采样索引，不作尖峰因果归因。

**目前只有准备/预检/等待，不存在完整98参考、预测或诊断结论。** 原三消费者PID身份实查，实际缺完整98被拒；完整97全部8713参考保存算术精确复算，无神经推理/物理/优化器更新。等待及分析沿原archive4h截止，不延长或另开训练。

上一轮97原binder误读逐方法不存在的passed字段，本轮在登记前引入fixed_report_contract：要求总报告passed、逐方法文件与总报告methods完全相同、checkpoint/value hash一致，以及完整state不变和保存算术标记。使用实际完整97三方法报告（确实没有passed字段）正例通过，27个内存损坏样例拒绝；实际binder已静态核对调用同一函数。原97失败及修复收据完整保留，不覆盖旧源码或结果。

`{N}` 仅静态99候选：driver改为将来完整98父/有限99身份，18依赖与正式98逐字节相同，真实98 trainer的候选转换仅预算异常轮次文字98→99。600万容量与原第三阶段继承不变，未创建99科学决定/登记/run目录，未恢复任何99状态。后续必须等完整98科学审查，再登记有限99并进行实际完整状态/原生重复更新/CPU/启动门禁；静态检查不等于获准科学推进或实际恢复通过。

重新读取原始关机交接并保留全部最终要求：改善后reward稳定、原loss健康、完整冻结评测、最终完整集合统一SPT Tref、峰矩/接触舒适/机器安全与失败分母、用户指定ESN公平比较。指定ESN仍未获得，原交接已记录问过，未重复追问或用远端其他ESN替代。Direct33原数值验收决定保持launch34=false；实际已保存冻结33总报告30行重新计数，Task/Strict0/0、完整55s30、机器违规0，仅回读汇总，非重做物理审计。原28最终内存证明缺口/恢复2已证保持。

原102身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，三路steps增长 `{growth}`；保存总steps `{steps}`。新诊断尚未推理，完整98结果、三消费者输出及实际图仍待。下一步继续检查原98进度，等实际完成后按原loss/全90/新旧终端证据作有限99决定。

独立GPU guard持续运行，科研全部结束仍不停止。保存窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，min `{gpu['minimum']}`%、低于50 `{gpu['below50']}`，末值 `{gpu['last']}`%；含保活负载，不等于科学吞吐或每瞬时保证。

本轮实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`。证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员大小/hash/AST核验。Git与远端核验见 `{A}/PUBLICATION.json`。大checkpoint/replay/raw仍共享SSD；HDD配额满，仅既有254字节LATEST指针原地更新回读，非HDD/arm1完整备份。
'''
(R/'docs'/(TAG+'.md')).write_text(body)
entry=f'''## 2026-10-31 — 完整98新终端诊断等待已登记，原102进程继续

- [交接](docs/{TAG}.md)。新增只读消费者等待原98核心/固定8713终端/全90与population审查后构建8803参考与全90新终端诊断；原块边界/五critic/mask/全state不变要求保持。完整97保存算术与缺完整98拒绝通过，尚无98推理/结论。
- 上轮binder字段错误已于登记前按总报告passed、逐方法精确相等、state/算术/value hash修正；实际三97报告正例及27损坏报告拒绝通过，原97失败/修复保留。无新训练派发。
- 有限99仅静态候选，18依赖原样、实际98trainer仅预算错误文字变化；未科学登记/恢复/启动，仍须全98审查与真实门禁。重读原最终SPT/指定ESN要求，Direct33决定与冻结30行Task/Strict0/0、原历史缺口保持，Goal active。
- 原102身份连续{ob['elapsed_s']:.3f}s，steps增长{growth}；三正式/archive/三个消费者继续。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅指针。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
paths=[str((E/x['relative']).relative_to(R)) for x in manifest]+[str((E/'MANIFEST.json').relative_to(R)),f'docs/{TAG}.md',f'docs/{TAG}_SAVE.json','AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md'];put(A/'TASK_PATHS.json',dict(paths=paths));print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps)))
