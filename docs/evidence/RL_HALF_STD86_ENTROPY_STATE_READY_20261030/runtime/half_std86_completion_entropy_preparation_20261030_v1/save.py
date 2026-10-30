from pathlib import Path
import json,time,hashlib,ast,tarfile,socket,subprocess,os
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';P=B/'runs/parameter86_half_std_paired_20261030_v3'
TAG='RL_HALF_STD86_ENTROPY_STATE_READY_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def check(j):
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==str(j['start']) and s[0]!='Z';return dict(pid=j['pid'],start=s[19],state=s[0])
assert read(D/'ENTROPY_INTERFACE_REVIEW.json')['passed'] and read(D/'ENTROPY_ACTUAL87_REVIEW.json')['passed']
assert not (D/'WAIT_FAILURE.json').exists() and not (P/'REVIEW_FAILURE.json').exists()
states={}
for j in read(P/'LAUNCH.json')['jobs']:
 d=P/j['group'];assert not (d/'FAILURE.json').exists()
 if (d/'FINISHED.json').exists():assert read(d/'FINISHED.json')['passed'];states[j['group']]='verified_terminal'
 else:states[j['group']]=check(j)
for name,j,out in [('reviewer',read(P/'REVIEW_LAUNCH.json'),P/'FINISHED.json'),('independent_raw_wait',read(D/'WAIT_IDENTITY.json')['job'],D/'WAIT_FINISHED.json')]:
 if out.exists():assert read(out)['passed'];states[name]='verified_terminal'
 else:states[name]=check(j)
old=read(B/'runtime/recovery87_full_and_seed_review_20261030_v1/SAVE_SNAPSHOT.json')
for j in old['identities']:
 if j['name'].startswith('guard') or j['name'].startswith('gpu'):states[j['name']]=check(dict(pid=j['pid'],start=j['proc_start_ticks']))
progress={k:read(P/k/'PROGRESS.json') for k in read(P/'PLAN.json')['groups']}
samples=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()];samples=[x for x in samples if x['time']>=read(D/'PLAN.json')['time']];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples));gpu=dict(samples=len(samples),minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,historical_dips_preserved=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),states=states,progress=progress,gpu=gpu,goal='active',automatic88=False,direct34=False))
files=set(p for p in D.iterdir() if p.is_file() and p.suffix in {'.py','.json','.jsonl','.txt','.diff'})
for p in P.iterdir():
 if p.is_file() and p.suffix in {'.json','.log'}:files.add(p)
for k in progress:
 for p in (P/k).iterdir():
  if p.is_file() and p.suffix in {'.json','.log'}:files.add(p)
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_COMPLETE87_HALF_STD86_RUNNING_20261030'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,active_files_are_snapshots=True,large_artifacts='Original SSD, not full HDD/arm1 backup'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='7bff39ecbb3eda9b3ddb0b991f8893b4cb97aafb',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
actual=read(D/'ENTROPY_ACTUAL87_REVIEW.json');interface=read(D/'ENTROPY_INTERFACE_REVIEW.json')
text=f'''# 半标准差评测继续；训练熵目标持久化基础已核验

2026-10-30，Goal active。上一轮完成87/冻结86原16审查并启动唯一半标准差配对，属于实质进展。本轮实际查询、fetch/read main `7bff39ecbb3eda9b3ddb0b991f8893b4cb97aafb` 和 baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新增远端变化；按仓库sii-research-sync发布，无子agent。完整87未收敛，完整结论与边界仍见 [上一交接](RL_COMPLETE87_HALF_STD86_RUNNING_20261030.md)。

主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。新源码/证据 `{D}`，科学评测 `{P}`，冻结runtime未修改。

## 在途原16与全量独立审计

原PLAN0d857019、四固定86组合×同四动作seed、pre-tanh std×0.5、最多16×55s/22000动作/1760万子步/0更新不变。没有重启或新增科学回合。四evaluator PID1280069/72/75/76的start身份和reviewer1280079均已重新核验，允许已完成有FINISHED的任务自然退出，不依据旧PROGRESS重启。

保存进度(完整回合数,seed,在途动作) `{ {k:(v['completed_episodes'],v['seed'],v['actions']) for k,v in progress.items()} }`。只记录运行进度，不从部分seed选方案；最终全16/最终state不变/paired图和独立raw审计仍待。

新唯一等待审计器PID1888816/start574492188，继承原LAUNCH+原wall deadline，不延长科学预算、不启动physics。每30秒检查原四evaluator和reviewer的实际/proc身份或明确完成收据、失败文件与GPU新鲜样本；原完整review完成才调用 `audit_half_std_raw.py`。该审计在前轮原16独立入口上明确允许并保留有安全原因的短回合，检查全部实际子步/动作、dt5e-5、有限值、峰矩、外穿透、接触分母与reward重建；不强制所有候选必须跑满才被统计，不删除失败，不新增forward/physics/update。入口与原版本diff保留。

恢复时先读原root FINISHED/REVIEW/PAIRED_REVIEW/PAIRED_SAVED_REVIEW，以及新目录WAIT_FINISHED/HALF_STD_RAW_REVIEW/HALF_STD_RAW_SAVED_REVIEW；仍在运行就核验PID/start继续等待。完整后实际查看两张结果图并保留PLOT_INSPECTION，然后审全16增益和退化。半标准差是推理采样干预，不证明训练熵目标等价或一定有效，不自动88/Direct34。

## 解决训练熵目标在恢复时丢失的基础接口

原PublishedLearner不持久化SAC target_entropy。新增独立 `persisted_entropy_target.py`，marker版本1绑定明确target、5/7动作维和准确父learner digest。只允许显式启用迁移且digest完全匹配的旧父进入；后续恢复必须marker准确，拒绝缺失/错误版本/目标/维度/父摘要。state保存和update都检查当前目标未漂移，不能从未恢复的fresh learner开始训练；不覆盖actor forward。

此处只准备恢复基础，未选定新的科学目标、未创建88训练checkpoint。真实完整87全部三方法测试保持原目标I−5/A,V−7；除新marker外，完整权重/actor、q与alpha优化器、RNG、更新计数和所有旧目标marker逐digest精确一致，内存序列化/反序列化再恢复精确，原checkpoint前后SHA不变。只读过原replay digest，未重建Replay对象，不冒称本次重新验证全replay恢复。三份原87checkpoint和准确父digest见ENTROPY_ACTUAL87_REVIEW。

随机初始化的真实native CHEQ接口测试覆盖5维minimum和7维mean：保持原目标时一次真实native update与原实现的完整后状态/全部metrics精确一致；测试用替代目标分别−6/−8时，alpha梯度差约1.0、原native target metric与新增applied metric准确，完整序列化恢复精确。17项拒绝测试通过。**这些−6/−8仅是软件测试值，不是科学选定超参数。** 成功测试6次native update调用；先前三次失败尝试各2次，共另6次，总12次随机fixture调用，每调用内部含原optimizer步骤，不把调用数冒充每个优化器step数。实际checkpoint更新0、physics0。

初版逐字比对失败保留：所有数值/权重/优化器/RNG完全相同，只有step_metrics中原target为整数−5、适配器为浮点−5.0；已改成原目标时保留原整数类型。原失败源码、记录与诊断保留；不是原科学模型损坏。当前adapter SHA `{sha(D/'persisted_entropy_target.py')}`。

这尚不足以直接部署训练。若全16证据支持另登记训练熵修订，必须明确有限预算和目标，统一trainer/resume/frozen-eval/health的loader与diagnostics、拒绝旧loader静默忽略marker，并验证完整实际启动。新的训练父必须完整87，不能从诊断86回退。当前仍无88决定/启动和Direct34。

## GPU与恢复材料

原v7守护保持，科学结束仍合成保载。此次{gpu['samples']}采样，最低 `{gpu['minimum']}`%、低于50次数 `{gpu['below50']}`，末值 `{gpu['last']}`%。合成占用不等同科研吞吐，历史warmup0/v6低谷保留，不保证采样间每个瞬时；不是重启自启服务。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`；tar逐成员字节/源码AST已核，Git index/commit另核。依赖前包521成员/SHAabd952ef的完整87与原16/半std源码证据；大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份。HDD LATEST原位254字节指向本文。成功正常push并观察实际远端后才在包外写PUBLICATION。

Direct33数值阶段接受但冻结全30 Task/Strict0/0，旧28缺最终内存证明；指定ESN不可用，不替换/重复追问。原partial75、不可判74—76、79安全中止和历史所有窗口失败保持。Goal active，完成要求仍是四方法收敛、冻结测试与指定比较，不能以本次软件预检通过替代。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 半标准差评测继续；熵目标持久化基础通过

- [交接](docs/{TAG}.md)。原固定86同16 std×0.5评测按原身份继续，未扩预算/重启/提前选seed。唯一PID1888816原deadline内等待完整review后全raw独立复算，保留短回合/失败；完整结果与图仍待，无自动88/Direct34。
- 新版本化entropy marker绑定target/维度/准确父，17拒绝、两维真实native同目标update逐字等价与替代测试目标alpha梯度/序列化通过；真实完整87三份全learner仅加marker其余精确、原SHA不变，0实际更新/physics。失败整数vs浮点metadata诊断保留；12随机fixture native调用不算科学训练。仅恢复基础、未选科学目标，trainer/eval/health接入仍待，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍保载。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验、非HDD/arm1全备份；main7bff39ec/baselinef6e8f8c实际fetch/read，发布见收据，无子agent。

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
