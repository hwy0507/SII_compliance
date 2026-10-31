from pathlib import Path
import json,hashlib,time,ast,difflib,sys,copy
B=Path(__file__).resolve().parents[2];S=B/'runs/parameter_census94_96_reward_stability_20261031_v1';D=B/'runs/parameter_census97_99_reward_stability_20261031_v1';T=B/'runtime/census97_continuation_20261031_v1';R=B/'runs/parameter_census_cycle97_20261031_v1';D.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
read=lambda p:json.loads(p.read_text())
def identity(s):return s.replace('[94,95,96]','[97,98,99]').replace('[94, 95, 96]','[97, 98, 99]').replace('protocol94','protocol97').replace('c==94','c==97').replace('paired94_to96','paired97_to99').replace('94-96','97-99')
for name in ['audit.py','review_saved.py','bind_inputs.py','binding_rules.py']:
 old=(S/name).read_text();new=identity(old)
 if name=='audit.py':
  new=new.replace('intent recorded after94 launch but before its first complete episode outcome.','intent recorded before97 launch.').replace('First94 protocol','First97 protocol').replace('Capacity4m and historical23/47 markers preserved.','Capacity6m, original2m/4m markers and explicit96-to97 third capacity stage preserved. Original94-96 failed window retained separately.')
 if name=='binding_rules.py':
  new=new.replace("for group in ['protocol97','anchor_protocol55']:","check_ref(p['previous94_96_failed_report'])\n for group in ['protocol97','anchor_protocol55']:")
  new=new.replace(" if st['optimizer_settings_changed'] is not False:"," if p.get('replay_capacity_third_stage')!=plan['third_capacity_stage'][m]:raise ValueError('Third capacity stage changed')\n if st['optimizer_settings_changed'] is not False:")
  new=new.replace("followup_marker=plan['followup_marker'])","followup_marker=plan['followup_marker'],third_capacity_stage=plan['third_capacity_stage'],previous94_96_failed_report=plan['previous94_96_failed_report'])")
  new=new.replace("ck['replay']['capacity']!=4000000","ck['replay']['capacity']!=6000000")
  new=new.replace("    if any(ck['replay']['arrays'][k].shape", "    if ck.get('replay_capacity_third_stage')!=plan['third_capacity_stage'][m] or ck['replay'].get('replay_capacity_third')!=plan['third_capacity_stage'][m]['marker']:raise ValueError('Saved third capacity marker missing')\n    if any(ck['replay']['arrays'][k].shape")
 if name=='bind_inputs.py':new=new.replace("automatic_training=False)","automatic_training=False,third_capacity_stage=p['third_capacity_stage'],previous94_96_failed_report=p['previous94_96_failed_report'])")
 ast.parse(new);(D/name).write_text(new);(D/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(S/name),tofile=str(D/name))))
p=read(S/'PLAN.json');p.update(time=time.time(),cycles=[97,98,99],intent=ref(T/'STABILITY_WINDOW_INTENT.json'),source_sha256=sha(D/'audit.py'),review_source_sha256=sha(D/'review_saved.py'),previous94_96_failed_report=ref(S/'REVIEW.json'),third_capacity_stage=read(T/'STABILITY_WINDOW_INTENT.json')['third_capacity_stage'],protocol97={m:ref(R/m/'REGISTRATION.json') for m in ['impedance','admittance','vmc']});p.pop('protocol94');put(D/'PLAN.json',p);put(D/'SOURCE_LOCK.json',dict(time=time.time(),files={f.name:sha(f) for f in D.iterdir() if f.suffix in ('.py','.json') and f.name!='SOURCE_LOCK.json'}))
sys.path.insert(0,str(D));from binding_rules import locked,protocol,validate_registration
from bind_inputs import build
plan=locked(D);checks={}
for m in plan['protocol97']:
 reg=read(R/m/'REGISTRATION.json');protocol(reg,m,97,plan);bad=copy.deepcopy(reg);bad['replay_capacity_third_stage']['marker']['capacity']=4000000
 try:protocol(bad,m,97,plan)
 except ValueError:checks[m]=True
 else:raise AssertionError('Wrong capacity accepted')
try:validate_registration(D,build({}),check_checkpoints=True)
except ValueError as e:assert str(e)=='All nine complete input groups required'
else:raise AssertionError('Missing cycles accepted')
intent=read(T/'STABILITY_WINDOW_INTENT.json');launch=read(R/'LAUNCH.json');assert intent['time']<min(j['time'] for j in launch['jobs'])
# No arithmetic/statistical expressions changed: exact reverse of identity/report-label edits.
original=(S/'audit.py').read_text();candidate=(D/'audit.py').read_text();restored=candidate.replace('[97, 98, 99]','[94, 95, 96]').replace('paired97_to99','paired94_to96').replace('97-99','94-96').replace('intent recorded before97 launch.','intent recorded after94 launch but before its first complete episode outcome.').replace('First97 protocol','First94 protocol').replace('Capacity6m, original2m/4m markers and explicit96-to97 third capacity stage preserved. Original94-96 failed window retained separately.','Capacity4m and historical23/47 markers preserved.');assert restored==original
put(D/'PREPARATION_REVIEW.json',dict(passed=True,time=time.time(),original_window=ref(S/'REVIEW.json'),prospective_intent_precedes_launch=True,statistical_kernel_byte_exact_after_reversing_only_cycle_identity_and_descriptive_text=True,wrong_capacity_rejected=checks,missing_nine_groups_rejected=True,complete_inputs_bound=False,statistics_performed=False,physics_steps=0,optimizer_updates=0))
print('Prospective97-99 binder prepared; no complete inputs/statistics')
