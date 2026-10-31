from pathlib import Path
import re,tokenize,io,ast,difflib,json,hashlib,time
B=Path(__file__).resolve().parents[2];OLD=B/'runtime/census96_continuation_20261031_v1';D=B/'runtime/census97_continuation_20261031_v1';R=B/'runs/parameter_census_cycle97_20261031_v1';D.mkdir();R.mkdir()
def advance(s):
 # Advance cycle identifiers only, never numeric decimals, hashes, or unrelated modules.
 def sub(t):return re.sub(r'00095|00096|(?<![\d.])(?:95|96)(?!\d)',lambda m:{'00095':'00096','00096':'00097','95':'96','96':'97'}[m[0]],t)
 out=[]
 for t in tokenize.generate_tokens(io.StringIO(s).readline):
  if t.type==tokenize.NUMBER and t.string in ('95','96'):t=t._replace(string=str(int(t.string)+1))
  elif t.type in (tokenize.STRING,tokenize.NAME,tokenize.COMMENT):t=t._replace(string=sub(t.string))
  out.append(t)
 return tokenize.untokenize(out)
# Only stage orchestration/consumers move. All numerical learner/census/capacity modules stay byte exact.
stages={'driver.py','check_contract.py','check_cpu_consumer.py','run_preflight.py','launch96.py','startup96.py','archive96.py','review96.py','health96.py','loss96.py','observe96.py'}
for p in OLD.glob('*.py'):
 if p.name in ('prepare.py','check_window_protocol.py'):continue
 s=p.read_text();name=p.name
 if name in stages:
  s=advance(s);name=name.replace('96','97')
  # Original96 consumer failure was fixed independently; use the verified gamma here.
  if name in ('startup97.py','review97.py'):s=s.replace('gamma=.9996','gamma=.9995')
 (D/name).write_text(s)
(D/'parameter_replay_capacity6m.py').write_bytes((B/'runtime/census_capacity6m_preparation_20261031_v1/parameter_replay_capacity6m.py').read_bytes())
p=D/'driver.py';s=p.read_text()
def replace(a,b,count=1):
 global s
 assert s.count(a)==count,(a,s.count(a));s=s.replace(a,b)
replace("changes=[('Finite96 new-transition budget exceeded','Finite97 new-transition budget exceeded')]", """changes=[('Finite96 new-transition budget exceeded','Finite97 new-transition budget exceeded'),
 ('        conditional_terminal_amendment=protocol[\'conditional_terminal_amendment\'],\\n', '        conditional_terminal_amendment=protocol[\'conditional_terminal_amendment\'],\\n        replay_capacity_third_stage=protocol[\'replay_capacity_third_stage\'],\\n')]
 # Add the stage to both execution and checkpoint metadata using exact whole lines.
 changes=changes[:1]+[(\"\\n\"+' '*indent+\"conditional_terminal_amendment=protocol['conditional_terminal_amendment'],\",\"\\n\"+' '*indent+\"conditional_terminal_amendment=protocol['conditional_terminal_amendment'],\\n\"+' '*indent+\"replay_capacity_third_stage=protocol['replay_capacity_third_stage'],\") for indent in (8,12)]""")
# Replace the temporary list above by simpler syntax to avoid embedded quoting ambiguity.
a=s.index(' changes=');z=s.index(' for a,b in changes:',a)
s=s[:a]+''' changes=[('Finite96 new-transition budget exceeded','Finite97 new-transition budget exceeded')]
 for indent in (8,12):
  old="\\n"+' '*indent+"conditional_terminal_amendment=protocol['conditional_terminal_amendment'],"
  new=old+"\\n"+' '*indent+"replay_capacity_third_stage=protocol['replay_capacity_third_stage'],"
  changes.append((old,new))
'''+s[z:]
replace("return dict(parent,post_interruption_continuation=stage)","""from parameter_replay_capacity6m import MARKER
 cap=dict(version=1,parent_cycle=96,first_cycle=97,marker=MARKER,entry_checkpoint=e['checkpoint'],parent_stripped_replay_digest=e['stripped_replay_digest'],source=ref(D/'parameter_replay_capacity6m.py'),old_rows_preserved=True)
 return dict(parent,post_interruption_continuation=stage,replay_capacity_third_stage=cap)""")
replace("ck['steps']+41250>4000000","ck['steps']+41250>6000000")
replace(" from census_native import KEY,marker\n from validate_published_finite_check_20261025 import digest\n st=p['post_interruption_continuation'];h=", " from census_native import KEY,marker\n from parameter_replay_capacity6m import KEY as CK,MARKER as CAP6\n from validate_published_finite_check_20261025 import digest\n st=p['post_interruption_continuation'];h=")
replace("if r['capacity']!=4000000", "if r.get(CK)!=CAP6 or ck.get('replay_capacity_third_stage')!=p['replay_capacity_third_stage'] or r['capacity']!=6000000")
replace("base,replay=old_classes(p);return census_class(base),replay", """from train_published_compliance_20261025 import Replay
 from parameter_replay_capacity6m import replay_class
 from persisted_violation_critic import violation_replay_class
 base,_=old_classes(p);cap=p['replay_capacity_third_stage'];wrapped=violation_replay_class(replay_class(Replay,cap['parent_stripped_replay_digest']),p['violation_critic_amendment']['binding'])
 class Replay6m(wrapped):
  def __init__(self,dimension,observation_dim,seed,capacity=6000000):
   if capacity!=6000000:raise ValueError('Explicit6m required')
   super().__init__(dimension,observation_dim,seed,capacity=6000000)
 return census_class(base),Replay6m""")
replace("def verify_initial(learner,replay,ck,out):", """def expected_replay(state):
 from parameter_replay_capacity6m import KEY,MARKER
 return dict(state,capacity=6000000,**{KEY:MARKER})

def verify_initial(learner,replay,ck,out):""")
replace("digest(replay.state_dict())==digest(ck['replay'])", "digest(replay.state_dict())==digest(expected_replay(ck['replay']))")
replace("full_trained96_learner_and_replay_exact=True", "full_trained96_learner_and_replay_exact=True,capacity_only_migration=True,expanded_replay_digest=digest(replay.state_dict())")
replace("digest(r.state_dict())==digest(ck['replay'])", "digest(r.state_dict())==digest(expected_replay(ck['replay']))")
p.write_text(s)
# Both consumers must enforce all three capacity markers and preserve old4m parent.
for name in ['startup97.py','review97.py']:
 p=D/name;s=p.read_text();s=s.replace('from parameter_replay_capacity4m_20261027 import MARKER as FOLLOWUP_MARKER','from parameter_replay_capacity4m_20261027 import MARKER as FOLLOWUP_MARKER\nfrom parameter_replay_capacity6m import MARKER as THIRD_MARKER, KEY as THIRD_KEY')
 s=s.replace("x['replay']['capacity']==4_000_000", "x['replay']['capacity']==6_000_000 and x['replay'][THIRD_KEY]==THIRD_MARKER and x['replay_capacity_third_stage']==json.loads((run.parent/'REGISTRATION.json').read_text())['replay_capacity_third_stage']")
 s=s.replace('current_replay_capacity=4_000_000','current_replay_capacity=6_000_000,replay_capacity_third=THIRD_MARKER')
 if name=='review97.py':s=s.replace("crossed_original_capacity=True,", "crossed_original_capacity=True,crossed_third_capacity=x['steps']>4_000_000,rows_beyond_third_capacity=max(0,x['steps']-4_000_000),")
 p.write_text(s)
# Add capacity contract negatives while retaining the previous37 per method.
p=D/'check_contract.py';s=p.read_text();s=s.replace("('new_cycle',97)","('new_cycle',98)")
s=s.replace(" assert len(rejections)==37", """ for key in ('marker','parent_stripped_replay_digest','entry_checkpoint'):
  bad=copy.deepcopy(p);bad['replay_capacity_third_stage'][key]={};reject('third_capacity_'+key,lambda:validate_protocol(parent,bad))
 assert len(rejections)==40""");p.write_text(s)
p=D/'launch97.py';s=p.read_text().replace('==111','==120').replace('negative_rejections=111','negative_rejections=120');p.write_text(s)
# Save exact deltas; no stage can run until separate decision/registration/checks exist.
for name in stages:
 target=name.replace('96','97');new=(D/target).read_text();ast.parse(new);(D/(target+'.diff')).write_text(''.join(difflib.unified_diff((OLD/name).read_text().splitlines(True),new.splitlines(True),fromfile=str(OLD/name),tofile=str(D/target))))
for p in D.glob('*.py'):ast.parse(p.read_text())
print(D)
