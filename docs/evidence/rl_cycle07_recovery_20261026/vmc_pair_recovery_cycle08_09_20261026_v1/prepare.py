from pathlib import Path
import json,time,hashlib,sys,copy,os
os.sched_setaffinity(0,{54})
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent
sys.path.insert(0,str(B/'runtime/vmc_cycle07_target_recovery_probe_20261026_v1'))
from validate_published_finite_check_20261025 import digest
sys.path.insert(0,str(B/'runtime/source_train17_clock/source/tools'))
from train_published_compliance_20261025 import validate_resume_protocol,validate_completed_stage_checkpoint
def ref(p):
 with Path(p).open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),sha256=h)
parent=B/'runs/reviewed_continuation_cycle_archive_20261026_v1/vmc/cycle_00007.pt'
oldreg=B/'runs/clock_parameter_reviewed_cycle06_07_20261026_v1/vmc/REGISTRATION.json'
cycle=B/'runs/reviewed_cycle07_audit_20261026_v1/vmc_REVIEW.json';health=B/'runs/reviewed_cycle07_audit_20261026_v1/health/DIAGNOSIS.json';probe=B/'runs/vmc_cycle07_target_recovery_probe_20261026_v1/REVIEW.json'
assert ref(parent)['sha256']==json.loads(cycle.read_text())['checkpoint_sha256']
p=json.loads(probe.read_text());assert p['passed'] and p['parent_checkpoint']==ref(parent) and not p['weights_promoted']
decision=dict(time=time.time(),parent_cycle=7,new_cycles=2,target_change=[5,2],actor_and_critic_lr_unchanged=True,auxiliary_weights_imported=False,cycle_review=ref(cycle),health=ref(health),probe=ref(probe),parent=ref(parent),decision='Withdraw failed all5 intervention, restore original random-pair target only, preserve full cycle7 state and replay. All5 two online cycles did not improve reward and terminal MAE rose16.01 to29.32 to54.90. Matched5000-update pair diagnostic improves terminal MAE to33.04 versus47.25 all5 and42.27 pair+criticLR0.1; but Q tail grows and loss remains abnormal. This is not a repair or convergence claim; two finite online cycles8/9 test recovery under original target with fresh observations. No auxiliary weights or arbitrary resets. Do not automatically extend.',automatic_extension=False,convergence_claim=False)
(OUT/'SCIENTIFIC_DECISION.json').write_text(json.dumps(decision,indent=2)+'\n')
x=torch.load(parent,map_location='cpu',weights_only=False);original=copy.deepcopy(x)
assert x['cycle']==7 and x['boundary']=='complete_condition_cycle' and x['learner']['bellman_target_count']==5
x['learner'].pop('bellman_target_count');x['cycles']=[]
for k,v in original.items():
 if k not in ['learner','cycles']:assert digest(x[k])==digest(v)
for k,v in original['learner'].items():
 if k!='bellman_target_count':assert digest(x['learner'][k])==digest(v)
folder=OUT/'vmc';folder.mkdir();prepared=folder/'prepared_parent.pt';torch.save(x,prepared)
reg=json.loads(oldreg.read_text());rates=[g['lr'] for g in x['learner']['actor_optimizer']['param_groups']]
reg['resume_parent_registration']=ref(oldreg);reg['completed_stage_continuation']=dict(kind='reviewed_complete_stage',new_cycles=2,parent_cycle=7,actor_learning_rate_factor=None,parent_actor_learning_rates=rates,review=ref(OUT/'SCIENTIFIC_DECISION.json'))
path=folder/'REGISTRATION.json';path.write_text(json.dumps(reg,indent=2)+'\n')
validate_resume_protocol(x['protocol_sha256'],reg,ref(path)['sha256']);validate_completed_stage_checkpoint(x,reg['completed_stage_continuation'],2,rates)
receipt=dict(time=time.time(),source_parent=ref(parent),prepared_parent=ref(prepared),only_learner_change='Removed bellman_target_count5 metadata to restore original default2 target train function',all_network_optimizer_replay_rng_preserved=True,new_stage_cycles_history=[],old_cycles_history_preserved_in_parent=True,registration_validated=True)
(folder/'PREPARED_PARENT.json').write_text(json.dumps(receipt,indent=2)+'\n')
oldcmd=json.loads((B/'runs/clock_parameter_reviewed_cycle06_07_20261026_v1/vmc/LAUNCH.json').read_text())['command']
for arg,value in [('--registration',path),('--resume',prepared),('--output',folder/'train')]:oldcmd[oldcmd.index(arg)+1]=str(value)
(OUT/'PREPARED_COMMAND.json').write_text(json.dumps(dict(command=oldcmd),indent=2)+'\n')
print('prepared and validated',flush=True)
