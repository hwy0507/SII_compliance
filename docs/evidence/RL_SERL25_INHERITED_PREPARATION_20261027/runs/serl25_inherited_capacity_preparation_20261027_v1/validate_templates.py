from pathlib import Path
import ast,copy,hashlib,json,tempfile,textwrap,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');rt=B/'runtime'
out=B/'runs/serl25_inherited_capacity_preparation_20261027_v1';out.mkdir()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=[rt/f'{s}_serl_capacity25{suffix}_20261027.py' for s,suffix in [('prepare',''),('launch',''),('setup','_monitors')]]
templates=rt/'serl_capacity25_monitor_templates_20261027_v1';manifest=json.loads((templates/'MANIFEST.json').read_text())
for name,h in manifest['templates'].items():assert sha(templates/name)==h
for p in files+list(templates.glob('*.py')):ast.parse(p.read_text())
assert "runtime/setup_serl_capacity25_monitors_20261027.py" in files[1].read_text()
setup=files[2].read_text();assert 'cycle24' not in setup and 'capacity24' not in setup and "monitors['boundary']" not in setup
assert set(manifest['templates'])=={'startup_review.py','review.py','coordinator.py','diagnose.py'}
prep=files[0].read_text();assert "stage['parent_cycle']=24" in prep and "p['replay_capacity_stage']['parent_cycle']==23" in prep
assert "oldname='serl_capacity_batch65536_cycle24_20261027_v1'" in prep
assert "name='serl_capacity_batch65536_cycle25_20261027_v1'" in prep
assert '257351' not in prep+files[1].read_text()
assert "len(terminal)==780" in (templates/'diagnose.py').read_text()
helper=B/'repository/SII_compliance/code/mujoco_6d_vmc_benchmark/tools/serl_replay_capacity_20261027.py'
module=ast.parse(helper.read_text());marknode=next(n for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MARKER' for t in n.targets))
marker=eval(compile(ast.Expression(marknode.value),str(helper),'eval'),{'dict':dict})
checks={}
with tempfile.TemporaryDirectory(dir=out) as td:
 root=Path(td);entry=root/'entry23.metadata';entry.write_text('Metadata fixture only, not a model or replay.');parent=root/'parent24.metadata';parent.write_text('Metadata fixture only, not a model or replay.')
 stage=dict(marker=marker,parent_cycle=23,entry_checkpoint=dict(path=str(entry),sha256=sha(entry)))
 parentreg=root/'parent_registration.json';parentreg.write_text(json.dumps(dict(replay_capacity_stage=stage)))
 reg=dict(replay_capacity_stage=copy.deepcopy(stage),resume_parent_registration=dict(path=str(parentreg),sha256=sha(parentreg)),reviewed_continuation_stage=dict(parent_cycle=24,checkpoint=dict(path=str(parent),sha256=sha(parent))))
 old=dict(cycle=24,boundary='complete_condition_cycle',steps=1010000,protocol_sha256=sha(parentreg),replay=dict(capacity=2000000,size=1010000,cursor=1010000,replay_capacity_extension=copy.deepcopy(marker)))
 x=dict(steps=1011000,replay=dict(capacity=2000000,size=1011000,cursor=1011000,replay_capacity_extension=copy.deepcopy(marker)))
 for name in ['startup_review.py','review.py']:
  s=(templates/name).read_text();start=s.index("assert reg['replay_capacity_stage']['marker']==CAPACITY_MARKER");end=s.index('capacity_review=dict',start)
  # Restore first-line indentation before dedenting the exact executed guard block.
  indent=' ' if name=='startup_review.py' else '    '
  block=textwrap.dedent(indent+s[start:end].rstrip())
  compile(block,name,'exec')
  def run(r,o,c):exec(block,dict(reg=r,old=o,x=c,CAPACITY_MARKER=marker,parent=parent,Path=Path,sha=sha,json=json))
  run(copy.deepcopy(reg),copy.deepcopy(old),copy.deepcopy(x))
  mutations=[('wrong_parent_cycle',lambda r,o,c:o.update(cycle=23)),('partial_parent',lambda r,o,c:o.update(boundary='partial')),('legacy_parent_capacity',lambda r,o,c:o['replay'].update(capacity=1000000)),('lost_parent_marker',lambda r,o,c:o['replay'].pop('replay_capacity_extension')),('parent_cursor_mismatch',lambda r,o,c:o['replay'].update(cursor=999999)),('wrong_protocol_hash',lambda r,o,c:o.update(protocol_sha256='bad')),('relabeled_historical_entry',lambda r,o,c:r['replay_capacity_stage'].update(parent_cycle=24)),('changed_parent_reference',lambda r,o,c:r['resume_parent_registration'].update(sha256='bad')),('wrong_current_parent',lambda r,o,c:r['reviewed_continuation_stage'].update(parent_cycle=23)),('wrong_checkpoint_reference',lambda r,o,c:r['reviewed_continuation_stage']['checkpoint'].update(sha256='bad')),('lost_current_marker',lambda r,o,c:c['replay'].pop('replay_capacity_extension')),('current_cursor_mismatch',lambda r,o,c:c['replay'].update(cursor=0))]
  passed=[]
  for label,change in mutations:
   r,o,c=copy.deepcopy(reg),copy.deepcopy(old),copy.deepcopy(x);change(r,o,c)
   try:run(r,o,c)
   except (AssertionError,KeyError):passed.append(label)
   else:raise AssertionError('Accepted invalid metadata: '+label)
  checks[name]=dict(valid_inherited_metadata_passed=True,rejected_mutations=passed)
report=dict(time=time.time(),passed=True,scope='AST, actual launcher/setup/template linkage and extracted inherited-capacity guard metadata fixtures only; not actual24 checkpoint restoration or25 deployment.',checks=checks,source_files=[dict(path=str(p),sha256=sha(p)) for p in files+list(templates.glob('*.py'))],manifest=dict(path=str(templates/'MANIFEST.json'),sha256=sha(templates/'MANIFEST.json')),learner_updates=0,new_physics=0,formal25_launched=False)
(out/'STATIC_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'REGISTRATION.json').write_text(json.dumps(dict(time=time.time(),parent_cycle=24,next_cycle=25,historical_capacity_entry=23,old_capacity=2000000,new_capacity=2000000,original_batch_parent_cycle=12,expected_full_health_terminals=780,automatic_training=False,waiter_started=False,actual_parent24_not_yet_available=True,scope='Prepared future25 scripts only. Start bounded check-only waiting after formal24 identity is known; scientific review and actual restore remain required.',files=report['source_files'],monitor_manifest=report['manifest'],static_review=dict(path=str(out/'STATIC_REVIEW.json'),sha256=sha(out/'STATIC_REVIEW.json'))),indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['source_files','manifest']},indent=2))
