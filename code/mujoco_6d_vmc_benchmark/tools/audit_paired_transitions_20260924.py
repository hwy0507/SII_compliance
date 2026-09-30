"""Pure offline transition/reward/controller audit against a hashed source snapshot."""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import numpy as np

FIELDS=('step_index','actor_period_s','observation','next_observation','next_observation_valid','requested_action','policy_action',
        'parameter_request','parameter_control_active','log_scale','stiffness','damping',
        'execution_action','reward','stage','next_stage','terminated','truncated')
REQUIRED_SOURCES=('canonical48_rl_env_20260923.py','canonical48_paired_rl_env_20260924.py',
    'canonical48_potential_reward_20260924.py','canonical48_vmc_tuning_20260924.py',
    'run_vmc_6d_constrained_push_20260918.py')


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):return json.loads(Path(path).read_text())


def pure_definitions(path,names,namespace,constants=()):
    """Load selected numerical definitions only; never import a simulator."""
    selected=[]
    for node in ast.parse(Path(path).read_text()).body:
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names:selected.append(node)
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in node.targets):
            selected.append(node)
    found={node.name for node in selected if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    require(found==set(names),'Missing frozen numerical definitions')
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace)


def load_frozen(snapshot,manifest):
    snapshot=Path(snapshot).resolve();hashes=manifest['source_hashes']
    require(all('scripts/'+name in hashes for name in REQUIRED_SOURCES),'Required frozen source hashes absent')
    for name,expected in hashes.items():
        path=(snapshot/name).resolve()
        require(path.is_relative_to(snapshot),'Source path escapes snapshot')
        require(sha(path)==expected,'Frozen source hash mismatch: '+name)
    ns={'np':np,'copy':copy}
    pure_definitions(snapshot/'scripts/canonical48_potential_reward_20260924.py',
        ('potential','shaped_reward','protocol'),ns,('GAMMA','POSITION_SCALE_M','STAGE_MAX'))
    pure_definitions(snapshot/'scripts/run_vmc_6d_constrained_push_20260918.py',
        ('virtual_frame','SixDVirtualDynamics'),ns)
    pure_definitions(snapshot/'scripts/canonical48_vmc_tuning_20260924.py',('Canonical48VMCTuning',),ns)
    pure_definitions(snapshot/'scripts/canonical48_rl_env_20260923.py',('evaluation_summary',),ns)
    require(manifest['reward']==ns['protocol'](),'Manifest reward protocol mismatch')
    require(manifest['training']['gamma']==ns['GAMMA'],'PPO/reward gamma mismatch')
    train_options=json.loads(manifest['fixture_specs']['train']['command']['environment']['CORE_VMC_CONFIG'])
    require(manifest['nominal_options']==train_options,'Nominal VMC options not from train fixture')
    return ns


def exact(actual,expected,label):
    a,b=np.asarray(actual),np.asarray(expected)
    require(a.shape==b.shape and np.array_equal(a,b),'Exact mismatch: '+label)
    require(np.isfinite(a).all(),'Nonfinite: '+label)


def close(actual,expected,label):
    a,b=np.asarray(actual,dtype=float),np.asarray(expected,dtype=float)
    require(a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all(),'Invalid shape/value: '+label)
    require(np.allclose(a,b,rtol=1e-12,atol=1e-12),'Numerical replay mismatch: '+label)
    return float(np.max(np.abs(a-b))) if a.size else 0.


def audit_episode(directory,manifest,ns,split):
    directory=Path(directory);contract=read(directory/'transition_contract.json')
    require(contract['base_bridge_sha256']==manifest['source_hashes']['scripts/canonical48_rl_env_20260923.py'],
        'Episode base bridge hash differs from snapshot')
    require(contract['mode']==manifest['mode'],'Episode mode drift')
    require(contract['adapter_train_nominal_options']==manifest['nominal_options'],'Episode nominal options drift')
    require(contract['reward']==manifest['reward'],'Episode reward protocol drift')
    require(contract['runtime_core_config']==json.loads(manifest['fixture_specs'][split]['command']['environment']['CORE_VMC_CONFIG']),
        'Episode runtime fixture config drift')
    rows=[json.loads(line) for line in (directory/'transitions.jsonl').read_text().splitlines()]
    count=len(rows);summary=read(directory/'transition_summary.json')
    require(summary['transitions']==count,'Transition summary count mismatch')
    expected_arrays={key:np.asarray([row[key] for row in rows]) for key in FIELDS}
    if rows:
        for key in rows[0]['reward_terms']:
            expected_arrays['reward_term_'+key]=np.asarray([row['reward_terms'][key] for row in rows])
    with np.load(directory/'transitions.npz',allow_pickle=False) as archived:
        require(set(archived.files)==set(expected_arrays),'JSONL/NPZ fields differ')
        for key,value in expected_arrays.items():exact(archived[key],value,'journal '+key)
    with np.load(directory/'actor_trace.npz',allow_pickle=False) as actor:
        for actor_key,journal_key in [('observation','observation'),('action','execution_action'),('phase_reward_metadata','stage')]:
            exact(actor[actor_key],expected_arrays[journal_key],'actor '+actor_key)
    if not rows:
        require(not summary['completed'],'Empty episode marked complete')
        return dict(directory=str(directory),transitions=0,complete=False,empty_reset=True)
    mode=manifest['mode'];dim=6 if mode=='parameter6' else 7
    low=np.full(dim,-1.);high=np.ones(dim)
    if mode=='direct7':low[0]=0.
    controller=ns['Canonical48VMCTuning'](manifest['nominal_options']);controller.reset()
    terminal=bool(rows[-1]['terminated'])
    require(summary['completed']==terminal,'Completion metadata mismatch')
    require(summary['last_next_observation_valid']==(not terminal),'Last observation validity metadata mismatch')
    result=read(directory/'rollout.json') if terminal else None
    evaluation=ns['evaluation_summary'](result,manifest['fixture_specs'][split]) if terminal else None
    max_reward_error=max_controller_error=0.
    discounted_actual=discounted_base=0.;gamma=ns['GAMMA']
    for index,row in enumerate(rows):
        label=f'{directory.name} transition {index}'
        require(row['step_index']==index and row['actor_period_s']==.04,label+' index/action period mismatch')
        require(np.asarray(row['observation']).shape==(48,) and np.asarray(row['next_observation']).shape==(48,),label+' observation shape')
        require(np.asarray(row['requested_action']).shape==(dim,),label+' action shape')
        require(not row['truncated'],label+' unexpected truncation')
        require(bool(row['terminated'])==(terminal and index==count-1),label+' wrong terminal position')
        require(bool(row['next_observation_valid'])==(not bool(row['terminated'])),label+' wrong next validity')
        require(bool(row['parameter_control_active'])==(mode=='parameter6'),label+' wrong parameter active mask')
        applied=np.clip(np.asarray(row['requested_action']),low,high)
        exact(row['policy_action'],applied,label+' applied action')
        if mode=='parameter6':
            action=controller.act(np.asarray(row['observation']),applied);parameters=controller.last_parameters
        else:
            action=applied;parameters=dict(request=np.zeros(6),log_scale=np.zeros(6),
                stiffness=controller.nominal_k,damping=controller.nominal_d)
        for key,expected in [('parameter_request',parameters['request']),('log_scale',parameters['log_scale']),
                ('stiffness',parameters['stiffness']),('damping',parameters['damping']),('execution_action',action)]:
            max_controller_error=max(max_controller_error,close(row[key],expected,label+' '+key))
        if index<count-1:
            exact(row['next_observation'],rows[index+1]['observation'],label+' next actor observation')
            require(row['next_stage']==rows[index+1]['stage'],label+' phase alignment')
        if row['terminated']:
            exact(row['next_observation'],row['observation'],label+' explicit terminal placeholder')
            require(row['next_stage']==result['final_stage'],label+' terminal stage')
        reward,terms=ns['shaped_reward'](row['observation'],row['stage'],row['next_observation'],row['next_stage'],
            terminal=bool(row['terminated']),gate_success=bool(evaluation['development_gate']) if row['terminated'] else False,
            invalid_or_upstream=bool(result['invalid_physics'] or result['upstream_contact']) if row['terminated'] else False)
        require(set(row['reward_terms'])==set(terms),label+' reward term keys')
        max_reward_error=max(max_reward_error,close(row['reward'],reward,label+' reward'))
        for key,value in terms.items():max_reward_error=max(max_reward_error,close(row['reward_terms'][key],value,label+' reward '+key))
        discounted_actual+=gamma**index*row['reward'];discounted_base+=gamma**index*terms['base_terminal']
    initial=ns['potential'](rows[0]['observation'],rows[0]['stage'])
    last_phi=0. if terminal else ns['potential'](rows[-1]['next_observation'],rows[-1]['next_stage'])
    expected_discounted=discounted_base-initial+gamma**count*last_phi
    residual=close(discounted_actual,expected_discounted,'Discounted shaping identity including last recorded transition')
    return dict(directory=str(directory),split=split,mode=mode,transitions=count,complete=terminal,
        last_next_observation_valid=not terminal,last_reward_included=True,
        max_reward_reconstruction_error=max_reward_error,max_controller_replay_error=max_controller_error,
        discounted_actual_reward=discounted_actual,discounted_base_reward=discounted_base,
        initial_potential=initial,last_potential=last_phi,expected_discounted_reward=expected_discounted,
        telescoping_residual=residual,task_success=result['success'] if terminal else None,
        development_gate=evaluation['development_gate'] if terminal else None,
        hashes={name:sha(directory/name) for name in ('transitions.jsonl','transitions.npz','actor_trace.npz','transition_contract.json')})


def audit_run(run,snapshot):
    run=Path(run);manifest=read(run/'manifest.json');ns=load_frozen(snapshot,manifest)
    require(manifest['mode'] in ('parameter6','direct7'),'Unknown mode')
    episodes=sorted(run.rglob('transitions.jsonl'));require(bool(episodes),'No transition journals found')
    reports=[];training_rows=[]
    for path in episodes:
        relative=path.relative_to(run);parts=relative.parts
        split='validation' if len(parts)>1 and parts[:2]==('eval','validation') else 'train'
        reports.append(audit_episode(path.parent,manifest,ns,split))
        if parts[0]=='train':training_rows.extend(json.loads(line) for line in path.read_text().splitlines())
    sb3_report=None
    if (run/'sb3_received_rewards.jsonl').exists():
        received=[json.loads(line) for line in (run/'sb3_received_rewards.jsonl').read_text().splitlines()]
        require(len(received)==len(training_rows),'SB3/Gym reward count mismatch')
        max_conversion=0.
        for index,(row,entry) in enumerate(zip(training_rows,received)):
            require(entry['step']==index+1 and entry['done']==row['terminated'],'SB3 transition order/done mismatch')
            require(entry['gym_float64']==row['reward'],'SB3 callback Gym reward mismatch')
            require(entry['sb3_float32']==float(np.float32(row['reward'])),'SB3 float32 reward mismatch')
            require(entry['reward_terms']==row['reward_terms'],'SB3 reward terms mismatch')
            max_conversion=max(max_conversion,abs(entry['sb3_float32']-row['reward']))
        sb3_report=dict(transitions=len(received),all_float32_conversions_exact=True,max_float64_to_float32_error=max_conversion)
    completed=read(run/'COMPLETE.json') if (run/'COMPLETE.json').exists() else None
    if completed:require(not (run/'FAILED.json').exists(),'Both COMPLETE and FAILED')
    if completed and completed['status']=='complete':
        require(len(training_rows)==manifest['training']['steps']==completed['recorded_transitions']==8192,'Final budget mismatch')
        require(sb3_report is not None,'Completed training lacks independent SB3 reward records')
    return dict(passed=True,run=str(run.resolve()),snapshot=str(Path(snapshot).resolve()),
        manifest_sha256=sha(run/'manifest.json'),verified_source_files=len(manifest['source_hashes']),
        episodes=reports,training_transitions=len(training_rows),sb3_received_rewards=sb3_report,
        complete_episodes=sum(row['complete'] for row in reports),
        partial_episodes=sum(not row['complete'] and row['transitions']>0 for row in reports),
        limitations=['No simulation, training, checkpoint reselection, or mutable-source imports.',
            'Controller replay uses frozen definitions and tolerance rtol=atol=1e-12; raw journal/actor comparisons are exact.',
            'Partial last next observation is retained in independent journal; old actor_trace cannot independently witness that final next boundary.',
            'Gym reward is float64; SB3 receives float32. Callback logs verify conversion when present, not actual advantages or critic/bootstrap values.',
            'Terminal next observation is a marked placeholder; terminal potential is zero and no physical terminal actor observation is claimed.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('run','snapshot','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();require(not args.output.exists(),'Fresh output required')
    report=audit_run(args.run,args.snapshot);report['audit_tool_sha256']=sha(__file__)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(passed=True,output=str(args.output),episodes=len(report['episodes']),training_transitions=report['training_transitions'])))


if __name__=='__main__':main()
