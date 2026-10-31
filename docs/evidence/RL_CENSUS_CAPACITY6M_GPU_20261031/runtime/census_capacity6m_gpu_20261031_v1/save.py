from pathlib import Path
import ast,hashlib,json,shutil,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census_capacity6m_gpu_20261031_v1';R=B/'repository/SII_compliance'
TAG='RL_CENSUS_CAPACITY6M_GPU_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2,allow_nan=False);f.write('\n')
review=read(O/'REVIEW.json');assert review['passed'] and not (O/'FAILURE.json').exists()
assert review['disposable_optimizer_updates']==9 and not review['formal_updates'] and not review['physics_steps']
for p in Path('/proc').glob('[0-9]*/cmdline'):
 try:raw=p.read_bytes()
 except OSError:continue
 assert str(D/'check_gpu.py').encode() not in raw,'GPU checker still running'
plan=read(O/'PLAN.json')
for p,h in plan['sources'].items():assert sha(p)==h
for p in D.glob('*.py'):ast.parse(p.read_text())
for m,r in review['methods'].items():
 assert r==read(O/(m+'_REVIEW.json'))
 a=r['outcomes'];assert [x['tag'] for x in a]==['old4m','new6m','new6m_repeat']
 for k in ['batch_sha256','sampled_rng_digest','metrics','updated_full_state_digest']:assert all(x[k]==a[0][k] for x in a)
 for k in ['complete_device_mirror_equal','all_terminal_values_and_strata_equal','full_learner_adam_rng_restored','full_old_new_replay_rng_restored']:assert r[k]
 assert r['rows']==plan['parents'][m]['steps']
start=read(O/'LIVE_START.json')
for e in start['identities']:
 s=Path('/proc',str(e['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==e['start']
progress={m:read(B/'runs/parameter_census_cycle96_20261031_v1'/m/'train/PROGRESS.json') for m in review['methods']}
growth={m:progress[m]['steps']-start['progress'][m]['steps'] for m in progress};assert all(v>0 for v in growth.values())
rows=[json.loads(x) for x in Path('/tmp/sii_gpu_util_guard_20261031_recovery_v1/samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=plan['time']];assert rows and time.time()-rows[-1]['time']<15
gpu=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(O/'LIVE_END.json',dict(time=time.time(),identity_count_at_both_endpoints=len(start['identities']),continuous_observation=False,progress=progress,growth=growth,gpu=gpu))
(O/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
E.mkdir();A.mkdir();manifest=[]
for root in (D,O):
 for p in sorted(root.iterdir()):
  if not p.is_file() or p.suffix not in ('.py','.json','.jsonl'):continue
  rel=p.relative_to(B);dest=E/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);assert p.read_bytes()==dest.read_bytes()
  manifest.append(dict(relative=str(rel),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
 members=len(t.getmembers())
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=members,all_members_verified=True,backup_scope='Shared SSD small evidence; prior6m CPU preparation and full95/96 assets remain SSD; HDD pointer only')
put(A/'RECEIPT.json',receipt);put(R/'docs'/f'{TAG}_SAVE.json',receipt)
peaks={m:r['peak_device_allocated_bytes'] for m,r in review['methods'].items()}
entry=f'''## 2026-10-31 — 600万回放GPU原生更新等价通过；完整96仍待

- [交接](docs/{TAG}.md)。三份真实全95在GPU0比较原4m/新6m/重复6m，全部retained设备镜像、8533终端及32分层精确；65536批次与采样RNG相同，原loss/全部metrics和更新后完整learner/Adam/RNG digest逐值相同，随后全state恢复。
- 共9次隔离更新、0正式更新/physics、无权重保存；三原checkpoint hash保持。新容量尚未部署，准确全96父恢复及有限97契约仍待，既有21负例/跨4m/满6m拒绝证据保持；原94–96窗口及A19.7689%必要条件失败不变。
- 原101身份两端一致，steps增长{growth}；GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，guard继续。原三96训练/archive/两个消费者继续；完整96/原loss健康/联合收敛、Direct原结论及指定ESN缺失保持，Goal active。
- SSD小包{members}成员/SHA{receipt['sha256'][:8]}，HDD仅指针。开工main8b39c197/baselinef6e8f8c2实际query/fetch/read；GPU测试未修改原正式源码/协议。

'''
body=f'''# 600万容量GPU恢复与原生更新验证（2026-10-31）

Goal active。上一轮属于progress：完整CPU回放迁移与容量边界准备已完成；本轮补齐GPU缓存和实际学习更新兼容性。原第96轮三路训练继续，未重启、未派发97。

主机 `{socket.gethostname()}`，共享SSD `{B}`，Python `{B}/env/bin/python`。使用仓库sii-research-sync，实际query/fetch/read main `8b39c19760d2e69db66999c7ec05962a37e45335`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。没有子agent。

## 实际检查与结果

源码 `{D}/check_gpu.py`，独立输出 `{O}`。固定CPU54/nice15/GPU0、900秒上限、三方法各3次隔离更新；运行前GPU0空余{plan['gpu_snapshot'].splitlines()[0].split(',')[2].strip()}MiB，实际UUID `{plan['gpu_uuid']}`。原GPU1/2/3正式训练与四卡guard继续。

使用真实完整95三份已hash绑定checkpoint，恢复原census learner及完整4m回放，同时建立6m候选；保留2m/4m历史容量和双架构标记，显式传6m给默认4m的52维wrapper。比较全部保留行的GPU镜像与CPU原件；8533终端的values、indices和32种mask分层一致，不只比较抽样子集。

每方法从同一原learner/Adam/RNG和回放RNG出发，分别在old4m、new6m、new6m_repeat上调用原生65536批次的learner.update。三次批次值与采样RNG相同，全部metrics（含original_sampled_q_loss与条件估计loss）和更新后完整状态digest精确相同，gradient_steps每次恰加1。随后全部learner/Adam/RNG与两种回放RNG恢复原始状态，原checkpoint文件hash和原内存state digest不变。

总计9次临时optimizer更新，0正式更新、0physics、0权重保存。三方法峰值PyTorch已分配显存字节为{peaks}；不包含guard、CUDA上下文等其他进程，不能当整卡总显存。实际检查进程已结束，GPU0显存已释放，guard继续。

该结果证明同一完整95数据上的容量变更不会改变所测采样和原生更新，不是新数据跨4m后的算法等价、完整96恢复、训练改善或收敛结论。前轮CPU迁移、21负例、合成跨4m、满6m拒绝证据仍见[容量准备](RL_CENSUS_CAPACITY6M_PREPARATION_20261031.md)。

## 正式任务与后续

原101身份在准备前后两端PID/start一致，新增steps{growth}，不是全程连续身份观察。保存进度{ {m:p['steps'] for m,p in progress.items()} }；原三96 learner、90sampler、修正版archive、固定8533终端与全90比较消费者仍运行。GPU{gpu['samples']}样本最低{gpu['minimum']}%、低于50次数{gpu['below50']}；含synthetic guard与本轮临时GPU检查，不等于正式训练吞吐或每瞬时保证。

先完成全96回放/action/reward/原loss及图、真实新terminal、全90比较与固定终端评估，再绑定原94–96九组输入并执行原统计。A94→95的19.7689%稳定必要条件失败及所有历史失败保持。之后按完整96结果决定有限97，绑定真实96全部状态、适配三容量标记的协议/checkpoint/startup/fullreview、进行准确父状态恢复检查，才可接入候选容量；没有自动97/98。当前96仍是4m，原physics/MJB/Task/Strict/actor49/critic52/reward/LR/batch65536/UTD1保持。

Direct33原数值验收、冻结30条件Task/Strict0/0、旧28memory-invariance缺口与恢复2已证保持。指定ESN缺失、最终独立比较与联合收敛未完成。中断须保全最新96 partial，不回退95；MuJoCo物理state未保存。

## 归档

证据包 `{archive}`，{members}成员，SHA256 `{receipt['sha256']}`，全部tar成员与原文件字节核验。小证据在 `docs/evidence/{TAG}`；依赖前轮6m准备及原95/96大型SSD产物。HDD仅原254字节LATEST指针，不是完整备份。发布核验收据 `{A}/PUBLICATION.json`。
'''
(R/'docs'/f'{TAG}.md').write_text(body)
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=R/name;old=p.read_text();add=entry.replace('docs/'+TAG,TAG) if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
 else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');size=pointer.stat().st_size;data=(str(R/'docs'/f'{TAG}.md')+'\nGoal active; SSD assets.\n').encode();assert len(data)<=size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data)
print(json.dumps(dict(passed=True,growth=growth,gpu=gpu,members=members)))
