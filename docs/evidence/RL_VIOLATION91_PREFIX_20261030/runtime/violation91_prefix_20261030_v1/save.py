from pathlib import Path
import json,time,hashlib,tarfile,ast,socket,os
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle91_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1'
TAG='RL_VIOLATION91_PREFIX_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
obs=read(D/'OBSERVATION_REVIEW.json');loss=read(D/'prefix5000/REVIEW.json');assert obs['passed'] and loss['passed'] and read(D/'prefix5000/PLOT_INSPECTION.json')['actual_image_viewed']
for j in obs['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
for m in loss['methods']:
 assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
 with (T/m/'train/optimizer.jsonl').open('rb') as f:assert b''.join(next(f) for _ in range(5000))==(D/'prefix5000'/(m+'_optimizer_first5000.jsonl')).read_bytes()
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists()
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists()
rows=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(D/'PLAN.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
gpu=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],includes_synthetic_guard=True)
progress={m:read(T/m/'train/PROGRESS.json') for m in loss['methods']};frozen={m:read(F/m/'PROGRESS.json') for m in loss['methods']}
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),progress91=progress,frozen90=frozen,gpu=gpu,identities=obs['identities'],goal='active'))
E.mkdir();A.mkdir();files=[p for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts];files += [B/'runtime/violation91_review_20261030_v1/CONSUMER_PARENT_BOUNDARY_REVIEW.json',T/'startup/REVIEW.json',B/'repository/RL_VIOLATION91_ONLINE_20261030/PUBLICATION.json']
for m in progress:files += [T/m/'train/PROGRESS.json',F/m/'PROGRESS.json']
manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<10_000_000;q=E/p.relative_to(B);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(p.relative_to(B)),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Fixed first5000 of91, saved arithmetic and actual plot, live original104 identities; no new training dispatch or complete-cycle claims'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for m in tar.getmembers():assert tar.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,backup_scope='Shared SSD; HDD254-byte pointer only, not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
lines=[]
for m,x in loss['methods'].items():
 q=x['stats']['agent_train/q_loss'];actor=x['stats']['agent_train/actor_loss'];lines.append(f"| {m} | {q['first1000']:.9f} | {q['last1000']:.9f} | {q['maximum']:.9f} | {actor['first1000']:.9f} → {actor['last1000']:.9f} |")
text=f'''# 第91轮固定前5000更新审查；原训练及冻结90继续

2026-10-30 UTC，Goal active。前序[91实际启动](RL_VIOLATION91_ONLINE_20261030.md)。本轮只读取原作业的已保存记录，0新物理步/0新optimizer update/无新阶段派发。原91及完整review/health/loss归档消费者、原冻结90评测/collector/postprocessor、GPU守护继续。未收敛，无自动92/Direct34。

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，分析源码 `{D}`，解释器 `{B}/env/bin/python`。按sii-research-sync实际query/fetch/read main `e0842d5fe91c0370061de3408bb003a9b32d758b` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；第一次查询TLS失败，重试成功，无相关科学协议变化。无子agent。

在读取91 loss数值前固定每方法最初5000个更新，沿用90同一窗口和算术；三路按准确完整90的实际steps绑定，分别从3729701、3732501、3733501开始。I90安全中止后的实际40752步保持，未假定其完整41250。原optimizer前缀逐字复制且读取后再次核验；全部step连续/update_index0、指标有限且q非负、NPZ逐值相同、math.fsum独立保存均值核验。已实际查看六栏图并记录hash。

| 方法 | critic首1000均值 | critic末1000均值 | critic最大值 | actor首末1000均值 |
|---|---:|---:|---:|---:|
{chr(10).join(lines)}

I反复出现约13的尖峰且最大25.05，actor均值继续上移；A critic末段略升，actor近-8.22；V孤立21.45尖峰及4000更新附近波动保留，actor近-11.544。全部有限仅排除本窗口NaN/Inf，不证明loss健康。当前只有部分周期，没有完整91 reward，不能据此前缀宣布reward平稳或整轮收敛。前序90完整loss独立存于REVIEW中的complete90_last1000；同52修订不等于已完成90—92统计窗口。维持原有限91预算和算法，等完整结果再判断后续，不依据早期波动擅改目标/阈值。

原进程实际连续观察{obs['elapsed_s']:.3f}秒、{obs['samples']}样本、{len(obs['identities'])}身份均保持，三路steps增长。保存时steps `{ {m:x['steps'] for m,x in progress.items()} }`，冻结90完成 `{ {m:x['completed_conditions'] for m,x in frozen.items()} }`/各30。最终完整91/health/loss、冻结90全90 raw/88→90配对/最终全state不变仍待。原物理/MJB/Task/Strict/filter/执行器/dt5e−5、actor49/canonical48、critic52/历史/Adam/RNG、回放4m/terminal128/batch65536/UTD1/原LR及失败记录不变。

保留完整90 I long0000全局穿透安全中止、外部bit0未覆盖该失败，固定旧终端A/V退化及旧失败窗口；partial75、74—76不可判、79安全中止、半std拒绝和全部软件失败不删除。Direct原数值验收与冻结33全30 Task/Strict0/0、原28最终内存证明缺失保持；指定ESN仍缺，不替用其他模型。

GPU守护原97370及97399–97402继续，科研结束仍保载；本轮{gpu['samples']}采样，最低{gpu['minimum']}%、低于50次数{gpu['below50']}、末值{gpu['last']}%。含合成负载，非科研吞吐或每瞬时保证，非重启自启服务。

证据包 `{archive}`，{receipt['members']}成员，{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`；逐tar成员/源码AST通过。Git index/commit逐字核验及正常push/实际远端确认写包外PUBLICATION。大checkpoint/raw仍共享SSD，HDD仅254字节指针，不是HDD/arm1全备份。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 原91固定前5000审查；I/V尖峰保留

- [交接](docs/{TAG}.md)。准确完整90边界、固定5000原字节/保存算术/六栏实际图通过。critic首末I1.764565→1.638681、A1.145342→1.161649、V.764069→.798559；I/V最大25.0458/21.4508，I actor继续上移。仅早期有限值，非loss健康或reward收敛；无新训练派发/自动92/Direct34。
- 原91/冻结90/消费者继续，{obs['elapsed_s']:.3f}s/{len(obs['identities'])}身份保持；steps{ {m:x['steps'] for m,x in progress.items()} }，冻结完成{ {m:x['completed_conditions'] for m,x in frozen.items()} }。完整91及冻结90全90/raw/paired仍待，所有旧失败保持。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍守护；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验、HDD仅254字节指针，非全备份。maine0842d5f/baselinef6e8f8c实际query/fetch/read（首次TLS失败重试成功），正常发布见收据；Goal active，无子agent。

'''
for name in ('UPDATE_LOG.md','HANDOFF.md'):
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:x['steps'] for m,x in progress.items()},frozen={m:x['completed_conditions'] for m,x in frozen.items()})))
