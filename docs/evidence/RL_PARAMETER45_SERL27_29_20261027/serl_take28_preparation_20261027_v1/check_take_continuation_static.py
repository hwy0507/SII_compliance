from pathlib import Path
import ast,json,hashlib,time,copy,importlib.util,sys,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';O=B/'runs/serl_take28_preparation_20261027_v1';O.mkdir()
driver=R/'code/mujoco_6d_vmc_benchmark/tools/resume_serl_take_recovery_continuation_20261027.py';spec=importlib.util.spec_from_file_location('candidate',driver);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
regpath=B/'runs/serl_recovery26_take27_20261027_v1/REGISTRATION.json';reg=json.loads(regpath.read_text());rt=Path(reg['recovery_continuation_stage']['runtime']);sys.path[:0]=[str(rt),reg['source_adapter']]
import resume_serl_capacity_reviewed_continuation_20261027 as old
import resume_serl_recovery26_take27_20261027 as entry
base=m.original_recovery_protocol(reg);assert base==json.loads(Path(reg['recovery_continuation_stage']['parent_registration']['path']).read_text())
entry.validate_protocol(reg['recovery_continuation_stage']['parent_registration']['sha256'],reg,'')
fixture=copy.deepcopy(reg);fixture['recovery_continuation_stage'].update(parent_cycle=27,new_cycle=28)
m.validate_stage_contract(fixture,reg);rejects=0
for key,value in [('parent_cycle',26),('new_cycle',29),('new_cycles',2),('quarantined_pending',0),('active_streams',list(range(30))),('gather_sha256','0'*64),('automatic_followup',True),('maximum_new_actions',41251)]:
 bad=copy.deepcopy(fixture);bad['recovery_continuation_stage'][key]=value
 try:m.validate_stage_contract(bad,reg)
 except ValueError:rejects+=1
 else:raise AssertionError(key)
bad=copy.deepcopy(fixture);bad['learner_batch_size']=65537
try:m.validate_stage_contract(bad,reg)
except ValueError:rejects+=1
else:raise AssertionError('protected contract')
steps=1121790
ck=dict(cycle=27,boundary='complete_condition_cycle',controller='direct',seed=20261026,cycles=[dict(cycle=24),dict(cycle=26),dict(cycle=27)],interruption_recovery=reg['interrupted_stream_recovery'],recovery_continuation=reg['recovery_continuation_stage'],steps=steps,replay=dict(size=steps,cursor=steps,multistep_target_extension=dict(pending={i:list(range(31)) for i in range(30)},ready=range(steps-930))),learner=dict(outer_updates=1034291+steps-1039290,num_gradient_steps=8274328+8*(steps-1039290)))
m.validate_parent(ck,reg);boundary=0
for key,value in [('cycle',26),('boundary','partial_episode_valid_replay_reset_environment_on_resume'),('cycles',[dict(cycle=24),dict(cycle=27)]),('cycles',[dict(cycle=24),dict(cycle=25),dict(cycle=26),dict(cycle=27)]),('recovery_continuation',{}),('steps',1039290)]:
 bad=dict(ck);bad[key]=value
 try:m.validate_parent(bad,reg)
 except ValueError:boundary+=1
 else:raise AssertionError(key)
raw=(Path(reg['source_adapter'])/'train_serl_state_20261026.py').read_text();tree=ast.parse(raw);node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main');native=old.transform_main(ast.get_source_segment(raw,node)+'\n');assert hashlib.sha256(native.encode()).hexdigest()==reg['reviewed_continuation_stage']['patched_main_sha256']
new=m.transform(native);prior=entry.transform(native);ast.parse(new)
assert new==prior.replace('complete26 to27; retain partial25 exposure and930 quarantined tails; reuse fully flushed streams30-59','reviewed complete-cycle continuation after take27; retain partial25 exposure and930 quarantined tails; reuse fully flushed streams30-59')
(O/'SAMPLER_MAIN.py.txt').write_text(new);(O/'SOURCE.diff').write_text(''.join(difflib.unified_diff(prior.splitlines(True),new.splitlines(True))))
(O/'DRIVER_SOURCE.diff').write_text(''.join(difflib.unified_diff((rt/'resume_serl_recovery26_take27_20261027.py').read_text().splitlines(True),driver.read_text().splitlines(True))))
r=dict(passed=True,time=time.time(),driver_sha256=hashlib.sha256(driver.read_bytes()).hexdigest(),patched_main_sha256=hashlib.sha256(new.encode()).hexdigest(),original_take27_actual_lineage_evidence_checked=True,contract_negative_fixtures=rejects,boundary_negative_fixtures=boundary,physical_sampler_body_identical=True,change='Generalized protected consecutive lineage validators; sampler only resume metadata wording differs',actual_complete27_restoration=False,optimizer_updates=0,new_physics=0,formal_deployment=False)
(O/'STATIC_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
