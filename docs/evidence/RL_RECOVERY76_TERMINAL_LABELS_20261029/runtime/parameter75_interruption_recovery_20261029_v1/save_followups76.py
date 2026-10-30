from pathlib import Path
import json,time,hashlib,tarfile,ast,subprocess,socket,math
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;RUN=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6');tag='RL_RECOVERY76_TERMINAL_LABELS_20261029'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def live(j):
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z';return dict(pid=j['pid'],proc_start_ticks=f[19])
folders=[B/f'runs/{m}_recovery76_terminal_followup_20261029_v1' for m in ['vmc','admittance']]+[B/'runs/parameter_recovery76_task_labels_20261029_v1']
snap=dict(time=time.time(),host=socket.gethostname(),learners=[],followups={},guard={})
for j in read(RUN/'LAUNCH.json')['jobs']:
 p=RUN/j['controller']/'train';assert not (p/'FAILURE.json').exists();v=live(j);v.update(method=j['controller'],progress=read(p/'PROGRESS.json'),samplers=len(Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split()));assert v['samplers']==30;snap['learners'].append(v)
snap['archive']=live(read(RUN/'MONITOR_LAUNCH.json'))
for folder in folders+[B/'runs/parameter_recovery76_loss_20261029_v1',B/'runs/parameter_recovery76_78_reward_stability_20261029_v1']:
 j=read(folder/'LAUNCH.json');assert sha(folder/'PLAN.json')==j['plan_sha256'];snap['followups'][folder.name]=dict(live(j),plan_sha256=j['plan_sha256'])
 for name in ['WAIT_FAILURE.json','FAILURE.json']:assert not (folder/name).exists()
 if folder in folders:
  p=read(folder/'PLAN.json')
  for n,h in p['sources'].items():assert sha(folder/n)==h
  for v in p.get('inputs',{}).values():assert sha(Path(v['path']))==v['sha256']
for m in ['vmc','admittance']:
 p=B/f'runs/{m}_recovery76_terminal_followup_20261029_v1';assert read(p/'ANCHOR_REVIEW.json')['passed'] and read(p/'ANCHOR_SAVED_REVIEW.json')['passed']
rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];assert time.time()-rows[-1]['time']<15
first=next(i for i,r in enumerate(rows) if all(v['utilization']>=50 for v in r['gpus']));stable=rows[first:]
for pid in [read(G/'LAUNCH.json')['pid'],*read(G/'LAUNCH.json')['workers'].values()]:
 f=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z'
snap['guard']=dict(path=str(G),first_warmup_samples=first,post_warmup_samples=len(stable),post_warmup_min=[min(r['gpus'][i]['utilization'] for r in stable) for i in range(4)],post_warmup_below50=[sum(r['gpus'][i]['utilization']<50 for r in stable) for i in range(4)],last=rows[-1],synthetic=True,keep_after_science=True)
write(D/'FOLLOWUP_FINAL_SNAPSHOT.json',snap)
E=R/'docs/evidence'/tag;E.mkdir(exist_ok=False);manifest=[]
sources=[p for folder in folders for p in folder.iterdir() if p.is_file() and p.suffix in ['.py','.json','.diff','.npz','.log']]
sources += [D/n for n in ['prepare_terminal76.py','prepare_labels76.py','deploy_terminal76.py','save_followups76.py','FOLLOWUP_FINAL_SNAPSHOT.json']]
for p in sorted(sources):
 data=p.read_bytes();rel=p.relative_to(B);dest=E/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 assert sha(p)==sha(dest);manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(dest)))
write(E/'MANIFEST.json',dict(files=manifest,time=time.time(),large_artifacts_excluded=True))
A=B/'repository'/tag;A.mkdir(exist_ok=False);tar=A/'FOLLOWUP_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 for x in t.getmembers():assert t.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),bytes=tar.stat().st_size,sha256=sha(tar),members=len(manifest)+1,member_bytes_and_python_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),compute_host=socket.gethostname(),pushed=False,push_failure='HTTPS username authentication unavailable',large_artifacts='Shared SSD; no full HDD/arm1 backup');write(A/'RECEIPT.json',receipt);write(R/'docs'/(tag+'_SAVE.json'),receipt)
vals={m:read(B/f'runs/{m}_recovery76_terminal_followup_20261029_v1/ANCHOR_SAVED_REVIEW.json')['independent_scalar_sse'] for m in ['vmc','admittance']}
steps='/'.join(str(j['progress']['steps']) for j in snap['learners'])
text=f'''\n\n## 05:55UTC后续：partial75终端基准和完整76标签等待已部署

原76三learner、归档/health、完整loss及76–78等待身份持续保持；本次快照steps {steps}、每路30sampler，无训练失败。原75中断结论不变。新两个终端等待器与一个全标签等待器见 `docs/evidence/{tag}/runtime/parameter75_interruption_recovery_20261029_v1/FOLLOWUP_FINAL_SNAPSHOT.json`，均仅只读诊断，无新训练。

partial75仍只有2244个terminal，与完整74的indices/57维feature/reward/masks全部精确相同，但权重和全replay分母已发生变化。以实际恢复的partial75 checkpoint重新CPU前向五critic，权重/前向RNG保持；独立scalar SSE VMC={vals['vmc']:.12f}，admittance={vals['admittance']:.12f}。保留原VMC五focus和A2752093；76完整后检查2244旧+30新增=2274、原两分母贡献及独立保存算术，完整图仍待实际生成与查看。不是完整75结果或收敛证明。

全标签工具明确比较完整74→恢复76，包含中途已保留partial75额外曝光，非连续完整周期。原180标签/90配对reward/模型/evaluator/物理0.2mm判据和Task-only变化检查保持，实际不完整76拒绝测试通过。等待完整归档与loss保存复核后自动运行交叉检查。

诊断准备期间首次VMC anchor读方法级`passed`键产生KeyError；方法收据本无该键。已保留首次源码/PLAN/日志，改成要求总审计passed且方法收据逐值完全相同，之后两路通过；无科学重启。全标签等待器初版使用了错误的loss失败文件名，身份核验后仅停止该诊断等待器并重启修正版，原LAUNCH/PLAN/source保留；三learner/guard未动。

GPU guardv6持续，排除最初{first}预热样本后{len(stable)}个样本各卡最低{snap['guard']['post_warmup_min']}%，低于50次数{snap['guard']['post_warmup_below50']}；包含合成负载，科学完成后继续。当前系统重启仍会终止进程，未宣称重启自启。

后续证据包 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员与源码AST检查通过。大型产物仍SSD，非HDD/arm1全备份。GitHub缺HTTPS认证，恢复提交a48d16cc与合并359c6ceb已在本地，远端发布仍待；不影响训练。Goal active，尚无77训练，Direct34false。
'''
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(p.read_text()+text);(A/'HANDOFF.md').write_text(p.read_text())
entry=f'''## 2026-10-29 — 恢复76全终端与标签后续

- [交接](docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md)。partial75的2244终端基准用真实恢复权重重新CPU前向并独立算术通过，V/A SSE {vals['vmc']:.9f}/{vals['admittance']:.9f}，旧feature/reward/masks精确、原focus与两分母保留。完整76两终端及全180标签等待已部署，真实不完整76拒绝，74→76额外partial75曝光明确；初次审计schema错误和等待器失败文件名修正原件保留，无科学重启。
- 原76/归档/全loss/76–78/guard保持，steps{steps}、各30sampler；guard预热后{len(stable)}样本min{snap['guard']['post_warmup_min']}%、低于50{snap['guard']['post_warmup_below50']}，科研完成仍保载。证据{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}已核SSD，非HDD/arm1全备份。main9defd6a4/baselinef6e8f8c已读，认证失败仅本地发布，Goal active、无77/Direct34/子agent。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':a,b=s.split('\n',1);p.write_text(a+'\n\n'+entry+b.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text('> **RL恢复76补充：实际partial75终端基准及76完整终端/标签等待已部署，原训练与GPU保载继续；见[当前交接](docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md)。**\n\n'+p.read_text())
print(json.dumps(receipt,indent=2));print(json.dumps(snap,ensure_ascii=False))
