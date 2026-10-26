from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys,time
os.sched_setaffinity(0,{54})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R=B/'repository/SII_compliance';OUT=B/'runs/parameter_pool30_preparation_20261026_v1'
reg=json.loads((OUT/'REGISTRATION.json').read_text())
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(__file__)==reg['source_sha256']
for p,h in reg['source_hashes'].items():assert sha(p)==h
root=B/'runtime/source_train17_clock'
sys.path.insert(0,str(B/'runtime/parameter_batch65536_cycle18_20261026_v1'))
sys.path.insert(0,str(root/'source/tools'))
import numpy as np
import torch
torch.set_num_threads(1)
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('registered_pool_candidate',R/'code/mujoco_6d_vmc_benchmark/tools/parameter_shared_sampler_pool_20261026.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
sampler_affinity,validate_pool,transform_trainer=helper.sampler_affinity,helper.validate_pool,helper.transform_trainer
from published_compliance_learner_20261025 import PublishedLearner
from published_pair_reduction_learner_20261026 import pair_class
from validate_published_finite_check_20261025 import digest
trainer=root/'source/tools/train_published_compliance_20261025.py'
original=trainer.read_text();candidate=transform_trainer(original);ast.parse(candidate)
# Only the two registered scheduling strings differ, not learner/update/physics.
guard="""    if len(set(cpus)) != len(cpus) or args.workers > len(cpus)-1:
        raise ValueError('Reserve one distinct learner CPU plus one per sampler')"""
assert candidate.replace('    _validate_parameter_sampler_pool(protocol, args, cpus)',guard).replace('str(_parameter_sampler_affinity(args.controller, cpus, slot))','str(cpus[slot+1])')==original
methods={}
for method,first in [('impedance',13),('admittance',26),('vmc',39)]:
    cp=Path(reg['parents'][method]['path']);assert sha(cp)==reg['parents'][method]['sha256']
    x=torch.load(cp,map_location='cpu',weights_only=False);assert x['cycle']==17 and x['boundary']=='complete_condition_cycle'
    protocol=json.loads((B/'runs/parameter_batch65536_cycle17_20261026_v1'/method/'REGISTRATION.json').read_text())
    protocol['sampler_pool']=dict(kind='shared_physical_cpu_set',workers=30,learner_cpu=first,physical_cpus=list(range(first+1,first+13)))
    args=SimpleNamespace(controller=method,workers=30);cpus=list(range(first,first+13));validate_pool(protocol,args,cpus)
    affinities=[sampler_affinity(method,cpus,slot) for slot in range(30)]
    assert all(set(map(int,value.split(',')))==set(cpus[1:]) for value in affinities)
    for bad_workers in [0,12,29,31]:
        bad=copy.copy(args);bad.workers=bad_workers
        try:validate_pool(protocol,bad,cpus)
        except ValueError:pass
        else:raise AssertionError('Bad worker count accepted')
    for bad_cpus in [cpus[:-1],[first]*13,list(range(13))]:
        try:validate_pool(protocol,args,bad_cpus)
        except ValueError:pass
        else:raise AssertionError('Changed CPU allocation accepted')
    for bad_slot in [-1,30]:
        try:sampler_affinity(method,cpus,bad_slot)
        except ValueError:pass
        else:raise AssertionError('Bad slot accepted')
    outputs=[];states=[]
    for repeat in range(2):
        learner=pair_class(PublishedLearner,{'impedance':'minimum','admittance':'mean','vmc':'mean'}[method])(
            root,dimension=x['replay']['arrays']['actions'].shape[1],direct=False,seed=x['seed'],device='cpu',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)
        learner.load_state_dict(x['learner']);assert digest(learner.state_dict())==digest(x['learner'])
        for slot in range(30):learner.reset_episode(stream=slot)
        assert len({id(learner.mixers[slot]) for slot in range(30)})==30
        counts=[0]*30;trace=[]
        # Interleaved nonuniform stream visits test local clocks and mixing,
        # including streams12..29 that the current online pool does not use.
        for slot in list(range(30))+list(reversed(range(30)))+[0,17,29,17,5]:
            raw=x['replay']['arrays']['observations'][-30+slot,:48]*x['learner']['observation_scale']
            before={s:(learner.episode_actions[s],float(learner.mixers[s].get_mixing_parameter())) for s in range(30)}
            obs,action,execution,context=learner.act(raw,step=x['steps']+len(trace)+1,stream=slot)
            assert obs[-1]==np.float32((1375-counts[slot])/1375)
            np.testing.assert_array_equal(execution,action*np.float32(context))
            counts[slot]+=1
            for other in range(30):
                if other!=slot:assert before[other]==(learner.episode_actions[other],float(learner.mixers[other].get_mixing_parameter()))
            trace.append((slot,obs.copy(),action.copy(),execution.copy(),context))
        assert learner.learner.num_gradient_steps==x['learner']['num_gradient_steps']
        outputs.append(digest(trace));states.append(digest(learner.state_dict()))
        learner.load_state_dict(x['learner']);assert digest(learner.state_dict())==digest(x['learner'])
        del learner
    assert outputs[0]==outputs[1] and states[0]==states[1]
    methods[method]=dict(checkpoint_sha256=sha(cp),streams=30,interleaved_actions_per_restore=65,repeated_restore_actions_and_full_state_exact=True,nonselected_stream_context_and_clock_unchanged=True,full_state_restored_after_gate=True,negative_guards=9,optimizer_updates=0,new_physics=0)
    del x
report=dict(time=time.time(),passed=True,methods=methods,base_trainer_sha256=sha(trainer),candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),scheduling_seams_only=True,optimizer_updates=0,new_physics=0,weights_saved=False,deployed=False,limitation='CPU/affinity mapping and existing30-stream isolation only; no online throughput, reward equivalence or convergence claim. Future deployment must bind latest completed formal parent, not this historical17 snapshot.')
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
