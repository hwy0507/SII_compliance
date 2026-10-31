from pathlib import Path
import ast,tokenize,io,re,json,time,hashlib,difflib
P=Path(__file__).resolve().parent;B=P.parents[1];N=B/'runtime/census100_new_terminal_diagnosis_20261031_v1';C=B/'runtime/census100_completion_20261031_v1';N.mkdir();C.mkdir();(B/'runs/census100_new_terminal_diagnosis_20261031_v1').mkdir()
mp={'98':'99','99':'100','100':'101','00098':'00099','00099':'00100','8803':'8893','8893':'8983'}
def label(s):
 if 'parameter_census97_99_reward_stability' in s:return s
 if re.search('[a-f0-9]{64}',s):return s
 return re.sub(r'(?<!\d)(00098|00099|8803|8893|98|99|100)(?!\d)',lambda m:mp[m[0]],s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
rows=[]
for oldroot,newroot,names in [(B/'runtime/census99_new_terminal_diagnosis_20261031_v1',N,['register.py','wait_diagnosis.py','build_reference99.py','analyze.py','review_saved.py','fixed_report_contract.py','check_report_contract.py']),(B/'runtime/census99_completion_20261031_v1',C,['check_full_context99.py','review_saved99.py','consolidate99.py','wait_checks.py'])]:
 for name in names:
  f=oldroot/name;source=f.read_text();ts=[]
  for t in tokenize.generate_tokens(io.StringIO(source).readline):
   v=t.string
   if t.type==tokenize.NUMBER and v in mp:v=mp[v]
   elif t.type in (tokenize.NAME,tokenize.STRING,tokenize.COMMENT,tokenize.FSTRING_MIDDLE):v=label(v)
   ts.append(t._replace(string=v))
  s=tokenize.untokenize(ts)
  if name=='check_report_contract.py':s=s.replace('census99_fixed97_terminal','census99_fixed98_terminal')
  if name=='wait_checks.py':s=s.replace('original97_99_audit_pending=True','original97_99_complete_failed=True,prospective100_102_audit_pending=True')
  if name=='consolidate99.py':
   s=s.replace("B / 'runtime/census97_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json'","B / 'runtime/census100_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json',\n          B / 'runs/parameter_census97_99_reward_stability_20261031_v1/REVIEW.json'")
   s=s.replace('original97–100 still requires its final bound audit','original97–99 complete failure retained and prospective100–102 still requires all three finite stages and final bound audit')
  ast.parse(s);out=newroot/label(name);out.write_text(s);(P/(newroot.name+'_'+out.name+'.diff')).write_text(''.join(difflib.unified_diff(source.splitlines(True),s.splitlines(True),fromfile=str(f),tofile=str(out))))
  aa=[t.string for t in tokenize.generate_tokens(io.StringIO(source).readline) if t.type==tokenize.NUMBER];bb=[t.string for t in tokenize.generate_tokens(io.StringIO(s).readline) if t.type==tokenize.NUMBER];assert [mp.get(v,v) for v in aa]==bb
  rows.append(dict(parent=ref(f),candidate=ref(out),nonstage_numeric_tokens_unchanged=True))
assert (N/'fixed_report_contract.py').read_bytes()==(B/'runtime/census99_new_terminal_diagnosis_20261031_v1/fixed_report_contract.py').read_bytes()
put(P/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=rows,fixed_report_contract_byte_exact=True,scope='Stage labels and terminal counts only; historical97 binding repair and original97 helper preserved; original97-99 failed window explicitly retained, prospective100-102 remains incomplete. No training or inference.'))
helper=B/'runtime/census97_boundary_review_20261031_v1'
put(C/'CONTEXT_PLAN.json',dict(time=time.time(),source_sha256=sha(C/'check_full_context100.py'),helper_sha256=sha(helper/'check_continuity.py'),complete_cycle=100,expected_terminal_rows_per_method=30,physics_steps=0,optimizer_updates=0))
R=B/'runs/parameter_census_cycle100_20261031_v1';rd=lambda p:json.loads(p.read_text());sources=list(C.glob('*.py'))+[C/'CONTEXT_PLAN.json',P/'SOURCE_REVIEW.json',helper/'check_continuity.py',helper/'CONTINUITY_REVIEW.json']
put(C/'WAIT_PLAN.json',dict(time=time.time(),sources={str(p):sha(p) for p in sources},original_monitor=rd(R/'MONITOR_LAUNCH.json'),deadline=min(j['time'] for j in rd(R/'LAUNCH.json')['jobs'])+14400,analysis_budget_seconds=1800,new_physics=0,optimizer_updates=0,automatic_training=False,scope='Only complete100 all-row context and all-loss saved arithmetic; original core must finish first. Actual plot inspection and consolidation separate; no101 dispatch.'))
print('Prepared100 terminal/full-context/full-loss sources')
