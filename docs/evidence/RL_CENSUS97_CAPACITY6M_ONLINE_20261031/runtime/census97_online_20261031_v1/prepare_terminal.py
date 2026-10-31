from pathlib import Path
import json,time,hashlib,re,ast,difflib
B=Path(__file__).resolve().parents[2];S=B/'runtime/census96_prefix_20261031_v1';D=B/'runtime/census97_terminal_20261031_v1';O=B/'runs/census97_fixed96_terminal_20261031_v1';D.mkdir();O.mkdir()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def read(p):return json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
for oldname,newname in [('terminal96.py','terminal97.py'),('wait_terminal96.py','wait_terminal97.py')]:
 old=(S/oldname).read_text();s=re.sub(r'8533|8443|(?<![\d.])(?:95|96)(?!\d)',lambda m:{'8533':'8623','8443':'8533','95':'96','96':'97'}[m[0]],old)
 s=s.replace('os.sched_setaffinity(0,{11})','os.sched_setaffinity(0,{11})')
 assert 'census97_fixed96_terminal_20261031_v1' in s or newname.startswith('wait');ast.parse(s);(D/newname).write_text(s);(D/(newname+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(S/oldname),tofile=str(D/newname))))
oldplan=read(B/'runs/census96_fixed95_terminal_20261031_v1/PLAN.json');newref=B/'runs/census96_new_terminal_diagnosis_20261031_v1';rp=read(newref/'REFERENCE_PLAN.json');methods={};inputs=[]
for m,old in oldplan['methods'].items():
 e=rp['methods'][m];v=newref/'reference96'/(m+'_values.npz');review=newref/'reference96'/(m+'_REVIEW.json');reg=B/f'runs/parameter_census_cycle97_20261031_v1/{m}/REGISTRATION.json'
 methods[m]=dict(terminal_rows=e['terminal_rows'],prediction_block_boundaries=e['prediction_block_boundaries'],parent_steps=read(reg)['post_interruption_continuation']['parent_steps'],parent_sha256=e['checkpoint']['sha256'],baseline_values=str(v),baseline_sha256=sha(v),baseline_review=str(review),registration=str(reg),checkpoint=str(B/f'runs/parameter_census_cycle97_archive_20261031_v1/{m}/cycle_00097.pt'),known_rows=old['known_rows']);inputs.extend([ref(v),ref(review),ref(reg)])
run=B/'runs/parameter_census_cycle97_20261031_v1';runtime=B/'runtime/census97_continuation_20261031_v1';monitor=read(run/'MONITOR_LAUNCH.json');launch=read(run/'LAUNCH.json');inputs.extend([ref(newref/'reference96/REVIEW.json'),ref(newref/'DIAGNOSIS.json'),ref(runtime/'SOURCES.json'),ref(runtime/'SCIENTIFIC_DECISION.json')]);p=dict(time=time.time(),methods=methods,inputs=inputs,source_hashes={n:sha(D/n) for n in ['terminal97.py','wait_terminal97.py']},runtime_hashes=read(runtime/'SOURCES.json')['files'],restore_runtime=str(runtime),run=str(run),complete_review=str(B/'runs/parameter_census_cycle97_review_20261031_v1'),original_monitor=monitor,wait_deadline_unix=min(j['time'] for j in launch['jobs'])+14400,analysis_budget_seconds=1200,baseline_prediction_key='initial_prediction',scope='All8623 full96 terminals,allfive/originalmasks; old<=95/new96, historical aborts and96short0600 retained. Requires full97; no training or independent-generalization claim.',automatic98=False)
put(O/'PLAN.json',p);print(D)
