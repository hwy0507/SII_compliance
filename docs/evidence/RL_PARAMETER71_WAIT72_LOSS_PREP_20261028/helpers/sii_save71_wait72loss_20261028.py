from pathlib import Path
import json,hashlib,ast,tarfile,time,datetime,socket,math,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance'
O=B/'runtime/parameter71_verified_wait_2244_20261028_v1';P=B/'runtime/parameter72_loss_preparation_20261028_v1'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
finished=read(O/'FINISHED.json');assert finished['samples']==7 and finished['all_original_identities_live']
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
tag='RL_PARAMETER71_WAIT72_LOSS_PREP_20261028';E=R/'docs/evidence'/tag;E.mkdir(exist_ok=False);manifest=[]
def copy(p,rel):
 d=E/rel;d.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();d.write_bytes(data);assert d.read_bytes()==data
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(path=str(rel),source=str(p),bytes=len(data),sha256=sha(d)))
for folder in [O,P]:
 for p in sorted(folder.iterdir()):
  if p.is_file() and p.suffix in ['.py','.json','.jsonl','.diff']:copy(p,folder.relative_to(B)/p.name)
for name in ['sii_prepare72_loss_20261028.py','sii_observe71_2244_20261028.py','sii_save71_wait72loss_20261028.py']:copy(Path('/tmp')/name,Path('helpers')/name)
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
doc=f'''# 第71轮原进程连续核验与72全loss审查准备

2026-10-28 UTC。Goal active，上一轮是已归档/发布的实质进展，本轮完成后续源码准备和原进程verified wait。承接[71早期审查、2124锚点及72仅恢复](RL_PARAMETER71_EARLY_ANCHOR_20261028.md)。Direct33原训练条件数值收敛判断保留、TaskStrict0/0，不启动34。当前在线参数RL尚未整体收敛。

## 真实运行观察

{utc(rows[0]['time'])}–{utc(rows[-1]['time'])} UTC，180秒/30秒间隔、共7次，原71三learner、archive、六等待器、五guard进程均按PID/start ticks验证live，三路步数每次严格增长；最后I/A/V {steps}。原learner2902207/2902208/2902211同start42203070保持。没有完整71归档或失败，观察结束是observer自然退出，不是科学结束；没有重启作业。详细身份/实时进度见[证据manifest](evidence/{tag}/MANIFEST.json)。

同期guard共{len(samples)}条约5秒采样，四卡最低{mins}%，均值{[round(s['mean'],6) for s in stats]}%，低于50计数{below}，最大间隔{guard['max_gap']:.6f}秒。原v5 supervisor3256866及四worker保持，STOP/FAILURE不存在。含合成负载，非科学吞吐或每瞬时保证；遵循用户要求，科学完成后也继续保载，非跨重启服务。

## 72全loss准备与验证

共享SSD `{B}`，实际计算主机 `{socket.gethostname()}`，Python env/bin/python。新准备目录runtime/parameter72_loss_preparation_20261028_v1包含audit.py、paired_gate.py、review_saved.py、wait.py、deploy.py。从原71同时周期映射，保护完整hash和原68–70字符串，逆变换/AST/diff检查通过。audit明确保留49–71全部历史、追加72；paired和独立review配对71→72；不移动历史窗口。

deploy绑定完整71 loss/标签/health/V+A终端及实际图、准确72恢复、旧65–67和68–70原审查、原71–73固定PLAN（SHA c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf）。当前PLAN只有[71,72,73]，不要求未来73结果才能部署72审查，不新增科学门槛。

真实执行deploy.py在缺DECISION72.json时非零拒绝，未创建72 loss run、waiter或72训练。独立静态检查确认history49..72、配对71/72、完整父/新source hash、准确原窗口路径及无提前启动。静态和负例成功不等于正向部署已通过；必须完整71审查并决定、实际72启动后才能运行该deploy。无需再次运行准备脚本覆盖现有目录。

原71全loss2909138/原71–73 2909145、标签3168755、V/A终端3247685/3247693、72仅恢复3191936继续；原训练协议/阈值保持。完整71后仍需独立全loss/label/health/terminal与实际图审查，再决定有限72，不以观察超时重启科学。

## 保存与同步

开工fetch/read main153448856358933ee350a1ab5bf1c1c0be8da82f和baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，保留并行非RL工作；遵循sii-research-sync，无子agent。共享SSD小包 `{archive}`，{len(members)}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/AST核验。[收据]({tag}_SAVE.json)。大checkpoint/replay/raw仍共享SSD，不是HDD/arm1全备份。HDD配额满，仅缩短重写现有恢复入口。
'''
(R/'docs'/(tag+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-28 — 第71轮三分钟核验与72全loss准备

- [交接](docs/{tag}.md)：{utc(rows[0]['time'])}–{utc(rows[-1]['time'])}UTC共7次原71三learner/archive/六等待器/五guard身份live，steps严格增长至{steps}；observer自然完成、科学继续，无重启。
- 72全loss四源/deploy静态就绪，49–71保留追加72/配对71→72；原65–67及68–70审查保持，绑定原71–73 PLAN不要求未来73结果。逆映射/AST/hash/独立静态通过，真实缺DECISION72拒绝，无72loss run/waiter或训练。
- {len(samples)}guard采样min{mins}%、低于50{below}，含合成负载，科学完成也继续，非瞬时保证。SSD包{len(members)}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份。开工main15344885/baselinef6e8f8c实际fetch/read，无子agent；Goal active、Direct34false。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[71连续观察与72全loss准备](docs/{tag}.md)。原71/71–73继续，72仅恢复、无训练；GPU完成后仍保载，Goal active。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
pointer=f'''# RL 2026-10-28 {utc(rows[-1]['time'])} UTC
ACTIVE. Cycle71 running; GPU guard stays on.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{tag}.md
Receipt docs/{tag}_SAVE.json
71 I2902207/A2902208/V2902211. NO72 training.
Guard3256866, /tmp/sii_gpu_util_guard_20261028_v5; no reboot service.
Large data SSD, not HDD/arm1 backup. Direct34=false.
'''
assert len(pointer.encode())<=p.stat().st_size;p.write_text(pointer);assert p.read_text()==pointer
print(json.dumps(receipt,indent=2))
