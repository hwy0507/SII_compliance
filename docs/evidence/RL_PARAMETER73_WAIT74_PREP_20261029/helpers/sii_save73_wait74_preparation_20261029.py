from pathlib import Path
import json,hashlib,ast,tarfile,time,datetime,socket,math,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance'
O=B/'runtime/parameter73_verified_wait_0053_20261029_v1';P=B/'runtime/parameter74_loss_preparation_20261029_v1';W=B/'runs/parameter_capacity74_76_reward_stability_20261029_v1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
finished=read(O/'FINISHED.json');assert finished['samples']==21 and finished['all_original_identities_live']
rows=[json.loads(l) for l in (O/'SAMPLES.jsonl').read_text().splitlines()]
for m in ['impedance','admittance','vmc']:assert all(b['progress'][m]['steps']>a['progress'][m]['steps'] for a,b in zip(rows,rows[1:]))
assert read(P/'INDEPENDENT_STATIC_REVIEW.json')['passed'];assert not (W/'LAUNCH.json').exists()
g=Path('/tmp/sii_gpu_util_guard_20261028_v5');assert not (g/'STOP').exists() and not (g/'FAILURE.json').exists()
raw=[l for l in (g/'samples.jsonl').read_bytes().splitlines(keepends=True) if l.endswith(b'\n') and rows[0]['time']<=json.loads(l)['time']<=rows[-1]['time']]
(O/'GUARD_SAMPLES.jsonl').write_bytes(b''.join(raw));samples=[json.loads(l) for l in raw];assert len(samples)>50
stats=[]
for i in range(4):
 v=[next(g['utilization'] for g in r['gpus'] if g['gpu']==i) for r in samples];stats.append(dict(gpu=i,minimum=min(v),mean=math.fsum(v)/len(v),below50=sum(x<50 for x in v)))
guard=dict(time=time.time(),samples=len(samples),start=samples[0]['time'],end=samples[-1]['time'],stats=stats,max_gap=max(b['time']-a['time'] for a,b in zip(samples,samples[1:])),synthetic_guard_included=True,instantaneous_guarantee=False,continue_after_science=True);write(O/'GUARD_REVIEW.json',guard)
tag='RL_PARAMETER73_WAIT74_PREP_20261029';utc=lambda t:datetime.datetime.fromtimestamp(t,datetime.timezone.utc).strftime('%H:%M:%S')
pointer=f'''# RL 2026-10-29 {utc(rows[-1]['time'])} UTC
ACTIVE. Cycle73 running; GPU guard stays on.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{tag}.md
Receipt docs/{tag}_SAVE.json
No74 training. Large data SSD. No reboot service.
'''
hdd=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');assert len(pointer.encode())<=hdd.stat().st_size
E=R/'docs/evidence'/tag;E.mkdir(exist_ok=False);manifest=[]
def copy(p,rel):
 d=E/rel;d.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();d.write_bytes(data);assert d.read_bytes()==data
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(path=str(rel),source=str(p),bytes=len(data),sha256=sha(d)))
for folder in [O,P,W]:
 for p in sorted(folder.iterdir()):
  if p.is_file() and p.suffix in ['.py','.json','.jsonl','.diff']:copy(p,folder.relative_to(B)/p.name)
for name in ['sii_prepare74_loss_20261029.py','sii_prepare74_76_window_20261029.py','sii_review74_preparation_20261029.py','sii_observe73_0053_20261029.py','sii_save73_wait74_preparation_20261029.py']:copy(Path('/tmp')/name,Path('helpers')/name)
old=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1'
for name in ['PLAN.json','LAUNCH.json']:copy(old/name,old.relative_to(B)/name)
write(E/'MANIFEST.json',dict(time=time.time(),files=manifest,all_bytes_and_python_ast_verified=True))
A=B/'repository'/(tag+'_'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S'));A.mkdir();archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 members=t.getmembers()
 for m in members:assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,members=len(members),member_bytes_and_python_ast_verified=True,compute_host=socket.gethostname(),source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),large_artifacts='Original shared SSD; not a full HDD or arm1 backup');write(R/'docs'/(tag+'_SAVE.json'),receipt);write(A/'RECEIPT.json',receipt)
steps='/'.join(str(finished['last_steps'][m]) for m in ['impedance','admittance','vmc']);mins='/'.join(str(s['minimum']) for s in stats);below=[s['below50'] for s in stats]
doc=f'''# 第73轮十分钟核验、74全loss准备与条件性74–76窗口

2026-10-29 UTC，Goal active。承接[73早期loss与74仅恢复](RL_PARAMETER73_EARLY_ANCHOR_20261029.md)。原73尚未完整，整体收敛仍未证明；Direct33原训练条件数值结论与TaskStrict0/0保持，不启动34。

{utc(rows[0]['time'])}–{utc(rows[-1]['time'])} UTC，600秒/30秒间隔，21次原73三learner/归档/六等待器/五guard均按PID/start ticks验证live，三路步数每次严格增加，末次I/A/V {steps}。观察器自然结束，原科学继续，没有重启或结束训练。原I2714363/A2714364/V2714365同start42979895；原73全loss2718561、原71–73 2909145、标签3073648、V/A终端3137325/3137336、74仅恢复3096807保持。

74全loss四个审查源码及deploy.py位于runtime/parameter74_loss_preparation_20261029_v1；保持完整49–73历史，只追加74，配对73→74。父/新源码hash、逆映射、AST与独立静态检查通过。真实缺DECISION74部署被拒绝，未创建runs/parameter74_loss_20261028_v1或新训练。正向部署要求完整73 loss/全部标签/health/终端/实际图、准确恢复及实际74启动。

部署入口保留原65–67、68–70审查和原71–73 PLAN；进入74前还须绑定原71–73完整REVIEW、独立算术与实际图。另绑定新的条件性74–76 PLAN，不要求未来74–76结果才能部署74审查，不新增科学阈值。

条件性74–76窗口在原73运行、74/75/76均未启动时登记：`{W}`，PLAN SHA `{sha(W/'PLAN.json')}`。三个源码仅按71→74/72→75/73→76作窗口映射，逆变换/AST/hash通过。原5%/近零1/seed2026102855/5000 bootstrap/anchor55/4m保持；这是下一连续非重叠窗口，只有完整73及原71–73审查后仍需要续训才使用。目前未启动新窗口等待器，无REGISTRATION/REVIEW或未来训练；必须在实际74启动后才启动固定14400秒等待。

原71–73 PLAN SHA `{sha(old/'PLAN.json')}` 与原waiter身份保持，必须完整报告，全部历史失败与通过结论保留。近零保护是统计解释限制，不是把reward推离零的新目标。74–76登记不预先决定一定训练三轮，不替代原窗口。固定30×55秒/41250新增/4m append/markers23/47/terminal128/batch65536/UTD1/原LR/masks/reward/物理/gates均未修改。

同期{len(samples)}个guard样本，四卡最低{mins}%，均值{[round(s['mean'],6) for s in stats]}%，低于50计数{below}，最大间隔{guard['max_gap']:.6f}秒。原v5五进程保持，STOP/FAILURE不存在；含合成占用，不是纯科学吞吐或每瞬时保证。科研完成后仍保载，非跨重启服务。

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器env/bin/python。开工实际fetch/read maine8b4f7a8843d88e137e6c968447ca0a9796d5721/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，保存前再次fetch/read main3d2d1d9d4e5a3fd5fa57648033a20de44282bb22、baseline未变，安全快进保留非RL原108观察22→24记录，未操作其进程。遵循sii-research-sync，无子agent。

[证据manifest](evidence/{tag}/MANIFEST.json)。共享SSD包 `{archive}`，{len(members)}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/Python AST核验。[保存收据]({tag}_SAVE.json)。大checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份；HDD满只重写既有入口。

下一步继续原73，完成全loss/标签/health/全2184旧终端对比及原71–73统计审查，独立复算和看图；准确73恢复后再依据结果决定是否有限74。当前无74训练。
'''
(R/'docs'/(tag+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 第73轮十分钟核验与74/74–76准备

- [交接](docs/{tag}.md)：{utc(rows[0]['time'])}–{utc(rows[-1]['time'])}UTC共21次原73三learner/archive/六等待器/五guard身份live，steps严格增至{steps}，观察自然结束、科学继续，无重启。
- 74全loss四源/deploy静态就绪，完整49–73保留追加74、配对73→74；原65–67/68–70审查保留，要求原71–73完整审查/独立算术/实际图及条件性74–76准确PLAN。逆映射/AST/hash/独立静态通过，真实缺DECISION74拒绝，无74loss run/waiter或训练。
- 条件性74–76 PLAN{sha(W/'PLAN.json')[:8]}在原73 live/未来三轮未启动时登记；原5%/近零1/seed2026102855/5000/anchor55保持。无新窗口等待器，原71–73PLANc160b5d6/waiter2909145保持且须全审，不提前要求未来窗口结果。
- {len(samples)}guard样本min{mins}%、低于50{below}，含合成负载、科研完成也继续。SSD包{len(members)}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份；开工maine8b4f7a8/baselinef6e8f8c实际fetch/read，无子agent。Goal active、Direct34false。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[73十分钟核验与74/74–76准备](docs/{tag}.md)。原73/71–73继续，无74训练；GPU科研完成后仍保载，Goal active。**\n\n'+p.read_text())
hdd.write_text(pointer);assert hdd.read_text()==pointer
print(json.dumps(receipt,indent=2))
