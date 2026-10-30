from pathlib import Path
import ast,re,json,time,hashlib,difflib,subprocess
B=Path(__file__).resolve().parent.parent;OLD=B/'runtime/violation91_terminal_followup_20261030_v1';D=B/'runtime/violation92_terminal_followup_20261030_v1';O=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';D.mkdir();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for src,dest in [('register.py','register.py'),('compare91.py','compare92.py'),('check91_v2.py','check92.py'),('wait91.py','wait92.py'),('launch.py','launch.py'),('observe.py','observe.py')]:
 before=(OLD/src).read_text();s=before
 mapping={'violation91_fixed87_terminal_followup_':'violation92_fixed87_terminal_followup_','violation90_fixed87_terminal_followup_':'violation91_fixed87_terminal_followup_','parameter_violation_cycle91_':'parameter_violation_cycle92_','violation91_continuation_':'violation92_continuation_','cycle_00091.pt':'cycle_00092.pt','compare91':'compare92','wait91.py':'wait92.py','validate_architecture91':'validate_architecture92','validate_recovery91':'validate_recovery92','automatic92':'automatic93','incomplete91':'incomplete92','complete91_validation':'complete92_validation','partial91':'partial92','complete91 before':'complete92 before','complete91.':'complete92.','Full91':'Full92','target_cycle=91':'target_cycle=92','parent_cycle=90,target_cycle=92':'parent_cycle=91,target_cycle=92'}
 s=re.sub('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))),lambda m:mapping[m[0]],s)
 s=re.sub(r"(\['(?:cycle|parent_cycle|new_cycle)'\]\s*==\s*)(90|91)\b",lambda m:m[1]+str(int(m[2])+1),s)
 if src=='register.py':s=s.replace('Descriptive87/88/89/90/91 retention','Descriptive87/88/89/90/91/92 retention')
 if src=='check91_v2.py':s=s.replace('cycle=90','cycle=91').replace('actual_missing_complete91','actual_missing_complete92').replace('future complete91','future complete92').replace('partial unexpectedly complete','partial unexpectedly complete')
 if src=='compare91.py':
  s=s.replace('across87/88/89/90/91;','across87/88/89/90/91/92;')
  a="assert prior['checkpoint_sha256']==st['checkpoint']['sha256'] and b['rows']+prior['new_transitions']==prior['steps']"
  b="previous_protocol=read(st['parent_registration']['path']);assert sha(st['parent_registration']['path'])==st['parent_registration']['sha256']\n parent_review=read(previous_protocol['post_interruption_continuation']['cycle_review']['path'])['methods'][b['method']]\n assert prior['checkpoint_sha256']==st['checkpoint']['sha256'] and parent_review['steps']+prior['new_transitions']==prior['steps']"
  assert s.count(a)==1;s=s.replace(a,b)
  # Preserve all five earlier endpoints and the saved52 inputs, then append92.
  s=s.replace("'observations51','actions'","'observations51','observations52','actions'")
  s=s.replace("'complete89','complete90']","'complete89','complete90','complete91']")
  s=s.replace("old['observations52']=np.column_stack((old['observations51'],bit.astype(np.float32)));", "np.testing.assert_array_equal(old['observations52'],np.column_stack((old['observations51'],bit.astype(np.float32))));")
  s=s.replace('original87_88_89_90_saved_arithmetic_exact','original87_88_89_90_91_saved_arithmetic_exact').replace('actual_missing_complete91_rejected','actual_missing_complete92_rejected')
  s=s.replace('complete91=pred','complete92=pred')
  s=s.replace("'complete89','complete90','complete91']:statistics", "'complete89','complete90','complete91','complete92']:statistics")
  s=s.replace("[(-.32,'initial_control'),(-.16,'complete88'),(0,'complete89'),(.16,'complete90'),(.32,'complete91')]", "[(-.325,'initial_control'),(-.195,'complete88'),(-.065,'complete89'),(.065,'complete90'),(.195,'complete91'),(.325,'complete92')]").replace('width=.16','width=.13')
  s=s.replace("complete91_minus90_masked_sse=(np.array(statistics['complete91']['masked_sse'])-statistics['complete90']['masked_sse'])", "complete92_minus91_masked_sse=(np.array(statistics['complete92']['masked_sse'])-statistics['complete91']['masked_sse'])")
  s=s.replace("complete91_minus87_masked_sse=(np.array(statistics['complete91']['masked_sse'])", "complete92_minus87_masked_sse=(np.array(statistics['complete92']['masked_sse'])")
  s=s.replace('fixed87_terminal_87_88_89_90_91.png','fixed87_terminal_87_88_89_90_91_92.png')
 if src=='launch.py':
  a="fix=read(D/'CHECK91_FAILURE_AND_FIX.json');assert sha(Path(fix['replacement_source']))==fix['replacement_sha256'] and sha(Path(fix['original_source']))==fix['original_sha256']"
  assert s.count(a)==1;s=s.replace(a,"assert read(D/'SOURCE_REVIEW.json')['passed'];assert sha(D/'check92.py')==plan['source_hashes']['check92.py']")
  s=s.replace("fix['replacement_sha256']","sha(D/'check92.py')")
 ast.parse(s);(D/dest).write_text(s);(D/(dest+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile=str(OLD/src),tofile=dest)))
# Fixed first5000, selected before reading current loss values.
old=B/'runtime/violation91_prefix_20261030_v1/prefix91.py';s=old.read_text();before=s
s=s.replace('parameter_violation_cycle91_','parameter_violation_cycle92_').replace('parameter_violation_cycle90_review_','parameter_violation_cycle91_review_').replace('cycle91','cycle92').replace('Cycle91','Cycle92').replace('complete90_last1000','complete91_last1000').replace('Complete90 losses','Complete91 losses');ast.parse(s);(D/'prefix92.py').write_text(s);(D/'prefix92.py.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile=str(old),tofile='prefix92.py')))
repo=B/'repository/SII_compliance';remote={n:subprocess.check_output(['git','rev-parse','origin/'+n],cwd=repo,text=True).strip() for n in ('main','baseline')}
(D/'PREFIX_PLAN.json').write_text(json.dumps(dict(time=time.time(),scope='Fixed first5000 per method inherited from91; selected before reading92 losses; no new physics/update',source_sha256=sha(D/'prefix92.py'),parent_script=str(old),parent_sha256=sha(old),actual_parent_review=str(B/'runs/parameter_violation_cycle91_review_20261030_v1/REVIEW.json'),formal_updates=0,physics_steps=0,convergence_claim=False,remote=remote),indent=2)+'\n')
(D/'REMOTE_START.json').write_text(json.dumps(dict(time=time.time(),actual_query_fetch_read=True,**remote),indent=2)+'\n')
print('Prepared fixed87 followup92 and fixed first5000 loss review; no launch')
