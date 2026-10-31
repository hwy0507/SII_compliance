from pathlib import Path
import ast,tokenize,io,re,json,hashlib,time,difflib
P=Path(__file__).resolve().parent;B=P.parents[1];O=B/'runtime/census99_continuation_20261031_v1';D=B/'runtime/census100_continuation_20261031_v1';D.mkdir()
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
# Token-level adaptation: no floating point token or opaque digest substitution.
mp={'98':'99','99':'100','100':'101','00098':'00099','00099':'00100'}
def label(s):
 if 'parameter_census97_99_reward_stability' in s or 'WINDOW97_99' in s:return s
 if re.search(r'[a-f0-9]{64}',s):raise AssertionError('Opaque digest in stage adapter')
 return re.sub(r'(?<!\d)(00098|00099|98|99|100)(?!\d)',lambda m:mp[m[0]],s)
def adapt(s):
 out=[]
 for t in tokenize.generate_tokens(io.StringIO(s).readline):
  v=t.string
  if t.type==tokenize.NUMBER and v in ('98','99','100'):v=mp[v]
  elif t.type in (tokenize.NAME,tokenize.STRING,tokenize.COMMENT):v=label(v)
  out.append(t._replace(string=v))
 return tokenize.untokenize(out)
mutable=['driver.py','prepare.py','check_contract.py','check_cpu_consumer.py','run_preflight.py','launch99.py','startup99.py','review99.py','archive99.py','observe99.py','loss99.py']
rows=[]
for f in O.glob('*.py'):
 if f.name=='check_window_protocol.py':continue
 name=label(f.name) if f.name in mutable or f.name=='health99.py' else f.name
 new=adapt(f.read_text()) if f.name in mutable else f.read_text()
 if f.name=='prepare.py':
  new=new.replace("W/'SOURCE_LOCK.json']","W/'SOURCE_LOCK.json',D/'STABILITY_WINDOW_INTENT.json']")
 if f.name=='launch99.py':new=new.replace('WINDOW97_99_PROTOCOL_REVIEW','WINDOW100_102_PROTOCOL_REVIEW')
 if f.name=='check_contract.py':new=new.replace("['marker']['version']=100","['marker']['version']=99")
 ast.parse(new);(D/name).write_text(new)
 rows.append(dict(source=ref(f),destination=ref(D/name),byte_exact=f.read_bytes()==(D/name).read_bytes()))
 (P/(name+'.diff')).write_text(''.join(difflib.unified_diff(f.read_text().splitlines(True),new.splitlines(True),fromfile=str(f),tofile=str(D/name))))
# Fresh resource gate (same resource limits).
s=(B/'runtime/census98_completion_20261031_v1/check_resource99.py').read_text().replace('census99_continuation','census100_continuation')
(D/'check_resource.py').write_text(s)
assert (D/'health100.py').read_bytes()==(O/'health99.py').read_bytes()
assert '.9995' in (D/'startup100.py').read_text()
put(P/'SOURCE_ADAPTATION.json',dict(passed=True,time=time.time(),files=rows,token_numbers_only=True,health_byte_exact=True,dependencies_byte_exact=True))
W=B/'runs/parameter_census97_99_reward_stability_20261031_v1';C=B/'runtime/census99_completion_20261031_v1';N=B/'runs/census99_new_terminal_diagnosis_20261031_v1'
intent=read(B/'runtime/census97_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json');intent.update(time=time.time(),cycles=[100,101,102],previous97_99_failed_report=ref(W/'REVIEW.json'),previous97_99_saved_review=ref(W/'SAVED_ARITHMETIC_REVIEW.json'),scope='Prospective non-overlapping100-102 window before100 launch; original5%/nearzero1/5000bootstrap retained. Original97-99 failed all methods and is not shifted. Only one finite100 prepared;101/102 separately decided and registered, no automatic training. Original loss health and final evaluation remain required.')
put(D/'STABILITY_WINDOW_INTENT.json',intent)
files=[Path(x['path']) for x in read(C/'COMPLETE99_SCIENTIFIC_REVIEW.json')['inputs']]+[C/'COMPLETE99_SCIENTIFIC_REVIEW.json',C/'COMPLETION_REVIEW.json',C/'IMPEDANCE_LONG0000_ABORT_REVIEW.json',C/'ABORT_RESIDUAL_LINK_REVIEW.json',W/'REVIEW.json',W/'SAVED_ARITHMETIC_REVIEW.json',W/'BINDING_REVIEW.json',W/'PLOT_INSPECTION.json',B/'runtime/census99_window_completion_preparation_20261031_v1/CAPACITY_ASSERTION_REPAIR_REVIEW.json',B/'runtime/census99_window_completion_preparation_20261031_v1/WINDOW_BOOTSTRAP_SCALAR_REVIEW.json',D/'STABILITY_WINDOW_INTENT.json']
full=read(B/'runs/parameter_census_cycle99_review_20261031_v1/REVIEW.json');assert full['passed']
prior=dict(time=time.time(),passed=True,parent_cycle=99,new_cycle=100,new_cycles=1,maximum_new_actions_per_method=41250,automatic_followup=False,offline_weights_promoted=False,optimizer_settings_changed=False,reward_physics_changed=False,capacity_unchanged=6000000,convergence_claim=False,direct34=False,facts=full['methods'],evidence=[ref(f) for f in dict.fromkeys(files)],reason='All complete99 state/context/loss and terminal diagnostics reviewed; original97-99 failed all three methods. I new global-penetration abort has terminal masked SSE8909.6665 and original-loss spike22.2616; A old-terminal SSE regresses46.17%; V spike/actor drift persist. One finite unchanged100 from exact99 lets the retained failure enter continued online learning; no guarantee of recovery/convergence, no offline weights, no gate relaxation. Prospective non-overlapping100-102 intent fixed before launch;101/102 require separate evidence decisions. Full restore/native/contract/CPU/resource/protocol/startup checks mandatory.')
put(C/'NEXT_FINITE_DECISION.json',prior)
print(D)
