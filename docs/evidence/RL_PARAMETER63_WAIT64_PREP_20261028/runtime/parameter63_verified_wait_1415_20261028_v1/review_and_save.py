from pathlib import Path
import json,time,math,hashlib,tarfile,ast,shutil
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';OUT=Path(__file__).parent
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2)+'\n')
done=read(OUT/'OBSERVER_FINISHED.json');assert done['reason']=='finite_observation_elapsed'
rows=[json.loads(s) for s in (OUT/'SAMPLES.jsonl').read_text().splitlines()]
assert len(rows)>=20 and all(x['index']==i for i,x in enumerate(rows))
assert all(all(j['live'] for j in x['learners']+x['watchers']) for x in rows)
assert all(not j['failure'] and not j['finished'] for x in rows for j in x['learners'])
for i in range(3):assert all(a['learners'][i]['progress']['steps']<c['learners'][i]['progress']['steps'] for a,c in zip(rows,rows[1:]))
review=dict(passed=True,time=time.time(),samples=len(rows),first_time=rows[0]['time'],last_time=rows[-1]['time'],first_steps=[x['progress']['steps'] for x in rows[0]['learners']],last_steps=[x['progress']['steps'] for x in rows[-1]['learners']],all_original_identities_held=True,steps_strictly_increased=True,observer_exit_reason=done['reason'],training_restarted=False,convergence_claim=False)
write(OUT/'REVIEW.json',review)
guard=[json.loads(s) for s in Path('/tmp/sii_gpu_util_guard_20261028_v5/samples.jsonl').read_text().splitlines()]
guard=[x for x in guard if rows[0]['time']<=x['time']<=rows[-1]['time']]
assert len(guard)>80
(OUT/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in guard))
gr=dict(passed=True,time=time.time(),samples=len(guard),first_time=guard[0]['time'],last_time=guard[-1]['time'],gpus={},max_gap_seconds=max(c['time']-a['time'] for a,c in zip(guard,guard[1:])),synthetic_guard_included=True,continuous_instantaneous_guarantee=False)
for gpu in range(4):
    vals=[next(g['utilization'] for g in x['gpus'] if g['gpu']==gpu) for x in guard]
    gr['gpus'][str(gpu)]=dict(min=min(vals),mean=math.fsum(vals)/len(vals),below50=sum(v<50 for v in vals))
write(OUT/'GUARD_REVIEW.json',gr)
tag='RL_PARAMETER63_WAIT64_PREP_20261028';dest=R/'docs/evidence'/tag;assert not dest.exists();dest.mkdir(parents=True)
files=list(OUT.glob('*.py'))+list(OUT.glob('*.json'))+list(OUT.glob('*.jsonl'))
files+=list((B/'runtime/parameter64_loss_preparation_20261028_v1').iterdir())
terminal=B/'runs/vmc62_terminal_anchor_followup_20261028_v1'
files += [terminal/n for n in ['review_new_terminals.py','review_new_terminals.py.diff','NEW_TERMINALS_REVIEW.json','NEW_TERMINALS_SOURCE_REVIEW.json','NEW_TERMINALS_LABEL_REVIEW.json']]
members=[]
for p in sorted(files):
    assert p.is_file();rel=p.relative_to(B);q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);assert p.read_bytes()==q.read_bytes()
    if q.suffix=='.py':ast.parse(q.read_text())
    members.append(dict(source=str(p),member=str(rel),bytes=q.stat().st_size,sha256=sha(q)))
write(dest/'MANIFEST.json',dict(time=time.time(),members=members,all_python_ast_passed=True,large_artifacts_excluded=True))
pack=B/'repository'/(tag+'_'+time.strftime('%H%M%S',time.gmtime()));pack.mkdir();archive=pack/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tf:
    for x in members:tf.add(dest/x['member'],arcname=x['member'])
    tf.add(dest/'MANIFEST.json',arcname='MANIFEST.json')
with tarfile.open(archive) as tf:
    for x in members:
        v=tf.extractfile(x['member']).read();assert len(v)==x['bytes'] and hashlib.sha256(v).hexdigest()==x['sha256']
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(members),all_member_bytes_verified=True,all_python_ast_passed=True,large_artifacts_remain_shared_ssd=True,hdd_or_arm1_full_backup=False)
write(R/'docs/RL_PARAMETER63_WAIT64_PREP_SAVE_20261028.json',receipt)
print(json.dumps(dict(observation=review,guard=gr,archive=receipt),indent=2))
