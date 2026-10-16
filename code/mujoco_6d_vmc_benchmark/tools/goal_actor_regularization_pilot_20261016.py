"""Prepare a finite resumed Direct alpha0/1 pair after the active four families.

Preparation/preflight need a closed checkpoint, not a stopped healthy queue.
Launch and run require the whole predecessor stage to have closed. No automatic
launch, policy selection, final acceptance, or successful-convergence claim.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import shutil
import subprocess

from rl_goal_stage_20261016 import BENCH, read, write, digest, manifest, verify_inputs, completed_stage_checkpoints
from rl_recovery_control_20261016 import verify_checkpoint

KIND='resumed_actor_regularization_pilot'
UPDATED=('rl_goal_stage_20261016.py','probe_goal_credit_20261016.py',
         'train_v4_recovery_rl_20261016.py','goal_actor_regularization_20261016.py',
         'goal_actor_regularization_pilot_20261016.py')


def wrapper(checkpoint, hashes):
    return ('from pathlib import Path\n'
        'from goal_actor_regularization_20261016 import make_actor_regularized_adapter\n'
        'BATCH_SIZE=256\n'
        'OfficialParameterAgent=make_actor_regularized_adapter('
        f'Path(__file__).with_name("official_parameter_agent_n25.py"),{str(checkpoint)!r},{hashes!r})\n')


def validate_pair(reg):
    assert reg['experiment_kind']==KIND and not reg.get('previous_stage') and not reg.get('selected_lineages')
    assert reg['new_interactions_per_family']==11000 and reg['maximum_new_interactions']==22000
    assert reg['optimizer_schedule_steps']==1000000 and len(reg['jobs'])==2
    pred=reg['pilot_predecessor'];root=Path(pred['root'])
    assert digest(root/'REGISTRATION.json')==pred['registration_sha256']
    evidence=reg['probe_evidence']
    assert digest(Path(evidence['path']))==evidence['sha256']
    old=read(root/'REGISTRATION.json')
    assert len(old['jobs'])==4 and {j['controller'] for j in old['jobs']}=={None,'impedance','admittance','vmc'}
    original=next(j for j in old['jobs'] if j['controller'] is None)
    cp=Path(reg['source_checkpoint'])
    assert cp.parent==Path(original['output'])
    checked=verify_checkpoint(cp)
    assert checked['hashes']==reg['source_checkpoint_hashes']
    assert digest(cp.parent/'PROTOCOL.json')==reg['source_protocol_sha256']
    spec=read(cp.parent/'PROTOCOL.json')
    assert spec['goal_registration_sha256']==pred['registration_sha256']
    assert spec['agent_config']['n_step']==25 and spec['agent_config']['actor_bc_alpha']==0.
    assert spec['utd']==1 and not spec.get('tracking_guidance')
    for key in ('parent_root','parent_protocol_sha256','runtime','python','compute_host','resources',
                'dispatch_lock','minimum_free_disk','training_convergence'):
        assert reg[key]==old[key],key
    assert reg['parameter_manifest']==old['parameter_manifest']
    ignored={'tools/'+name for name in UPDATED}
    assert {k:v for k,v in reg['source_manifest'].items() if k not in ignored}=={
        k:v for k,v in old['source_manifest'].items() if k not in ignored}
    control,treatment=reg['jobs']
    assert [j['name'] for j in reg['jobs']]==['direct_control','direct_regularized']
    excluded={'name','output','unit','parameter_source','actor_regularization_migration','actor_bc_alpha'}
    assert {k:v for k,v in control.items() if k not in excluded}=={
        k:v for k,v in treatment.items() if k not in excluded}
    for job,alpha in zip(reg['jobs'],(0.,1.)):
        assert job['controller'] is None and job['actor_bc_alpha']==alpha
        assert job['actor_regularization_migration']==bool(alpha)
        assert job['reward']=='office_task' and job['reward_variant']=='task_safety' and job['hp']=='direct_explore'
        assert job['seed']==original['seed']==spec['seed']
        assert job['checkpoint']==str(cp) and job['checkpoint_hashes']==checked['hashes']
        assert job['inherited_steps']==checked['step'] and job['limit']==checked['step']+11000<=1000000
        assert not job['credit_migration'] and not job.get('backend_migration') and not job.get('tracking_guidance')
    assert 'parameter_source' not in control
    alternate=Path(reg['run_root'])/'parameter_bc1'
    assert treatment['parameter_source']==str(alternate)
    assert manifest(alternate)==reg['regularized_parameter_manifest']
    altered={'official_parameter_agent.py','official_parameter_agent_n25.py','goal_actor_regularization_20261016.py'}
    assert {k:v for k,v in reg['regularized_parameter_manifest'].items() if k not in altered}=={
        k:v for k,v in reg['parameter_manifest'].items() if k not in altered}
    assert digest(alternate/'official_parameter_agent_n25.py')==reg['parameter_manifest']['official_parameter_agent.py']
    assert (alternate/'official_parameter_agent.py').read_text()==wrapper(cp,checked['hashes'])
    assert digest(alternate/'goal_actor_regularization_20261016.py')==reg['source_manifest']['tools/goal_actor_regularization_20261016.py']


def require_predecessor_complete(reg):
    validate_pair(reg)
    root=Path(reg['pilot_predecessor']['root'])
    old=read(root/'REGISTRATION.json');verify_inputs(old)
    state=read(root/'execution.json')
    assert state['registration_sha256']==reg['pilot_predecessor']['registration_sha256']
    return completed_stage_checkpoints(old,state)


def verify_restoration(reg,job,result):
    cfg=read(Path(job['checkpoint']).parent/'PROTOCOL.json')['agent_config']
    assert result['restored_agent_config']==dict(cfg,actor_bc_alpha=job['actor_bc_alpha'])
    expected={name+'/portable.msgpack':job['checkpoint_hashes'][name+'/portable.msgpack']
        for name in ('actor','critic','target_critic','temperature')}
    assert result['restored_model_state_hashes']==expected and result['restored_rng_matches']
    assert result['restored_normalizers_match'] and result['actual_actor_bc_alpha']==job['actor_bc_alpha']
    saved=read(Path(job['checkpoint'])/'official_agent_state.json')
    for key in ('interactions','updates','reward_samples'):
        assert result['restored_agent_diagnostics'][key]==saved[key]


def prepare(previous,cp,probe,destination):
    assert not destination.exists()
    old=read(previous/'REGISTRATION.json');verify_inputs(old)
    assert len(old['jobs'])==4 and not old.get('experiment_kind')
    original=next(j for j in old['jobs'] if j['controller'] is None)
    assert cp.parent==Path(original['output'])
    checked=verify_checkpoint(cp);spec=read(cp.parent/'PROTOCOL.json')
    assert spec['controller'] is None and spec['reward_variant']=='task_safety'
    assert spec['agent_config']['actor_bc_alpha']==0. and spec['agent_config']['n_step']==25
    assert checked['step']+11000<=1000000 and not spec.get('tracking_guidance')
    evidence=read(probe/'COMPARISON.json')
    assert evidence['checkpoint_hashes_unchanged'] and not evidence['training_treatment_deployed']
    for alpha in (0,1):
        arm=evidence['arms'][str(alpha)]
        assert arm['status']=='passed' and arm['discarded_updates']==256 and arm['actual_actor_bc_alpha']==float(alpha)
    destination.mkdir()
    source=destination/'source';parameter=destination/'parameter_n25';alternate=destination/'parameter_bc1'
    ignore=shutil.ignore_patterns('__pycache__','*.pyc')
    shutil.copytree(old['source'],source,ignore=ignore)
    shutil.copytree(old['parameter_source'],parameter,ignore=ignore)
    shutil.copytree(parameter,alternate,ignore=ignore)
    for name in UPDATED:shutil.copy2(BENCH/'tools'/name,source/'tools'/name)
    shutil.copy2(parameter/'official_parameter_agent.py',alternate/'official_parameter_agent_n25.py')
    shutil.copy2(BENCH/'tools/goal_actor_regularization_20261016.py',alternate/'goal_actor_regularization_20261016.py')
    (alternate/'official_parameter_agent.py').write_text(wrapper(cp,checked['hashes']))
    jobs=[]
    for name,alpha in (('direct_control',0.),('direct_regularized',1.)):
        output=destination/name
        job=dict(original,name=name,output=str(output),checkpoint=str(cp),checkpoint_hashes=checked['hashes'],
            inherited_steps=checked['step'],limit=checked['step']+11000,credit_migration=False,backend_migration=False,
            actor_bc_alpha=alpha,actor_regularization_migration=bool(alpha),
            unit='sii-rl-goal-'+hashlib.sha256(str(output).encode()).hexdigest()[:12])
        job.pop('parent_execution_sha256',None)
        if alpha:job['parameter_source']=str(alternate)
        jobs.append(job)
    started=datetime.now(timezone.utc)
    reg=dict(old)
    for key in ('previous_stage','selected_lineages','selection_basis','finite_continuation_budget','parent_checkpoint_hashes'):
        reg.pop(key,None)
    reg.update(experiment_kind=KIND,run_root=str(destination),registered_utc=started.isoformat(),
        dispatch_deadline_utc=(started+timedelta(hours=24)).isoformat(),stop_file=str(destination/'STOP_REQUESTED'),
        source=str(source),source_manifest=manifest(source),parameter_source=str(parameter),parameter_manifest=manifest(parameter),
        regularized_parameter_manifest=manifest(alternate),jobs=jobs,preflight_required_jobs=[j['name'] for j in jobs],
        maximum_new_interactions=22000,new_interactions_per_family=11000,
        coordinator_unit='sii-rl-goal-stage-'+hashlib.sha256(str(destination).encode()).hexdigest()[:12],
        pilot_predecessor=dict(root=str(previous),registration_sha256=digest(previous/'REGISTRATION.json')),
        source_checkpoint=str(cp),source_checkpoint_hashes=checked['hashes'],source_protocol_sha256=digest(cp.parent/'PROTOCOL.json'),
        probe_evidence=dict(path=str(probe/'COMPARISON.json'),sha256=digest(probe/'COMPARISON.json')),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BENCH,text=True).strip(),
        source_worktree_state='Parent frozen physics/reward retained. Explicit actor-loss migration and dispatch/preflight plumbing copied; content manifests authoritative.',
        evidence_basis='Same-checkpoint online alpha0/1 continuation, motivated by matched disposable replay probe. Earlier checkpoint is an explicit paired experimental branch, not a reset or replacement of the active four-family lineage.',
        credit_migration='None. Raw replay, network/optimizer states, normalizers and RNG retained; only treatment actor_bc_alpha0->1 changes.',
        limitations='Finite training-only pair; no acceptance. Preserve short/failed attempts and do not equate action contraction with task improvement.')
    write(destination/'REGISTRATION.json',reg);verify_inputs(reg)
    return reg


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-stage',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    reg=prepare(args.previous_stage.resolve(),args.checkpoint.resolve(),args.probe.resolve(),args.root.resolve())
    print(reg['run_root'])
