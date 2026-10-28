from pathlib import Path
import json,hashlib,ast,tarfile,time,datetime,socket,math,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance'
O=B/'runtime/parameter72_verified_wait_2345_20261028_v1';P=B/'runtime/parameter73_loss_preparation_20261028_v1'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
finished=read(O/'FINISHED.json');assert finished['samples']==11 and finished['all_original_identities_live']
rows=[json.loads(l) for l in (O/'SAMPLES.jsonl').read_text().splitlines()]
for m in ['impedance','admittance','vmc']:assert all(b['progress'][m]['steps']>a['progress'][m]['steps'] for a,b in zip(rows,rows[1:]))
g=Path('/tmp/sii_gpu_util_guard_20261028_v5');assert not (g/'STOP').exists() and not (g/'FAILURE.json').exists()
raw=[l for l in (g/'samples.jsonl').read_bytes().splitlines(keepends=True) if l.endswith(b'\n') and rows[0]['time']<=json.loads(l)['time']<=rows[-1]['time']]
(O/'GUARD_SAMPLES.jsonl').write_bytes(b''.join(raw));samples=[json.loads(l) for l in raw];assert len(samples)>20
stats=[]
for i in range(4):
 v=[next(g['utilization'] for g in r['gpus'] if g['gpu']==i) for r in samples];stats.append(dict(gpu=i,minimum=min(v),mean=math.fsum(v)/len(v),below50=sum(x<50 for x in v)))
guard=dict(time=time.time(),samples=len(samples),start=samples[0]['time'],end=samples[-1]['time'],stats=stats,max_gap=max(b['time']-a['time'] for a,b in zip(samples,samples[1:])),synthetic_guard_included=True,instantaneous_guarantee=False,continue_after_science=True)
write(O/'GUARD_REVIEW.json',guard)
tag='RL_PARAMETER72_WAIT73_LOSS_PREP_20261028';E=R/'docs/evidence'/tag;E.mkdir(exist_ok=False);manifest=[]
def copy(p,rel):
 d=E/rel;d.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();d.write_bytes(data);assert d.read_bytes()==data
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(path=str(rel),source=str(p),bytes=len(data),sha256=sha(d)))
for folder in [O,P]:
 for p in sorted(folder.iterdir()):
  if p.is_file() and p.suffix in ['.py','.json','.jsonl','.diff']:copy(p,folder.relative_to(B)/p.name)
for name in ['sii_prepare73_loss_20261028.py','sii_observe72_2345_20261028.py','sii_save72_wait73loss_20261028.py']:copy(Path('/tmp')/name,Path('helpers')/name)
write(E/'MANIFEST.json',dict(time=time.time(),files=manifest,all_bytes_and_python_ast_verified=True))
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S');A=B/'repository'/(tag+'_'+stamp);A.mkdir();archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 members=t.getmembers()
 for m in members:assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,members=len(members),member_bytes_and_python_ast_verified=True,compute_host=socket.gethostname(),source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),large_artifacts='Original shared SSD; not a full HDD or arm1 backup')
write(R/'docs'/(tag+'_SAVE.json'),receipt);write(A/'RECEIPT.json',receipt)
utc=lambda t:datetime.datetime.fromtimestamp(t,datetime.timezone.utc).strftime('%H:%M:%S')
steps='/'.join(str(finished['last_steps'][m]) for m in ['impedance','admittance','vmc'])
mins='/'.join(str(s['minimum']) for s in stats);below=[s['below50'] for s in stats]
doc=f'''# 第72轮五分钟原进程核验与73全loss准备

2026-10-28 UTC，Goal active。承接[72早期检查与73仅恢复](RL_PARAMETER72_EARLY_ANCHOR_20261028.md)。本轮完成后续审查源码准备和原进程verified wait；当前72尚未完整，不能宣布整体收敛。Direct33原训练条件数值结论保持、TaskStrict0/0，不启动34。

{utc(rows[0]['time'])}–{utc(rows[-1]['time'])}UTC，300秒/30秒间隔、11次原72三learner/归档/六等待器/五guard均按PID/start ticks验证live，三路步数每次严格增加，末次I/A/V {steps}。原I704014/start42588230、A704016/V704019同start42588231保持，各30sampler的原训练继续。无完整72或失败，observer自然结束，不是科学结束；未重启任务。

新增runtime/parameter73_loss_preparation_20261028_v1四个审查源码及deploy.py，从原72按周期映射，保护原68–70、原71–73、[71,72,73]及完整hash；逆映射/AST/diff/输入hash通过。audit保留49–72全部历史，仅追加73；paired和独立review配对72→73，不移动历史窗口。独立静态复核确认完整历史列表、配对键、父与新source hash及准确当前PLAN。

73部署入口要求完整72 loss/标签/health/V+A终端及实际图、准确73恢复、旧65–67和68–70原审查，以及原71–73固定PLAN（SHA c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf）。它不要求尚未运行的73结果才能部署73审查，没有新科学阈值。

实际执行deploy.py在缺DECISION73.json时非零拒绝，未创建73 loss run、waiter或训练。上述成功仅代表静态准备和负例验证；正向部署仍须完整72审查及实际73启动。不要重复运行准备脚本覆盖现有目录。

原72全loss708626、原71–73 2909145、标签978935、V/A终端1062827/1062828、73仅恢复997695继续。30×55秒/41250新增/4m append/markers23/47/terminal128/batch65536/UTD1及原LR/masks/reward/物理/gate保持。完整72后仍须独立算术/全部标签/健康和终端数组/实际图审查，再决定有限73。原窗口、近零保护解释和全部历史结论不变。

同期{len(samples)}个guard样本，四卡最低{mins}%，均值{[round(s['mean'],6) for s in stats]}%，低于50计数{below}，最大间隔{guard['max_gap']:.6f}秒。原v5五进程保持，STOP/FAILURE不存在；含合成占用，非科学吞吐或每瞬时保证。按用户要求，科研完成后仍保载，非跨重启服务。

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，env/bin/python。开工实际fetch/read maina39eab7b15a082cabf00ac4d03bcfb103d321bee、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，保留并行非RL工作，遵循sii-research-sync，无子agent。

[证据manifest](evidence/{tag}/MANIFEST.json)。共享SSD包 `{archive}`，{len(members)}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/Python AST核验。[保存收据]({tag}_SAVE.json)。大checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份；HDD满只重写既有入口。
'''
(R/'docs'/(tag+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-28 — 第72轮五分钟核验与73全loss准备

- [交接](docs/{tag}.md)：{utc(rows[0]['time'])}–{utc(rows[-1]['time'])}UTC共11次原72三learner/archive/六等待器/五guard身份live，steps严格增至{steps}，无完整/失败。observer自然结束，科学继续，无重启。
- 73全loss四源/deploy静态就绪，完整49–72保留追加73/配对72→73；原65–67/68–70审查及原71–73准确PLAN/列表保持。逆映射/AST/hash/独立静态通过，真实缺DECISION73拒绝，无73loss run/waiter或训练，正向部署仍待。
- {len(samples)}guard样本min{mins}%、低于50{below}，含合成负载，科研完成也继续，非瞬时保证。SSD包{len(members)}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份；开工maina39eab7b/baselinef6e8f8c实际fetch/read，无子agent。Goal active、Direct34false。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[72五分钟核验与73全loss准备](docs/{tag}.md)。原72/71–73继续，无73训练；GPU完成后仍保载，Goal active。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
pointer=f'''# RL 2026-10-28 {utc(rows[-1]['time'])} UTC
ACTIVE. Cycle72 running. GPU guard stays on.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{tag}.md
Receipt docs/{tag}_SAVE.json
NO73 training. Guard3256866, no reboot service.
Large data SSD; not HDD/arm1 backup.
'''
assert len(pointer.encode())<=p.stat().st_size;p.write_text(pointer);assert p.read_text()==pointer
print(json.dumps(receipt,indent=2))
