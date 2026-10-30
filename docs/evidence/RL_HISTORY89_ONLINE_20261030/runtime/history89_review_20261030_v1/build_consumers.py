from pathlib import Path
import re,ast,hashlib,json,difflib,time,shutil
D=Path(__file__).resolve().parent;B=D.parents[1];OLD=B/'runtime/history88_review_20261030_v3';RUN=B/'runs/parameter_history_cycle89_20261030_v1'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
records={}
for src,dst in [('startup88.py','startup89.py'),('review88.py','review89.py'),('archive88.py','archive89.py'),('loss88.py','loss89.py'),('observe88.py','observe89.py')]:
 old=(OLD/src).read_text();s=old
 paths={'parameter_history_cycle88_20261030_v2':'parameter_history_cycle89_20261030_v1','parameter_history_cycle88_20261030_v1':'parameter_history_cycle89_20261030_v1','parameter_history_cycle88_archive_20261030_v2':'parameter_history_cycle89_archive_20261030_v1','parameter_history_cycle88_review_20261030_v2':'parameter_history_cycle89_review_20261030_v1','parameter_history_cycle88_view_20261030_v2':'parameter_history_cycle89_view_20261030_v1','cycle_00088':'cycle_00089','startup_v3':'startup','review88.py':'review89.py','health88.py':'health89.py','loss88.py':'loss89.py','loss88.png':'loss89.png','automatic89':'automatic90','Cycle88 archive':'Cycle89 archive','New history88 updates':'New history89 updates'}
 s=re.sub('|'.join(map(re.escape,sorted(paths,key=len,reverse=True))),lambda m:paths[m.group()],s)
 # Simultaneous cycle literals; historical history_critic_amendment.first_cycle remains88.
 s=re.sub(r"(\['(?:cycle|parent_cycle|new_cycle)'\]\s*==\s*)(87|88)\b",lambda m:m[1]+str(int(m[2])+1),s)
 s=s.replace('cycle=88','cycle=89').replace("'--cycle','88'","'--cycle','89'")
 if src=='startup88.py':
  s=replace(s,"np.testing.assert_array_equal(v,a[k][:n,:50] if k in ('observations','next_observations') else a[k][:n])","np.testing.assert_array_equal(v,a[k][:n])")
  s=replace(s," peaks=np.load(h['sidecar']['path'],mmap_mode='r')\n for col,key in enumerate(('observations','next_observations')):np.testing.assert_array_equal(a[key][:n,50],feature(peaks[:,col]))"," assert old['history_critic_amendment']==h and original[KEY]==old['replay'][KEY]==marker(h['binding'])")
 if src=='review88.py':
  s=s.replace('complete recovery87','complete history88')
  s=replace(s,"assert np.array_equal(v,arr[k][:n,:50] if k in ('observations','next_observations') else arr[k][:n])","assert np.array_equal(v,arr[k][:n])")
  s=replace(s,"    peaks=np.load(h['sidecar']['path'],mmap_mode='r')\n    for col,key in enumerate(('observations','next_observations')):np.testing.assert_array_equal(arr[key][:n,50],feature(peaks[:,col]))","    assert old['history_critic_amendment']==h and old['learner'][KEY]==old['replay'][KEY]==marker(h['binding'])")
 if src=='loss88.py':s=replace(s,"n=reg['history_critic_amendment']['binding']['rows']","n=reg['history_critic_amendment']['binding']['rows']+41250")
 ast.parse(s);(D/dst).write_text(s);(D/(dst+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(OLD/src),tofile=str(D/dst))))
 records[dst]=dict(parent=str(OLD/src),parent_sha256=sha(OLD/src),sha256=sha(D/dst))
for name in ['persisted_history_critic.py','diagnose_published_value_bound_20261025.py','published_pair_reduction_learner_20261026.py','published_exact_projected_learner_20261026.py','published_finite_target_projection_20261026.py','published_projected_terminal_learner_20261026.py','published_target_pair_mean_20261026.py','published_terminal_loss_weight_20261026.py']:
 shutil.copyfile(OLD/name,D/name)
shutil.copyfile(OLD/'health88.py',D/'health89.py');assert sha(OLD/'health88.py')==sha(D/'health89.py')
(D/'CONSUMER_ADAPTATION.json').write_text(json.dumps(dict(time=time.time(),files=records,health_byte_identical=True,old_replay_all51_columns_directly_equal=True,old_history_binding_rows_stay87=True,loss_baseline_full88_rows=True,physical_steps=0,updates=0),indent=2)+'\n')
(D/'OBSERVATION_PLAN.json').write_text(json.dumps(dict(time=time.time(),source_sha256=sha(D/'observe89.py'),startup_wait_seconds=1800,observe_seconds=120,interval_seconds=10),indent=2)+'\n')
print(json.dumps(records,indent=2))
