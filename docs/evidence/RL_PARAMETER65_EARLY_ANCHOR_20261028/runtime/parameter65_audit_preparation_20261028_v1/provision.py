from pathlib import Path
import ast,re,json,hashlib,difflib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');HERE=Path(__file__).parent;run=B/'runs/parameter_capacity_pool30_cycle65_20261026_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def transform(s,m):
 rx=re.compile(r'(?<!\d)('+ '|'.join(m)+r')(?!\d)')
 return ''.join(x if re.fullmatch(r'[a-f0-9]{64}',x) else rx.sub(lambda a:m[a[0]],x) for x in re.split(r'([a-f0-9]{64})',s))
def adapt(source,dest,m,fix=None):
 old=source.read_text();new=transform(old,m);assert transform(new,{v:k for k,v in m.items()})==old
 if fix:new=fix(new)
 ast.parse(new);assert old.count('ky26288')==new.count('ky26288');assert re.findall(r'2026\d{4}',old)==re.findall(r'2026\d{4}',new)
 dest.write_text(new);dest.with_suffix('.py.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(source),tofile=str(dest))))
 return dict(source=ref(source),output=ref(dest),inverse_exact_before_explicit_adjustment=True,ast_passed=True)
# Terminal65: all1944 rows at complete64, expected1974 at complete65.
old=B/'runs/vmc64_terminal_anchor_followup_20261028_v1';out=B/'runs/vmc65_terminal_anchor_followup_20261028_v1';out.mkdir();m={'00063':'00064','00064':'00065','63':'64','64':'65','1914':'1944','1944':'1974'};rows=[]
for name in ['capture_anchor.py','review_anchor.py','track.py','review_values.py','wait.py']:
 fix=None
 if name=='capture_anchor.py':
  def fix(s):
   oldhash='46c3f151864b9e028e747ab5e7a9c84b695ae493f16674eb394e499d5b2b22a6';newhash='c39302451cc0f7fff54f7fc3988812fe48086fb2a813f2f260111f5981953c66';assert s.count(oldhash)==1;return s.replace(oldhash,newhash)
 rows.append(adapt(old/name,out/name,m,fix))
write(out/'SOURCE_REVIEW.json',dict(time=time.time(),passed=True,files=rows,mapping=m,dates_owner_and_hashes_protected=True,explicit_parent_checkpoint_sha256='c39302451cc0f7fff54f7fc3988812fe48086fb2a813f2f260111f5981953c66',no_scientific_change=True))
# Fixed prefix: protect the historical scope text while advancing current cycle.
old=B/'runs/parameter64_first5000_20261028_v1';out=B/'runs/parameter65_first5000_20261028_v1';out.mkdir();rows=[]
for name in ['audit.py','review_saved.py']:
 s=(old/name).read_text()
 if name=='audit.py':
  match=re.search(r"scope='([^']*)'",s);scope=match[1];masked=s.replace(scope,'__HISTORICAL_SCOPE__');new=transform(masked,{'64':'65'});assert transform(new,{'65':'64'})==masked
  new=new.replace('__HISTORICAL_SCOPE__','Descriptive first5000 of65, registered after training launch and prefix availability. Same original5000 length; all prior53-55/56-58/59-61/62-64 results retained; ongoing65-67 original plan unchanged.')
  ast.parse(new);(out/name).write_text(new);(out/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile=str(old/name),tofile=str(out/name))))
  rows.append(dict(source=ref(old/name),output=ref(out/name),inverse_current_cycle_with_scope_protected=True))
 else:rows.append(adapt(old/name,out/name,{'64':'65'}))
write(out/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=rows,prefix_length_and_formula_unchanged=True,historical_scope_explicitly_preserved=True))
p=readplan=json.loads((old/'PLAN.json').read_text());p.update(time=time.time(),cycle=65,registration={m:ref(run/m/'REGISTRATION.json') for m in p['methods']},source_sha256=sha(out/'audit.py'),parent_source_sha256=sha(old/'audit.py'));write(out/'PLAN.json',p)
# Full labels: unchanged generic auditor, advance waiter only.
old=B/'runtime/parameter_task_label_audit64_20261028_v1';out=B/'runtime/parameter_task_label_audit65_20261028_v1';out.mkdir();result=B/'runs/parameter_task_label_audit65_20261028_v1';result.mkdir();(out/'audit_labels.py').write_bytes((old/'audit_labels.py').read_bytes());row=adapt(old/'wait64.py',out/'wait65.py',{'63':'64','64':'65'});write(out/'SOURCE_REVIEW.json',dict(passed=True,auditor_unchanged=True,auditor_sha256=sha(out/'audit_labels.py'),waiter=row))
# Bounded next-stage check-only preparation; retain verified buffered-copy implementation.
old=B/'runtime/prepare_parameter65_20261028_v1';out=B/'runtime/prepare_parameter66_20261028_v1';out.mkdir();m={'00064':'00065','00065':'00066','64':'65','65':'66'};rows=[]
for source,target in [('prepare_parameter65.py','prepare_parameter66.py'),('launch_parameter65.py','launch_parameter66.py'),('startup65.py','startup66.py'),('wait_prepare.py','wait_prepare.py')]:rows.append(adapt(old/source,out/target,m))
assert 'copy_function=verified_copy' in (out/'prepare_parameter66.py').read_text() and 'shutil.copyfile(' not in (out/'launch_parameter66.py').read_text()
write(out/'SOURCE_REVIEW.json',dict(time=time.time(),passed=True,files=rows,mapping=m,verified_buffered_copy_unchanged=True,scientific_config_unchanged=True,automatic_training=False))
write(out/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,files={n:sha(out/n) for n in ['launch_parameter66.py','startup66.py']}))
write(HERE/'SOURCE_PROVISION_REVIEW.json',dict(time=time.time(),passed=True,terminal_anchor_rows=1944,expected_complete65_rows=1974,prefix_rows=5000,labels_auditor_unchanged=True,next_stage=66,automatic_training=False))
print('65 prefix/terminal/label and66 restore sources prepared; no job launched by this script')
