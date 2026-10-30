from pathlib import Path
import sys,json,time,copy,hashlib,subprocess,os,ast,difflib
D=Path(__file__).parent;B=D.parents[1];OLD=B/'runtime/history88_online_20261030_v1';R=B/'runs/parameter_history_cycle88_20261030_v2';R0=B/'runs/parameter_history_cycle88_20261030_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
import torch
from driver import sha,put,read,validate_actor_rates,validate_protocol
from train_published_compliance_20261025 import registered_stage_actor_rates
torch.set_num_threads(1);p=read(R0/'admittance/REGISTRATION.json');ck=torch.load(p['post_interruption_continuation']['checkpoint']['path'],map_location='cpu',weights_only=False);actual=[g['lr'] for g in ck['learner']['actor_optimizer']['param_groups']];_,expected=registered_stage_actor_rates(p['completed_stage_continuation']);validate_actor_rates(actual,expected);assert actual!=expected and max(abs(a-e) for a,e in zip(actual,expected))<1e-12
rejects=0
for bad in [[float('nan')],[float('inf')],[],[actual[0]+1e-6],[0.]]:
 try:validate_actor_rates(bad,expected)
 except ValueError:rejects+=1
 else:raise AssertionError('Invalid LR accepted')
assert rejects==5;del ck
for name in ['startup88.py','review88.py','archive88.py','loss88.py']:
 s=(D/name).read_text();assert s.replace('parameter_history_cycle88_20261030_v2','parameter_history_cycle88_20261030_v1').replace('parameter_history_cycle88_archive_20261030_v2','parameter_history_cycle88_archive_20261030_v1').replace('parameter_history_cycle88_view_20261030_v2','parameter_history_cycle88_view_20261030_v1').replace('parameter_history_cycle88_review_20261030_v2','parameter_history_cycle88_review_20261030_v1')==(OLD/name).read_text()
for name in ['driver.py','startup88.py','review88.py','archive88.py','loss88.py']:
 (D/(name+'.diff')).write_text(''.join(difflib.unified_diff((OLD/name).read_text().splitlines(True),(D/name).read_text().splitlines(True),fromfile=str(OLD/name),tofile=str(D/name))))
p['post_interruption_continuation']['driver_sha256']=sha(D/'driver.py');validate_protocol(p['post_interruption_continuation']['parent_registration']['sha256'],p);put(R/'admittance/REGISTRATION.json',p)
j=next(x for x in read(R0/'COMMANDS.json')['jobs'] if x['controller']=='admittance');j=copy.deepcopy(j);j['command'][1]=str(D/'driver.py')
for flag,value in [('--registration',R/'admittance/REGISTRATION.json'),('--output',R/'admittance/train')]:j['command'][j['command'].index(flag)+1]=str(value)
put(R/'RETRY_COMMAND.json',j);put(D/'LR_RETRY_CONTRACT_REVIEW.json',dict(passed=True,time=time.time(),actual_actor_lr=actual,expected_computed_lr=expected,differences=[a-e for a,e in zip(actual,expected)],unchanged_optimizer_settings=True,negative_rejections=rejects,consumer_paths_only_changed=True,new_physics=0,old_admittance_zero_physics=True,original_I_V_not_restarted=True))
for f in D.glob('*.py'):ast.parse(f.read_text())
put(D/'SOURCES.json',dict(time=time.time(),files={f.name:sha(f) for f in D.glob('*.py')}))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (R/'admittance/check_only.log').open('x') as f:subprocess.run(j['command']+['--check-only'],check=True,stdout=f,stderr=subprocess.STDOUT,env=env)
assert read(R/'admittance/CHECK_ONLY_REVIEW.json')['passed'];print('Only zero-physics A retry ready; original I/V live')
