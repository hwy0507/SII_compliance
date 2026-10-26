"""Review fixed-budget paired prefix exploration, including physical/action replay."""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import math
import os
import sys
import time


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def wilson(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,center-half),min(1.,center+half)]


def main(args):
    os.sched_setaffinity(0,{52})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    out=args.run;reg=json.loads((out/'REGISTRATION.json').read_text());report=json.loads((out/'REVIEW.json').read_text())
    assert report['passed'] and report['full_learner_optimizer_rng_unchanged'] and report['completed_pairs']==128
    assert report['optimizer_updates']==report['replay_writes']==0 and report['weights_saved'] is False
    for key in ['checkpoint','training_registration','cycle_review','health_review']:assert sha(reg[key]['path'])==reg[key]['sha256']
    for ref in reg['source_hashes'].values():assert sha(ref['path'])==ref['sha256']
    protocol=json.loads(Path(reg['training_registration']['path']).read_text());root=Path(protocol['runtime'])
    sys.path[:0]=[reg['adapter_runtime'],str(Path(reg['episode_adapter']).parent),str(root/'source/tools')]
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner
    from validate_serl_state_20261026 import digest
    from evaluate_serl_seeded_multistep_20261026 import seeded_action,case_action_seed
    from summarize_published_episode_audit_20261025 import summarize
    from replay_published_filter_audit_20261025 import audit as filter_audit
    from replay_published_torque_audit_20261025 import audit as torque_audit
    ck=torch.load(reg['checkpoint']['path'],map_location='cpu',weights_only=False)
    learner=SerlMultistepLearner(root,upstream=Path(reg['upstream']),upstream_manifest=Path(reg['upstream_manifest']),dimension=7,direct=True,seed=ck['seed'],device='cuda:0')
    learner.load_state_dict(ck['learner']);initial=digest(learner.state_dict());assert initial==digest(ck['learner'])==report['initial_state_digest']==report['final_state_digest']
    assert len(report['episodes'])==256
    audits=[];pair_records={};physical_samples=0;max_action_error=0.
    condition=next(c for c in protocol['conditions'] if c['id']==reg['case_id'])
    for episode in report['episodes']:
        index=episode['pair'];mode=episode['mode'];folder=Path(episode['folder'])
        assert 0<=index<128 and mode in ('independent','episode_constant')
        seed=case_action_seed(reg['action_seed_start']+index,condition['id']);assert seed==episode['seed']
        assert sha(folder/'rollout.mjb')==condition['model_sha256']
        rows=[json.loads(l) for l in (folder/'actor_intervals.jsonl').read_text().splitlines()]
        assert len(rows)==episode['actions'] and 0<len(rows)<=6
        key=learner.jax.random.PRNGKey(seed)
        for i,row in enumerate(rows):
            action,key=seeded_action(learner,row['observation'],i,key,mode)
            error=float(np.max(np.abs(action-np.asarray(row['action']))));max_action_error=max(max_action_error,error)
            np.testing.assert_array_equal(action,np.asarray(row['action']));np.testing.assert_array_equal(action,np.asarray(row['executed_action']))
        physical=summarize(folder,'direct',f'{index}:{mode}');filt=filter_audit(folder);torque=torque_audit(folder)
        assert filt['passed'] and torque['passed'];assert physical['samples']<=4800 and physical['row']['elapsed_s']<=.2400001
        assert physical['row']['full_horizon'] is False
        stage=physical['row']['final_task_stage'];assert episode['left_initial_approach']==(stage!='approach')
        assert physical['row']['abort_reason']==episode['terminal']['result']['abort_reason']
        physical_samples+=physical['samples']
        audit=dict(pair=index,mode=mode,source=episode['folder'],physical=physical,filter=filt,torque=torque,action_replay_exact=True)
        (folder/'PREFIX_REVIEW.json').write_text(json.dumps(audit,indent=2)+'\n')
        entry=dict(pair=index,mode=mode,seed=seed,stage=stage,left_initial_approach=stage!='approach',machine_violation=physical['row']['machine_safety_violation'],abort=physical['row']['abort_reason'],samples=physical['samples'],elapsed_s=physical['row']['elapsed_s'],first_action=rows[0]['action'],first_observation=rows[0]['observation'],review=dict(path=str(folder/'PREFIX_REVIEW.json'),sha256=sha(folder/'PREFIX_REVIEW.json')))
        audits.append(entry);assert (index,mode) not in pair_records;pair_records[index,mode]=entry
    assert physical_samples<=reg['maximum_physical_substeps']
    discordance=collections.Counter()
    for i in range(128):
        a=pair_records[i,'independent'];b=pair_records[i,'episode_constant']
        np.testing.assert_array_equal(a['first_action'],b['first_action']);np.testing.assert_array_equal(a['first_observation'],b['first_observation'])
        discordance[str(int(a['left_initial_approach']))+str(int(b['left_initial_approach']))]+=1
    summaries={}
    for mode in ['independent','episode_constant']:
        a=[e for e in audits if e['mode']==mode];k=sum(e['left_initial_approach'] for e in a)
        summaries[mode]=dict(trials=128,left_initial_approach=k,left_initial_approach_without_violation=sum(e['left_initial_approach'] and not e['machine_violation'] for e in a),wilson95_interval_for_prefix_exit=wilson(k,128),aborts=sum(e['abort'] is not None for e in a),machine_violations=sum(e['machine_violation'] for e in a),stages=dict(collections.Counter(e['stage'] for e in a)))
    assert digest(learner.state_dict())==initial and sha(reg['checkpoint']['path'])==reg['checkpoint']['sha256']
    result=dict(passed=True,time=time.time(),report_sha256=sha(out/'REVIEW.json'),source_sha256=sha(__file__),checkpoint=reg['checkpoint'],summaries=summaries,paired_exit_table=dict(discordance),trials=audits,physical_substeps=physical_samples,max_action_replay_error=max_action_error,full_network_optimizer_rng_unchanged=True,new_physics_by_review=0,optimizer_updates=0,convergence_claim=False,limitation='Paired .24s prefixes on one original condition,128 externally predetermined seeds; prefix exit is not full task success. Wilson intervals describe this frozen prefix experiment, not all30 conditions or future changing training policies. Original physical/filter/torque telemetry and seeded actions replayed; no independent raw dynamics rerun. No selection/extension of seeds or rollout data added to training.')
    (out/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(summaries=summaries,paired=discordance,physical_substeps=physical_samples),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);main(p.parse_args())
