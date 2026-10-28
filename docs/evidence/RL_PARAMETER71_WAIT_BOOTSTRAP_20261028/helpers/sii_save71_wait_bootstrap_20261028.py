from pathlib import Path
import json,hashlib,ast,tarfile,time,datetime,socket,math,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance'
O=B/'runtime/parameter71_verified_wait_2248_20261028_v1';P=B/'runtime/parameter68_70_bootstrap_independent_20261028_v1'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
finished=read(O/'FINISHED.json');assert finished['samples']==21 and finished['all_original_identities_live']
rows=[json.loads(l) for l in (O/'SAMPLES.jsonl').read_text().splitlines()]
for m in ['impedance','admittance','vmc']:assert all(b['progress'][m]['steps']>a['progress'][m]['steps'] for a,b in zip(rows,rows[1:]))
g=Path('/tmp/sii_gpu_util_guard_20261028_v5');assert not (g/'STOP').exists() and not (g/'FAILURE.json').exists()
raw=[l for l in (g/'samples.jsonl').read_bytes().splitlines(keepends=True) if l.endswith(b'\n') and rows[0]['time']<=json.loads(l)['time']<=rows[-1]['time']]
(O/'GUARD_SAMPLES.jsonl').write_bytes(b''.join(raw));samples=[json.loads(l) for l in raw];assert len(samples)>100
stats=[]
for i in range(4):
 v=[next(g['utilization'] for g in r['gpus'] if g['gpu']==i) for r in samples];stats.append(dict(gpu=i,minimum=min(v),mean=math.fsum(v)/len(v),below50=sum(x<50 for x in v)))
write(O/'GUARD_REVIEW.json',dict(time=time.time(),samples=len(samples),start=samples[0]['time'],end=samples[-1]['time'],stats=stats,max_gap=max(b['time']-a['time'] for a,b in zip(samples,samples[1:])),synthetic_guard_included=True,instantaneous_guarantee=False,continue_after_science=True))
assert read(P/'REVIEW.json')['passed'] and read(P/'PACKED_REVIEW.json')['passed']
for phase in ['start','end']:assert read(O/('tail_'+phase)/'SAVED_REVIEW.json')['passed']
tag='RL_PARAMETER71_WAIT_BOOTSTRAP_20261028';E=R/'docs/evidence'/tag;E.mkdir(exist_ok=False);manifest=[]
def copy(p,rel):
 d=E/rel;d.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();d.write_bytes(data);assert d.read_bytes()==data
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(path=str(rel),source=str(p),bytes=len(data),sha256=sha(d)))
for folder in [O,P]:
 for p in sorted(folder.rglob('*')):
  if p.is_file() and p.suffix in ['.py','.json','.jsonl','.npz'] and not p.name.endswith('_bootstrap.json'):copy(p,p.relative_to(B))
for name in ['sii_tail71_2248_20261028.py','sii_bootstrap68_70_independent_20261028.py','sii_observe71_2248_20261028.py','sii_save71_wait_bootstrap_20261028.py']:copy(Path('/tmp')/name,Path('helpers')/name)
for n in ['PLAN.json','REGISTRATION.json','REVIEW.json','SAVED_ARITHMETIC_REVIEW.json']:
 p=B/'runs/parameter_capacity68_70_reward_stability_20261028_v1'/n;copy(p,Path('original68_70')/n)
write(E/'MANIFEST.json',dict(time=time.time(),files=manifest,all_bytes_and_python_ast_verified=True,raw_bootstrap_draws_losslessly_packed_in_npz=True))
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
tailtable=''
for m in ['impedance','admittance','vmc']:
 a=read(O/'tail_start/REVIEW.json')['methods'][m];z=read(O/'tail_end/REVIEW.json')['methods'][m]
 def stat(r,k):return r['fields']['agent_train/'+k]['mean']
 tailtable+=f"|{m}|{stat(a,'q_loss'):.9f}→{stat(z,'q_loss'):.9f}|{stat(a,'actor_loss'):.9f}→{stat(z,'actor_loss'):.9f}|{stat(a,'entropy_coefficient'):.9f}→{stat(z,'entropy_coefficient'):.9f}|\n"
doc=f'''# 第71轮十分钟观察及原68–70不确定区间独立复核

2026-10-28 UTC。Goal active。承接[71观察与72完整loss准备](RL_PARAMETER71_WAIT72_LOSS_PREP_20261028.md)。本轮新增原始样本核验及独立bootstrap证据，没有改动科学训练、停止原进程或宣布收敛。Direct33原训练条件数值结论保留，TaskStrict0/0，不启动34。

## 原71连续运行

{utc(rows[0]['time'])}–{utc(rows[-1]['time'])}UTC，600秒/30秒、21次原71三learner、archive、六审查等待器和五guard PID/start ticks均live。三路每次步数严格增加，末次I/A/V {steps}。原learner2902207/2902208/2902211同start42203070保持；没有完整71或失败。observer自然结束，科学继续，无重启。固定30×55/41250新增/4m replay/batch65536/UTD1及原LR/masks/reward/物理/gate不变。

观察前后分别保存三路最新1000条完整optimizer原始字节（事后取样非前瞻窗口），记录来源offset/完整前缀hash，源跨度回读精确。步号连续、所有数值有限、独立fsum均值/极值核验通过。

|路|两次最新1000 critic均值|actor均值|temperature均值|
|---|---|---|---|
{tailtable}
仅这两段在途样本，不代替完整71 loss/health或固定reward窗口，也不以有限性单独证明健康收敛。其间未保存的更新仍由原完整审查负责。

## 原68–70 bootstrap独立复核

原REVIEW与SAVED_ARITHMETIC_REVIEW保持原字节，原标量复核的bootstrap_reruns=0仍描述当时事实。本轮在新runtime/parameter68_70_bootstrap_independent_20261028_v1进行事后独立复算：三类各10条件、按condition排序、seed2026102855+方法序号、5000次原分层重采样保持；用独立整数索引构造、math.fsum逐样本均值、手写排序线性分位数，不调用原审核脚本或原np.quantile。新物理/优化更新均0。

|路|68→70回报差的原95%条件构成敏感区间|每轮斜率区间|
|---|---|---|
|I|[-0.037629027,8.709085586]|[-0.018814514,4.354542793]|
|A|[-0.063797918,5.100350875]|[-0.031898959,2.550175438]|
|V|[-0.066808664,0.119972685]|[-0.033404332,0.059986342]|

与原保存区间最大差异I1.77636e−15/A9.15934e−16/V8.88178e−16，通过1e−12数值容差。输入episode/原报告/登记前后hash保持。全部5000×30索引及delta/slope保存原JSON在共享SSD，并无损打包NPZ（613319bytes，SHA49663ddcd5f8fb0f16a4174a810eafb7cbfe6f5241e3df902cc154d1bdf29e06），所有数组精确回读。

三者区间都含0，但“包含0”并不证明等价或稳定；I/A区间宽，原描述性5%/近零判定未改，整体未收敛结论保持。这里只核验条件构成敏感性，不是独立训练seed、冻结策略性能或泛化。原71–73 PLAN/5%/近零1/seed/5000保持，无提前窗口结论。后续必须完整71审查后决定有限72。

## GPU与保存

同期{len(samples)}个guard样本最低{mins}%，低于50计数{below}，含合成占用，非每瞬时保证。v5 supervisor3256866及四workers保持，STOP/FAILURE不存在；科研完成后继续保载，非跨重启服务。

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，env/bin/python。开工mainf2198d05d521cabb12d5640a9d7dacd9b1608bc3/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d实际fetch/read，保留非RL工作、遵循sii-research-sync，无子agent。[证据manifest](evidence/{tag}/MANIFEST.json)。

共享SSD包 `{archive}`，{len(members)}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/AST核验。[收据]({tag}_SAVE.json)。大checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份；HDD满仅重写既有入口。原71科学与71–73等待器继续，72 full-loss准备已就绪但未部署，无72训练。
'''
(R/'docs'/(tag+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-28 — 第71轮十分钟核验与原68–70 bootstrap复核

- [交接](docs/{tag}.md)：{utc(rows[0]['time'])}–{utc(rows[-1]['time'])}UTC共21次原71三learner/archive/六等待器/五guard身份live，steps严格增至{steps}；observer自然结束、科学继续，无重启。前后各三路1000日志原字节/全数值/连续步号/独立算术通过，仅在途样本。
- 原68–70分层5000 bootstrap独立整数索引/标量均值/手写分位数复核通过，最大区间差1.78e−15；旧收据/阈值不变。I/A宽区间、V较窄，含0不证明稳定；原整体未收敛保持。全部draws/delta/slope无损NPZ回读，0新物理/更新。
- {len(samples)}guard样本min{mins}%、低于50{below}，含合成负载、科学完成也继续。SSD包{len(members)}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份。开工mainf2198d05/baselinef6e8f8c实际fetch/read，无子agent；Goal active、Direct34false、无72训练。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[71十分钟观察与68–70独立复核](docs/{tag}.md)。原71继续，无72训练；GPU完成后仍保载，Goal active。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
pointer=f'''# RL 2026-10-28 {utc(rows[-1]['time'])} UTC
ACTIVE. Cycle71 running; GPU guard stays on.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{tag}.md
Receipt docs/{tag}_SAVE.json
71 I2902207/A2902208/V2902211. NO72 training.
Guard3256866; no reboot service. Large data SSD, not HDD/arm1 backup.
Direct34=false.
'''
assert len(pointer.encode())<=p.stat().st_size;p.write_text(pointer);assert p.read_text()==pointer
print(json.dumps(receipt,indent=2))
