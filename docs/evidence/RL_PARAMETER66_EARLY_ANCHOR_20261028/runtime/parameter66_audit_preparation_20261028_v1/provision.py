from pathlib import Path
import ast,re,json,hashlib,difflib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');HERE=Path(__file__).parent;run=B/'runs/parameter_capacity_pool30_cycle66_20261026_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):
 with p.open('x') as f:f.write(json.dumps(d,indent=2)+'\n')
def transform(s,m):
 rx=re.compile(r'(?<!\d)('+ '|'.join(m)+r')(?!\d)')
 return ''.join(x if re.fullmatch(r'[a-f0-9]{64}',x) else rx.sub(lambda a:m[a[0]],x) for x in re.split(r'([a-f0-9]{64})',s))
def adapt(source,dest,m,fix=None):
 old=source.read_text();new=transform(old,m);assert transform(new,{v:k for k,v in m.items()})==old
 if fix:new=fix(new)
 ast.parse(new);assert old.count('ky26288')==new.count('ky26288');assert re.findall(r'2026\d{4}',old)==re.findall(r'2026\d{4}',new)
 with dest.open('x') as f:f.write(new)
 dest.with_suffix('.py.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(source),tofile=str(dest))))
 return dict(source=ref(source),output=ref(dest),inverse_exact_before_explicit_adjustment=True,ast_passed=True)
# Complete65 all1974 fixed terminal inputs, expected2004 after66.
old=B/'runs/vmc65_terminal_anchor_followup_20261028_v1';out=B/'runs/vmc66_terminal_anchor_followup_20261028_v1';out.mkdir();m={'00064':'00065','00065':'00066','64':'65','65':'66','1944':'1974','1974':'2004'};rows=[]
for name in ['capture_anchor.py','review_anchor.py','track.py','review_values.py','wait.py']:
 fix=None
 if name=='capture_anchor.py':
  def fix(s):
   a='c39302451cc0f7fff54f7fc3988812fe48086fb2a813f2f260111f5981953c66';c='1d72af6620ce15dad2cb2996ddae9e9f293a16189d1d91cba8807e79abf34fc2';assert s.count(a)==1;return s.replace(a,c)
 rows.append(adapt(old/name,out/name,m,fix))
write(out/'SOURCE_REVIEW.json',dict(time=time.time(),passed=True,files=rows,mapping=m,dates_owner_and_hashes_protected=True,explicit_parent_checkpoint_sha256='1d72af6620ce15dad2cb2996ddae9e9f293a16189d1d91cba8807e79abf34fc2',no_scientific_change=True))
# Fixed first5000 with explicitly protected historical scope.
old=B/'runs/parameter65_first5000_20261028_v1';out=B/'runs/parameter66_first5000_20261028_v1';out.mkdir();rows=[]
for name in ['audit.py','review_saved.py']:
 s=(old/name).read_text()
 if name=='audit.py':
  scope=re.search(r"scope='([^']*)'",s)[1];masked=s.replace(scope,'__HISTORICAL_SCOPE__');new=transform(masked,{'65':'66'});assert transform(new,{'66':'65'})==masked
  new=new.replace('__HISTORICAL_SCOPE__','Descriptive first5000 of66, registered after training launch and prefix availability. Same original5000 length; all prior53-55/56-58/59-61/62-64 results retained; ongoing65-67 original plan unchanged.')
  ast.parse(new);(out/name).write_text(new);(out/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile=str(old/name),tofile=str(out/name))));rows.append(dict(source=ref(old/name),output=ref(out/name),inverse_current_cycle_with_scope_protected=True))
 else:rows.append(adapt(old/name,out/name,{'65':'66'}))
write(out/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=rows,prefix_length_and_formula_unchanged=True,historical_scope_explicitly_preserved=True))
p=json.loads((old/'PLAN.json').read_text());p.update(time=time.time(),cycle=66,registration={m:ref(run/m/'REGISTRATION.json') for m in p['methods']},source_sha256=sha(out/'audit.py'),parent_source_sha256=sha(old/'audit.py'));write(out/'PLAN.json',p)
# Unchanged all-label auditor; only advance cycle waiter.
old=B/'runtime/parameter_task_label_audit65_20261028_v1';out=B/'runtime/parameter_task_label_audit66_20261028_v1';out.mkdir();result=B/'runs/parameter_task_label_audit66_20261028_v1';result.mkdir();(out/'audit_labels.py').write_bytes((old/'audit_labels.py').read_bytes());row=adapt(old/'wait65.py',out/'wait66.py',{'64':'65','65':'66'});write(out/'SOURCE_REVIEW.json',dict(passed=True,auditor_unchanged=True,auditor_sha256=sha(out/'audit_labels.py'),waiter=row))
# Next67 only restore preparation; buffered verified copies retained.
old=B/'runtime/prepare_parameter66_20261028_v1';out=B/'runtime/prepare_parameter67_20261028_v1';out.mkdir();m={'00065':'00066','00066':'00067','65':'66','66':'67'};rows=[]
for source,target in [('prepare_parameter66.py','prepare_parameter67.py'),('launch_parameter66.py','launch_parameter67.py'),('startup66.py','startup67.py'),('wait_prepare.py','wait_prepare.py')]:rows.append(adapt(old/source,out/target,m))
assert 'copy_function=verified_copy' in (out/'prepare_parameter67.py').read_text() and 'shutil.copyfile(' not in (out/'launch_parameter67.py').read_text()
write(out/'SOURCE_REVIEW.json',dict(time=time.time(),passed=True,files=rows,mapping=m,verified_buffered_copy_unchanged=True,scientific_config_unchanged=True,automatic_training=False));write(out/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,files={n:sha(out/n) for n in ['launch_parameter67.py','startup67.py']}))
write(HERE/'SOURCE_PROVISION_REVIEW.json',dict(time=time.time(),passed=True,terminal_anchor_rows=1974,expected_complete66_rows=2004,prefix_rows=5000,labels_auditor_unchanged=True,next_stage=67,automatic_training=False))
print('66 prefix/terminal/labels and67 restore sources prepared; no job launched')
