from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle93_20261031_v1';V=B/'runs/parameter_violation_cycle93_review_20261031_v1';F=B/'runs/violation93_fixed92_terminal_followup_20261031_v1';C=B/'runtime/violation93_completion_20261031_v1'
TAG='RL_COMPLETE93_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
full=read(V/'REVIEW.json');loss=read(V/'loss/REVIEW.json');follow=read(F/'REVIEW.json');dec=read(D/'TERMINAL_DECOMPOSITION.json');audit=read(D/'abort93/REVIEW.json')
assert all(x['passed'] for x in [read(D/'DECOMPOSITION_SAVED_REVIEW.json'),full,loss,follow,dec,audit,read(F/'SAVED_REVIEW.json'),read(F/'FINISHED.json'),read(C/'COMPARISON_FINISHED.json'),read(C/'INTERPRETATION_SAVED_REVIEW.json'),read(C/'CHANGED_CASES_REVIEW.json')])
assert read(V/'FINISHED.json')['completed'] and read(D/'COMPLETION_REVIEW.json')['passed']
for folder in [D,V,F,C]:
 plots=read(folder/'PLOT_INSPECTION.json');assert plots['actual_visual_inspection']
 for x in plots['plots']:assert x['inspected'] and sha(x['path'])==x['sha256']
completed=read(T/'LAUNCH.json')['jobs']+[read(T/'MONITOR_LAUNCH.json'),read(F/'PROCESS.json'),read(C/'PROCESS.json')]
for j in completed:
 p=Path('/proc',str(j['pid']),'stat')
 if p.exists():
  s=p.read_text().rsplit(')',1)[1].split();assert s[0]=='Z' or s[19]!=str(j.get('start',j.get('proc_start_ticks')))
for j in read(D/'WATCH_PLAN.json')['guard_identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
for m in full['methods']:assert read(T/m/'train/FINISHED.json')['status']=='stopped_at_complete_cycle'
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists() and not (guard/'FAILURE.json').exists()
rows=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(D/'WATCH_PLAN.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,original93_jobs_normal_completion=True,goal='active',automatic94=False))
files=set()
for folder in [D,V,F,C]:
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.npz','.png','.md'} and p.stat().st_size<10_000_000:files.add(p)
for m in full['methods']:
 for n in ['REGISTRATION.json','CHECK_ONLY_REVIEW.json','INITIAL_STATE_REVIEW.json']:files.add(T/m/n)
 for n in ['FINISHED.json','PROGRESS.json','EXECUTION.json','episodes.jsonl']:files.add(T/m/'train'/n)
 files.update((B/'runs/parameter_violation_cycle93_archive_20261031_v1'/m).glob('*.json'))
files.update(T.glob('*.json'))
for item in audit['sources']:files.add(Path(item['path']))
for item in read(C/'CHANGED_CASES_REVIEW.json')['cases']:
 for x in item['pair'].values():files.add(Path(x['source']['path']))
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_VIOLATION93_GUARD_PROGRESS_20261031'/n)
for n in ['PLAN.json','REVIEW.json','SAVED_ARITHMETIC_REVIEW.json','EARLY_WINDOW_FAILURE_91.json','PLOT_INSPECTION.json']:files.add(B/'runs/parameter_violation90_92_reward_stability_20261030_v1'/n)
for n in read(F/'PLAN.json')['source_hashes']:files.add(B/'runtime/violation93_terminal_followup_20261031_v1'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Complete93 all90 outcomes/replay/health/loss/changed cases and all shortened episodes; all8263 fixed92 terminal comparisons and error decomposition, actual plot inspection. Original failed windows retained. Large checkpoint/replay/raw stay SSD.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for m in tar.getmembers():assert tar.extractfile(m).read()==(E/m.name).read_bytes()
remote=read(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
result_rows='\n'.join(f"| {m} | {x['steps']} | {x['new_transitions']} | {x['task']}/30 | {x['strict']}/30 | {x['reward_mean']:.12f} | `{x['checkpoint_sha256']}` |" for m,x in full['methods'].items())
loss_rows='\n'.join(f"| {m} | {x['stats']['agent_train/q_loss']['first1000_mean']:.9f} → {x['stats']['agent_train/q_loss']['last1000_mean']:.9f} | {x['stats']['agent_train/q_loss']['maximum']:.9f} | {x['stats']['agent_train/actor_loss']['first1000_mean']:.9f} → {x['stats']['agent_train/actor_loss']['last1000_mean']:.9f} |" for m,x in loss['methods'].items())
terminal_rows='\n'.join(f"| {m} | {x['groups']['all']['total92']:.6f} | {x['groups']['all']['total93']:.6f} | {x['groups']['known_aborts']['total_delta']:+.6f} | {x['groups']['other_terminals']['total_delta']:+.6f} |" for m,x in dec['methods'].items())
report=(D/'REPORT_BODY.md').read_text()+f'''

## 完整93数值

| 方法 | 累计steps | 新增transitions | Task | Strict | mean reward | checkpoint SHA256 |
|---|---:|---:|---:|---:|---:|---|
{result_rows}

| 方法 | critic首1000→末1000均值 | critic最大值 | actor首1000→末1000均值 |
|---|---:|---:|---:|
{loss_rows}

| 方法 | 固定92全终端SSE92 | SSE93 | 已知中止行变化 | 其余全部终端变化 |
|---|---:|---:|---:|---:|
{terminal_rows}

## 来源与保存

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮按仓库sii-research-sync实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`。原训练 `{T}`；完整checkpoint `{B}/runs/parameter_violation_cycle93_archive_20261031_v1/<method>/cycle_00093.pt`；完整审查 `{V}`，固定92终端 `{F}`，训练比较 `{C}`，新审查与源码 `{D}`。版本、seed、源/MJB和完整父checkpoint hash保持原REGISTRATION/EXECUTION，已纳入证据。

原三learner、archive和两个消费者均正常完成并逐PID/start验证退出，勿重启。GPU原guard仍运行且科学完成不触发STOP；本轮{gpu['samples']}采样/{gpu['elapsed_s']:.3f}秒，最低{gpu['minimum']}%、低于50次数{gpu['below50']}、末值{gpu['last']}%。含synthetic guard、非纯科研吞吐或每瞬时保证，旧低谷保持；不是重启服务。

共享SSD `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐tar成员与Python AST核验。manifest `docs/evidence/{TAG}/MANIFEST.json`，index/commit字节核验及实际远端push收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，仅既有LATEST254字节原地更新回读，大checkpoint/replay/raw仍SSD，非HDD/arm1全备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
entry=(D/'ENTRY.md').read_text()+f"\n- GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束继续guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}；HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。Goal active，无子agent。\n\n"
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu)))
