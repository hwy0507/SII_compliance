from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance'
T=B/'runs/parameter_violation_cycle90_20261030_v1';V=B/'runs/parameter_violation_cycle90_review_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';O=B/'runs/violation90_fixed87_terminal_followup_20261030_v1'
FD=B/'runtime/violation90_frozen_dispatch_20261030_v1';FP=B/'runtime/violation90_frozen_postprocess_20261030_v1';FA=B/'runs/parameter90_violation_frozen_saved_audit_20261030_v1'
TAG='RL_COMPLETE90_FROZEN90_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
full=read(V/'REVIEW.json');loss=read(V/'loss/REVIEW.json');interpret=read(D/'INTERPRETATION.json');follow=read(O/'REVIEW.json');abort=read(D/'ABORT_REVIEW.json');observed=read(D/'OBSERVATION_REVIEW.json');started=read(FD/'FROZEN_OBSERVATION_REVIEW.json')
assert all(x['passed'] for x in [full,loss,interpret,follow,abort,observed,started,read(D/'INTERPRETATION_SAVED_REVIEW.json')])
for folder in (D,V,O):
 plots=read(folder/'PLOT_INSPECTION.json');assert plots['actual_visual_inspection']
 for x in plots['plots']:assert x['inspected'] and sha(x['path'])==x['sha256']
for pid in (1096445,1096447,1096449,1096452,2283008):
 p=Path(f'/proc/{pid}/stat');assert not p.exists() or p.read_text().rsplit(')',1)[1].split()[0]=='Z'
identities=[]
jobs=read(F/'LAUNCH.json')['jobs']+[read(F/'REVIEW_LAUNCH.json'),read(FP/'PROCESS.json')]
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]+[(j['pid'],j['start']) for j in jobs]:
 p=Path('/proc',str(pid));s=(p/'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==str(start);identities.append(dict(pid=pid,start=s[19],state=s[0]))
frozen={}
for m in full['methods']:
 assert read(T/m/'train/FINISHED.json')['status']=='stopped_at_complete_cycle';assert not (F/m/'FAILURE.json').exists()
 frozen[m]=read(F/m/'PROGRESS.json');assert read(F/m/'STARTUP_REVIEW.json')['passed']
assert not (F/'REVIEW_FAILURE.json').exists() and not list(FP.glob('FAILURE*'))
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists()
rows=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(D/'OBSERVATION_PLAN.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=identities,frozen90=frozen,gpu=gpu,training90_completed=True,original90_archive_and_fixed_followup_completed=True,goal='active',automatic91=False))
files=set()
for folder in (D,V,O,FD,FP,FA):
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.npz','.png','.log'} and p.stat().st_size<10_000_000:files.add(p)
for p in F.rglob('*.json'):
 if len(p.relative_to(F).parts)<=2:files.add(p)
for m in full['methods']:
 for n in ('REGISTRATION.json','CHECK_ONLY_REVIEW.json','INITIAL_STATE_REVIEW.json'):files.add(T/m/n)
 for n in ('FINISHED.json','PROGRESS.json','EXECUTION.json'):files.add(T/m/'train'/n)
 for p in (B/'runs/parameter_violation_cycle90_archive_20261030_v1'/m).glob('*.json'):files.add(p)
files.update(T.glob('*.json'))
for n in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_FROZEN88_COMPLETE_20261030'/n)
files.add(B/'runs/parameter_violation90_92_reward_stability_20261030_v1/PLAN.json')
files.add(B/'runs/parameter_history88_90_reward_stability_20261030_v1/REVISION_BOUNDARY_90.json')
for n in ('rollout.json','TERMINAL.json'):files.add(T/'impedance/train/cycle_00090/active_long_train_0000'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Complete90, all90 training comparisons, full loss/health, fixed87 terminal followup and actual plots; all3 complete90 exact frozen restores and finite all90 dispatch/startup; global safety abort and software failure retained. Large checkpoints/raw remain shared SSD.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
remote=read(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 完整90已审；冻结90全90实际运行

2026-10-30 UTC，Goal active。原三路有限90训练及archive/full review/固定87终端跟踪正常结束，不重启。新冻结90已完成最终登记、三份实际完整checkpoint check-only恢复、实际有限派发和90秒启动检查；最终全90/raw/88→90配对仍待。未收敛，无91或Direct34。

主机 `{socket.gethostname()}`；共享SSD `{B}`，解释器 `{B}/env/bin/python`。实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，无新相关协议变化；使用sii-research-sync，无子agent。前序[冻结88全部完成](RL_FROZEN88_COMPLETE_20261030.md)。本轮源码 `{D}`，训练 `{T}`，完整审查 `{V}`，完整checkpoint `{B}/runs/parameter_violation_cycle90_archive_20261030_v1/<method>/cycle_00090.pt`。

| 方法 | 新transition/update | Task /30 | Strict /30 | mean reward | checkpoint SHA256 |
|---|---:|---:|---:|---:|---|
'''
for m,v in full['methods'].items():text+=f"| {m} | {v['new_transitions']} | {v['task']} | {v['strict']} | {v['reward_mean']:.12f} | `{v['checkpoint_sha256']}` |\n"
text+='\n全部旧回放精确保留、新current/next52和raw→mixed动作精确、全部新reward复算误差0，learner/optimizer有限。保持critic/replay52、actor49/canonical48、clock49/history50/rawbit51、已学history与Adam/双marker、4m append及23/47标记、terminal128/batch65536/UTD1/原LR/reward/masks及物理/MJB/gates/filter/执行器/dt5e−5；没有离线拟合权重晋升。\n\n'
text+=f'''阻抗`active_long_train_0000`在877动作/35.0800000006s安全中止，原因`global_penetration_exceeded_2mm`；原30分母保留，29条完整55s、1条中止，不补跑。全局峰穿透97.9125891mm，最深接触为office_v5_corner_top与target_object_geom；外部穿透仅0.04698594mm，最后current和terminal外部违规bit仍为0。上一轮同条件Task/Strict均成功、无abort。新增bit不是完整Task/Strict或全局安全状态，不能用它覆盖这类失败。`ABORT_REVIEW.json`绑定保存rollout/terminal/journal/transition/hash；非独立物理重跑或因果归因，不改物理门槛。

完整loss（首1000→末1000均值，全部原始点保存）：
'''
for m,v in loss['methods'].items():
 q=v['stats']['agent_train/q_loss'];act=v['stats']['agent_train/actor_loss'];text+=f"- {m}: critic {q['first1000_mean']:.9f}→{q['last1000_mean']:.9f}，max {q['maximum']:.9f}；actor {act['first1000_mean']:.9f}→{act['last1000_mean']:.9f}。\n"
text+='\n末段critic均值改善但I后段尖峰重现、三路actor上移；不能把有限值或单轮下降写成loss健康收敛。health、完整loss、训练逐条件变化、固定终端四图均已实际查看并绑定hash。\n\n'
for m,v in interpret['methods'].items():text+=f"{m}：89→90 mean变化{v['mean_reward_delta']:+.9f}；Task新增{v['task_gained']}、丢失{v['task_lost']}；Strict新增{v['strict_gained']}、丢失{v['strict_lost']}。\n\n"
text+='全部90条件及reward分项保留，保存回读/独立端点和核验通过；跨history51→violation52与额外在线训练，不做同修订稳定性或bit单独因果归因。首解释脚本在JSON path string调用Path.open时失败，尚未写结果、0新物理/更新；原脚本/PLAN/log保留，v2仅转换Path和绑定新源，重新执行通过。\n\n'
for m,v in read(O/'PLOT_INSPECTION.json')['summary'].items():text+=f"固定原87全部终端{m}：总masked SSE89→90 {v['total_masked_sse89']:.6f}→{v['total_masked_sse90']:.6f}（{v['relative_total_change']:+.3%}）；逐critic差{v['per_critic_delta']}。\n\n"
text+=f'''全部I2605/A2604/V2604旧终端/all5/原masks保留，完整learner/replay/RNG不变；I c0/1、A c3/4、V c0..3退化均保留。All-row SSE下降也不能替代in-bag拟合、策略安全或整体收敛。原88—90失败窗口不改，90—92统计方案当前只有完整90，不跑缺91/92的窗口，不自动训练91/92。

新冻结90 `{F}`：沿原预登记完整90、30原条件×三方法、seed2026102638、最多123750动作/99m子步、0更新。实际三份完整父恢复全learner/replay/digest/checkpoint精确，已绑定最终registration和实际图检；显式LAUNCH_AUTHORIZATION后才派发。启动观察{started['elapsed_s']:.3f}s/{started['samples']}样本通过，原evaluator/collector/postprocessor身份及物理CPU亲和性/动作进度保持。当前进度 `{frozen}`。最终全90结果、final fullstate invariance、raw审计与88→90配对尚待，原collector21600s截止不扩展。

派发源码 `{FD}`；后处理 `{FP}`，raw审计 `{FA}`；三者源/hash及真实缺完整90拒绝证据均保存。比较原88和新90的物理、reward、条件、action seed逐项一致，显式允许violation52修订；所有成功/失败与无接触NA保留。不得重复派发已结束的原冻结88或训练90。

GPU原guard97370及97399–97402持续，科研结束后也保载。本轮{gpu['samples']}采样/{gpu['elapsed_s']:.1f}s，min{gpu['minimum']}%、低于50{gpu['below50']}，末值{gpu['last']}%；含合成负载、非科研吞吐或每瞬时保证。旧v7 warmup0/v6低谷仍保留，非重启服务。

Direct原数值阶段已接受；冻结33全30 Task/Strict0/0、原28最终内存证明缺失仍保留，不新增成功要求、不为占用启动34。指定ESN缺失不替换，最终比较待。partial75、74—76不可判、79安全abort、90新abort、所有旧失败窗口/半std拒绝/软件失败保持。下一步依据完整90和固定终端分歧、阻抗安全退化，准备有记录的有限后续决定及全state恢复验证，不能用预登记统计自动派发91；原冻结90继续。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，tar成员/AST已核验；index/commit逐字核验及正常push/实际远端确认另存包外PUBLICATION。大checkpoint/raw仍原共享SSD，HDD仅原位254字节指针，非HDD/arm1全备份。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 完整90与安全中止已审；冻结90全90实际启动

- [交接](docs/{TAG}.md)。I40752/A,V41250新步，全旧replay及新52输入/动作/reward0误差；Task/Strict17/16、14/14、17/17。I long0000在35.08s全局穿透安全中止（97.91mm），外部bit0不覆盖该失败；原分母保留。critic末段下降但I尖峰/actor漂移，未收敛。
- 固定87旧终端all5 masked SSE：I−83.45%、A+9.70%、V+146.79%；所有退化保留，全state/RNG不变。全90训练对照及四实际图通过；首解释脚本路径类型失败/v2修复原件保留。完整90三份冻结check-only通过，有限全90实际派发及{started['elapsed_s']:.2f}s启动观察通过；最终raw/88→90配对/内存证明待。
- 原90/archive/终端等待正常结束勿重启，无91/Direct34；GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍保载。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验、HDD仅254字节指针，非HDD/arm1全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，正常发布见收据；Goal active，无子agent。

'''
for name in ('UPDATE_LOG.md','HANDOFF.md'):
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,frozen=frozen)))
