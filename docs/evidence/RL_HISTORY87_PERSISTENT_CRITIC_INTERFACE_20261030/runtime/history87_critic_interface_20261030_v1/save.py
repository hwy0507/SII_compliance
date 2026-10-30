from pathlib import Path
import json,time,hashlib,ast,tarfile,socket,subprocess,os
D=Path(__file__).parent;B=D.parents[1];R=B/'repository/SII_compliance';O=B/'runs/history87_interface_snapshots_20261030_v1'
TAG='RL_HISTORY87_PERSISTENT_CRITIC_INTERFACE_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
for name in ['REVIEW.json','CACHE_SAVED_REVIEW.json','CONSUMER_REVIEW.json','FINISHED.json']:assert read(D/name)['passed']
assert not list(D.glob('*FAILURE*'))
for planname in ['PLAN.json','CONSUMER_PLAN.json']:
 for n,h in read(D/planname)['sources'].items():assert sha(D/n)==h
assert sha(D/'check_cache_and_saved.py')==read(D/'CACHE_PLAN.json')['source_sha256']
cache=read(D/'CACHE_SAVED_REVIEW.json');core=read(D/'REVIEW.json');consumer=read(D/'CONSUMER_REVIEW.json')
large=[]
for method,r in cache['methods'].items():
 f=Path(r['snapshot']['path']);assert sha(f)==r['snapshot']['sha256'];large.append(r['snapshot'])
put(O/'MANIFEST.json',dict(files=large,role='Interface-only zero-update migration, no online88 authorization, original complete87 remains formal parent'))
ids=[]
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:
 fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();assert fields[19]==start and fields[0]!='Z';ids.append(dict(pid=pid,start=start))
rows=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=read(D/'PLAN.json')['time']];assert time.time()-rows[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[r['utilization'] for r in rows[-1]['gpus']],synthetic_included=True,scientific_training_running=False,historical_dips_preserved=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,guard_identities=ids,goal='active',online88=False,direct34=False))
# Archive exact source and small evidence, including the actual old dependencies.
files={p for p in D.iterdir() if p.is_file() and p.suffix in {'.py','.json','.jsonl','.log'}}
files.add(O/'MANIFEST.json')
for p in (B/'runtime/parameter86_half_std_paired_20261030_v3').glob('*.py'):files.add(p)
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_HALF_STD86_COMPLETE_HISTORY87_FIT_20261030'/n)
E.mkdir();A.mkdir();entries=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 entries.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=entries,large_artifacts=large,scope='Shared SSD; no HDD or arm1 full backup'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(entries)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(entries)+1,all_member_bytes_and_python_ast_verified=True,main='89b3025e1b4660e40ac3a7b42fa3fabd27489638',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',large_artifacts=large,backup_scope='Shared SSD only; existing HDD pointer, not HDD/arm1 full backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
rows=[]
for m,v in core['methods'].items():
 c=consumer['methods'][m];rows.append(f"|{m}|{v['binding']['rows']}|{v['initial_q_max_errors']['ensemble']}/{v['initial_q_max_errors']['ensemble_targets']}|{len(v['negative_rejections'])}|{c['terminal_health_rows']}|{c['recorded_observation_events']}+1|")
text=f'''# 完整87历史critic持久化与原生接口验证

2026-10-30，Goal active。本轮实现并验证51维critic/replay持久化接口、严格父状态迁移和只读消费入口。正式训练父仍完整87；没有第88轮注册或训练，没有Direct34，没有把离线拟合权重用于正式训练。reward稳定和loss健康尚未达成，不能把软件验证写成收敛。

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。实际开工与收尾query/fetch/read main `89b3025e1b4660e40ac3a7b42fa3fabd27489638` 和 baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新增远端改动。遵守仓库sii-research-sync，无子agent。

## 实现与约束

源码 `{D}/persisted_history_critic.py`；只读入口 `{D}/history_consumers.py`。绑定准确完整87的checkpoint、全learner/replay digest、sidecar SHA、方法/维度/行数。原clock replay50扩为51，索引50只加当前动作前已经完成区间的累计外穿透特征 `p/(p+0.0002)`；terminal next使用终端区间，未广播未来最终峰值。每个stream独立计数，缺区间、重复区间、穿透递减被拒绝，环境恢复时全部stream清零，旧replay历史保持。

在线及target全10个critic首层插入零列；Q Adam对应moment插入零列，旧权重/moment/counter/LR和actor/alpha/RNG原样保留。actor的51维入口只取原49维，物理canonical48不变；原clock索引49、CHEQ采样/mixing、两目标reducer、terminal128、有限上界公式保持。专门适配原本写死50维的投影输入，重新绑定foreach target参数引用。学习历史列之后critic不确定性和CHEQ mixing可能变化，这是有意的模型修订，不能称为始终相同策略。

replay保持4m append-only及23/47容量标记，全部旧字段和bootstrap masks逐字节保持；两个新增列来自前轮审完的87因果sidecar。旧checkpoint不能直接当51维load，必须走明确迁移入口；持久化marker不匹配拒绝。

## 完成验证

|方法|旧replay行数|在线/target初始Q最大误差|负例拒绝数|终端health行数|记录观测/terminal事件|
|---|---:|---|---:|---:|---|
{chr(10).join(rows)}

主检查实际{core['elapsed_s']:.3f}秒：三方法所有旧learner状态逆迁移后精确同父；全部10,824,948旧行及新增特征正确，下一批65536旧字段/新增列和RNG精确；两stream原生动作/混合上下文/clock/RNG相同。所有原87checkpoint SHA保持。随机5/7维fixture共12次原生update（非正式checkpoint update），恢复后重复两次update全state精确，历史梯度非零、target引用和actor隔离通过。

独立保存/cache核验实际{cache['elapsed_s']:.3f}秒：用不同实现逐字段去除新增零列，原agent/Adam/其他state全digest相同；完整learner+replay快照写盘回读、51列实际GPU cache、65536抽样及RNG、mask前缀不确定后的完整检查和重抽通过。仅在可丢弃内存replay各加1条合成行，验证旧前缀、Bernoulli RNG和GPU行同步，再恢复；保存快照没有这些合成行。

只读consumer验证实际{consumer['elapsed_s']:.3f}秒：固定I short0600、A short0900、V short0000的原87记录各1375观测+terminal，外部seed2026102633；逐步输入历史/clock，原生raw/mixed动作和上下文与零列前精确同值，完整learner/RNG/replay不变。全终端all5在线/target health预测精确同父，原投影公式逐位相同。这里重放的是既有观测，不是新物理轨迹、冻结评测成绩或held-out性能。

全部核验0新物理，0实际父checkpoint optimizer update。所有结果和源码均保存，没有测试失败记录。

## 下一步

继续准备独立、有限的history在线修订登记。仍需把新接口接入完整trainer恢复/registration/启动检查、周期归档及health/frozen evaluator的调用链，验证实际起步后才能启动正式88。当前trainer候选只在已确认事件位置增加一次consume_interval，去掉这一行后与原87trainer逐字相同；它不是可直接运行的正式88 driver。只读consumer模块通过记录重放，但旧冻结脚本的完整gate/review/dispatch尚未接入，不能直接改cycle数字启动。

正式父必须完整87；不回退诊断86，不晋升前轮离线clone。有限stage保持30×55s/每方法最多41250新transition、batch65536/UTD1/原LR/reward/masks/物理/gate/filter/dt，除单独登记的history模型信息外不改。完整87原85—87稳定性全失败、I/V末loss回升继续保留。Direct33数值接受但冻结30 Task/Strict0/0，中断28缺最终内存证明；指定ESN仍不可用，不用他主机替代、不重复追问。partial75、74—76不可判和79安全中止及所有历史失败窗口保持。

## 保存与GPU

全迁移快照目录 `{O}`，每个文件明确标记 `interface_only_no_online_approval`，各SHA/字节在MANIFEST和保存收据。它们是未更新的迁移状态，原完整87仍正式训练父，不把它们列为训练88结果。大型产物仅共享SSD，非HDD/arm1全备份；HDD已有LATEST指针原位254字节更新。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐tar成员/AST核验，另验Git index/commit；仅成功push后观测远端才在包外写PUBLICATION。

GPU本轮{gpu['samples']}样本最低 `{gpu['minimum']}`%、低于50次数 `{gpu['below50']}`、末值 `{gpu['last']}`%。v7 supervisor97370和四worker原身份保持，用户要求科研结束后也保载；有合成负载，不冒充训练吞吐。历史v7预热0和v6 31/33/44低谷不删除，采样不保证采样间每瞬时；守护非重启服务。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 完整87历史critic持久化与原生接口通过

- [交接](docs/{TAG}.md)。51维critic/replay、actor49隔离、全10critic/Adam零列迁移、原投影/foreach/全部stream历史恢复实现；完整87三份旧learner和10824948旧行精确，Q初始误差0/0，45负例、下一65536/RNG通过。
- 完整迁移快照写盘重载、实际GPU cache及3次可丢弃合成append通过；两维随机fixture12次native update重复恢复精确。原87三条完整记录1375+terminal/外部RNG、all5终端health及投影通过；0新physics/正式update，不是新评测或reward改善。完整trainer/eval/health调度接入和有限88登记仍待，Goal active，无Direct34。
- GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束继续守护；共享SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，完整迁移快照仅SSD、非HDD/arm1全备份。main89b3025e/baselinef6e8f8c已fetch/read，发布见收据，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert len(data)<=254 and p.stat().st_size==254
if len(data)<254:data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(receipt));print('GPU',gpu)
