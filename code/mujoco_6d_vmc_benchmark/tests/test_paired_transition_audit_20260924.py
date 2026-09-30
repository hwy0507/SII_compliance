"""Synthetic corruption checks; no MuJoCo import, simulator, or learned policy."""
import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('paired_audit',ROOT/'tools/audit_paired_transitions_20260924.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
OPTIONS=dict(stiffness_6d=[100,120,140,20,22,24],damping_6d=[11,12,13,4,5,6])


def write_json(path,value):path.write_text(json.dumps(value)+'\n')


def fixture():
    return dict(command=dict(environment=dict(CORE_VMC_CONFIG=json.dumps(OPTIONS))),
        focus='rod',row=dict(id='synthetic',split='train',physical_fixture='rod'),original_checks={})


def setup_case(tmp_path,mode='parameter6',terminal=False):
    ns={'np':np,'copy':__import__('copy')}
    audit.pure_definitions(ROOT/'scripts/canonical48_potential_reward_20260924.py',
        ('potential','shaped_reward','protocol'),ns,('GAMMA','POSITION_SCALE_M','STAGE_MAX'))
    manifest=dict(mode=mode,nominal_options=OPTIONS,fixture_specs={'train':fixture()},
        reward=ns['protocol'](),training=dict(gamma=.995),
        source_hashes={'scripts/'+name:audit.sha(ROOT/'scripts'/name) for name in audit.REQUIRED_SOURCES})
    ns=audit.load_frozen(ROOT,manifest)
    directory=tmp_path/'episode_00000';directory.mkdir()
    write_json(directory/'transition_contract.json',dict(mode=mode,adapter_train_nominal_options=OPTIONS,
        runtime_core_config=OPTIONS,reward=manifest['reward'],
        base_bridge_sha256=manifest['source_hashes']['scripts/canonical48_rl_env_20260923.py']))
    controller=ns['Canonical48VMCTuning'](OPTIONS);controller.reset()
    observations=np.zeros((4,48));observations[:,20]=[.09,.08,.07,.06]
    observations[:,39:45]=np.arange(24).reshape(4,6)*.33
    rows=[]
    for index in range(3):
        done=terminal and index==2;request=np.full(6 if mode=='parameter6' else 7,.2)
        if mode=='parameter6':
            action=controller.act(observations[index],request);parameters=controller.last_parameters
        else:
            action=request;parameters=dict(request=np.zeros(6),log_scale=np.zeros(6),stiffness=controller.nominal_k,damping=controller.nominal_d)
        after=observations[index] if done else observations[index+1]
        reward,terms=ns['shaped_reward'](observations[index],0,after,0,terminal=done)
        rows.append(dict(step_index=index,actor_period_s=.04,observation=observations[index].tolist(),next_observation=after.tolist(),
            next_observation_valid=not done,requested_action=request.tolist(),policy_action=request.tolist(),
            parameter_request=parameters['request'].tolist(),parameter_control_active=mode=='parameter6',
            log_scale=parameters['log_scale'].tolist(),stiffness=parameters['stiffness'].tolist(),damping=parameters['damping'].tolist(),
            execution_action=action.tolist(),reward=reward,reward_terms=terms,stage=0,next_stage=0,terminated=done,truncated=False))
    if terminal:
        contact=dict(max_penetration_m=0.,duration_s=0.,peak_resultant_force_n=0.)
        write_json(directory/'rollout.json',dict(panel_audit=dict(contacts=dict(rod=contact)),success=False,
            invalid_physics=False,upstream_contact=False,peak_torque_nm=0.,speed_p95_mps=0.,endpoint_error_m=.07,final_stage=0))
    persist(directory,rows)
    return directory,manifest,ns,rows


def persist(directory,rows):
    (directory/'transitions.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    arrays={key:np.asarray([row[key] for row in rows]) for key in audit.FIELDS}
    for key in rows[0]['reward_terms']:arrays['reward_term_'+key]=np.asarray([row['reward_terms'][key] for row in rows])
    np.savez_compressed(directory/'transitions.npz',**arrays)
    np.savez_compressed(directory/'actor_trace.npz',observation=arrays['observation'],action=arrays['execution_action'],phase_reward_metadata=arrays['stage'])
    write_json(directory/'transition_summary.json',dict(transitions=len(rows),completed=rows[-1]['terminated'],last_next_observation_valid=rows[-1]['next_observation_valid']))


@pytest.mark.parametrize('mode',['parameter6','direct7'])
@pytest.mark.parametrize('terminal',[False,True])
def test_actual_reward_and_final_partial_next_are_fully_audited(tmp_path,mode,terminal):
    directory,manifest,ns,rows=setup_case(tmp_path,mode,terminal)
    result=audit.audit_episode(directory,manifest,ns,'train')
    assert result['transitions']==3 and result['complete']==terminal
    assert result['last_reward_included'] and result['telescoping_residual']<1e-14
    expected=sum(.995**i*row['reward'] for i,row in enumerate(rows))
    assert result['discounted_actual_reward']==expected


@pytest.mark.parametrize('corruption',['reward','controller','partial_next','validity','actor'])
def test_independent_audit_rejects_consistent_journal_corruption(tmp_path,corruption):
    directory,manifest,ns,rows=setup_case(tmp_path)
    if corruption=='reward':rows[-1]['reward']+=.01
    elif corruption=='controller':rows[1]['stiffness'][0]+=1
    elif corruption=='partial_next':rows[-1]['next_observation'][20]+=.02
    elif corruption=='validity':rows[-1]['next_observation_valid']=False
    persist(directory,rows)
    if corruption=='actor':
        values=dict(np.load(directory/'actor_trace.npz'));values['action'][0,0]+=.01
        np.savez_compressed(directory/'actor_trace.npz',**values)
    with pytest.raises(ValueError):audit.audit_episode(directory,manifest,ns,'train')


def test_wrong_source_or_validation_nominal_cannot_be_substituted(tmp_path):
    _,manifest,_,_=setup_case(tmp_path)
    import copy
    changed=copy.deepcopy(manifest);changed['nominal_options']['stiffness_6d'][0]+=1
    with pytest.raises(ValueError,match='not from train fixture'):audit.load_frozen(ROOT,changed)
    manifest['source_hashes']['scripts/canonical48_potential_reward_20260924.py']='0'*64
    with pytest.raises(ValueError,match='Frozen source hash'):audit.load_frozen(ROOT,manifest)
