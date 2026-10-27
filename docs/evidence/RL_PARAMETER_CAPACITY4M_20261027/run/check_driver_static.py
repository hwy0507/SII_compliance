from pathlib import Path
import ast,json,hashlib,sys,time,copy,importlib.util
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');T=B/'repository/SII_compliance/code/mujoco_6d_vmc_benchmark/tools';O=B/'runs/parameter_capacity4m_preparation_20261027_v1'
sys.path.insert(0,str(T));p=T/'resume_cheq_capacity4m_pool30_20261027.py';spec=importlib.util.spec_from_file_location('candidate',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
from parameter_replay_capacity4m_20261027 import MARKER
stage=dict(marker=copy.deepcopy(MARKER),parent_cycle=47,old_capacity=2_000_000,new_capacity=4_000_000,historical_entry_cycle=23,auxiliary_weights_imported=False,optimizer_settings_changed=False,entry_checkpoint=dict(path='synthetic-contract-fixture',sha256='fixture'))
trial=dict(parent_cycle=47,checkpoint=copy.deepcopy(stage['entry_checkpoint']));mod.validate_followup_contract(stage,None,trial)
mod.validate_followup_contract(stage,copy.deepcopy(stage),dict(trial,parent_cycle=48));guards=[]
for key,value in [('parent_cycle',46),('old_capacity',1_000_000),('new_capacity',3_000_000),('historical_entry_cycle',22),('auxiliary_weights_imported',True),('optimizer_settings_changed',True),('marker',{})]:
 bad=copy.deepcopy(stage);bad[key]=value
 try:mod.validate_followup_contract(bad,None,trial)
 except ValueError:guards.append(key)
 else:raise AssertionError(key)
for name,t,previous in [('early_entry',dict(trial,parent_cycle=46),None),('late_entry',dict(trial,parent_cycle=48),None),('entry_checkpoint',dict(trial,checkpoint={}),None),('historical_mutation',trial,dict(stage,unregistered=True))]:
 try:mod.validate_followup_contract(stage,previous,t)
 except ValueError:guards.append(name)
 else:raise AssertionError(name)
s=p.read_text();old=(T/'resume_cheq_capacity_pool30_20261026.py').read_text();seam='    del ck\n    args.algorithm, args.seed, args.cycles'
a=s[s.index(seam):s.index("if __name__ == '__main__':")];b=old[old.index(seam):old.index("if __name__ == '__main__':")];assert a==b
# Native trainer/sampler/learner installation tail remains byte-identical.
assert "from parameter_replay_capacity_20261026 import replay_class, MARKER as CAPACITY_MARKER" in s
assert "ReplayWithCapacity = followup_class(Replay, followup['entry_replay_digest'])" in s
assert "ck['replay']['replay_capacity_extension'] == CAPACITY_MARKER" in s
ast.parse(s)
(O/'DRIVER_STATIC_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),driver_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),original_driver_sha256=hashlib.sha256((T/'resume_cheq_capacity_pool30_20261026.py').read_bytes()).hexdigest(),negative_contract_guards=guards,native_training_sampler_installation_tail_identical=True,original_capacity_marker_preserved=True,actual_complete47_restore=False,formal_deployment=False,new_physics=0,optimizer_updates=0),indent=2)+'\n');print('static passed',len(guards),'negative guards')
