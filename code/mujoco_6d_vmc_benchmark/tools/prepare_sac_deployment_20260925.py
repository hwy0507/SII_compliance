"""Audit and bind the fixed two-SAC x six fixtures plus zero7 parity; no physics."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import sys
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from audit_paired_transitions_20260924 import read, require
from canonical48_sac_deployment_20260925 import frozen_training, sha
from prepare_paired_multiseed_deployment_20260925 import absolute, bind, verify_inputs, canonical_result
from prepare_paired_six_fixture_deployment_20260924 import audit_directory
from audit_sac_startup_pair_20260925 import audit as startup_audit
import run_paired_six_fixture_deployment_20260924 as physics
import report_paired_six_fixture_20260924 as metrics

BRANCHES = ('online_only', 'demo_prefill')
FIXTURES = tuple(range(9400, 9406))
OLD_HASH = 'c417038bcc43c79ed52925cb942a7993b2eeb56595a9b731f92167adaf44b011'
ZERO_REPORT_HASH = 'ec921c8d04cc6af12b822548690f59b87ec5262342dd43b0d811ec7c3b2a6e9b'
FINAL_HASHES = dict(online_only='818c2a7883e6c8433621400a2984eeebde9e269e8fabe5a300857f3d5d113545',
                    demo_prefill='02936896178d223681cfc83e05ca4a8cb6468ed279fc3bc4999ec703a6ae8297')
PROTOCOL = 'docs/CANONICAL48_SAC_DEPLOYMENT_PROTOCOL_20260925.md'
ADDITIONS = (
    'scripts/canonical48_vmc_tuning_20260924.py',
    'tools/prepare_sac_deployment_20260925.py', 'tools/run_sac_deployment_20260925.py',
    'tools/report_sac_deployment_20260925.py', 'tools/prepare_paired_multiseed_deployment_20260925.py',
    'tools/prepare_paired_six_fixture_deployment_20260924.py', 'tools/run_paired_six_fixture_deployment_20260924.py',
    'tools/report_paired_six_fixture_20260924.py', 'tools/run_paired_multiseed_deployment_20260925.py',
    'tools/audit_sac_startup_pair_20260925.py', 'scripts/canonical48_sac_deployment_20260925.py',
    'scripts/run_panel_sac_deployment_20260925.py', 'scripts/run_panel_zero_20260924.py',
    'scripts/canonical48_paired_deployment_20260924.py', 'scripts/run_panel_paired_deployment_20260924.py',
    'tools/audit_paired_transitions_20260924.py')


def zero_parity(reference, current):
    reference, current = Path(reference), Path(current)
    files = ('rollout/rollout.npz', 'rollout/physics_states.npz', 'rollout/contact_samples.npz',
             'metrics/episode_0/substep_metrics.npz')
    arrays, inputs = {}, {}
    for root in (reference, current):
        require({str(p.relative_to(root)) for p in root.rglob('*.npz')} == set(files), 'Zero7 raw contract differs')
    for name in files:
        for root in (reference, current): bind(root/name, inputs)
        with np.load(reference/name, allow_pickle=False) as a, np.load(current/name, allow_pickle=False) as b:
            require(set(a.files) == set(b.files), 'Zero7 raw keys differ')
            for key in a.files:
                require(a[key].dtype == b[key].dtype and np.array_equal(a[key], b[key]), 'Zero7 exact raw mismatch: '+name+':'+key)
                require(a[key].dtype.kind in 'bfciuSU', 'Unexpected raw dtype')
                if a[key].dtype.kind in 'bfciu': require(np.isfinite(a[key]).all(), 'Nonfinite zero7')
                arrays[name+':'+key] = dict(shape=list(a[key].shape), dtype=str(a[key].dtype), exact=True)
    for root in (reference, current):
        for name in ('rollout/rollout.json', 'rollout/rollout.mjb', 'metrics/episode_0/substep_metrics.json'): bind(root/name, inputs)
    require(sha(reference/'rollout/rollout.mjb') == sha(current/'rollout/rollout.mjb'), 'Zero7 MJB differs')
    require(canonical_result(read(reference/'rollout/rollout.json')) == canonical_result(read(current/'rollout/rollout.json')), 'Zero7 dynamics JSON differs')
    require(read(reference/'metrics/episode_0/substep_metrics.json') == read(current/'metrics/episode_0/substep_metrics.json'), 'Zero7 50us summary differs')
    with np.load(current/'rollout/rollout.npz', allow_pickle=False) as raw:
        require(raw['observation'].shape == (600, 48) and raw['action'].shape == (600, 7) and not np.any(raw['action']), 'Full600 actual zero7 required')
    return dict(passed=True, full600=True, arrays=arrays, model_mjb_sha256=sha(current/'rollout/rollout.mjb'), input_sha256=inputs)


def matrix_keys(jobs):
    keys = [(j['method'], j['fixture']['seed']) for j in jobs]
    require(len(keys) == len(set(keys)) == 13 and set(keys) == {(b,f) for b in BRANCHES for f in FIXTURES} | {('zero7',9400)}, 'Exact SAC13 matrix required')
    return keys


def check_run(spec, reference, inputs):
    branch = spec['branch']; directory = absolute(spec['training_directory'])
    manifest, complete, _ = frozen_training(directory, branch)
    require(len(manifest['source_hashes']) == 167, 'Expected original167 Python sources')
    final_path = absolute(spec['final_audit']); final = read(final_path)
    require(bind(final_path, inputs) == FINAL_HASHES[branch], 'Independent final SAC audit not pinned')
    require(final['passed'] and final['algorithm'] == 'standard SAC' and final['branch'] == branch and final['seed'] == 20260923, 'Wrong final audit identity')
    require({k: final['final_checkpoint'][k] for k in ('seed','steps','updates')} == dict(seed=20260923,steps=8192,updates=8092), 'Wrong SAC checkpoint')
    require(final['optimizer_steps'] == complete['optimizer_steps'] == dict(actor=8092,critic=8092,entropy=8092), 'SAC actual optimizer budget differs')
    gym = final['gym_transition_audit']
    require(gym['passed'] and gym['training_transitions'] == 8192 and gym['manifest_sha256'] == sha(directory/'manifest.json'), 'Final Gym audit mismatch')
    for name, item in final['artifacts'].items():
        require('..' not in Path(name).parts and not Path(name).is_absolute(), 'Artifact escaped run')
        require(Path(item['path']) == Path(gym['run'])/name and bind(directory/name, inputs) == item['sha256'], 'Final original artifact mismatch')
    episodes = set(); count = 0
    for episode in gym['episodes']:
        folder = audit_directory(episode['directory'], gym['run'], directory)
        require(folder not in episodes, 'Duplicate Gym episode'); episodes.add(folder)
        if episode['transitions'] == 0:
            require(episode.get('empty_reset') and not (folder/'transitions.jsonl').read_text().strip(), 'Invalid empty reset'); bind(folder/'transitions.jsonl', inputs)
        else:
            require({'transitions.jsonl','transitions.npz','actor_trace.npz','transition_contract.json'} <= set(episode['hashes']), 'Incomplete Gym hashes')
            for name, value in episode['hashes'].items():
                require(Path(name).name == name and bind(folder/name, inputs) == value, 'Gym raw artifact changed')
        if folder.relative_to(directory).parts[0] == 'train': count += episode['transitions']
    require(count == 8192 and episodes == {p.parent.resolve() for p in directory.rglob('transitions.jsonl')}, 'Not all actual episodes audited')
    require({r['condition'] for r in final['evaluations']} == {'train/zero','train/sac','validation/zero','validation/sac'}, 'Four final evaluations missing')
    zero_path = absolute(spec['zero_parity']); zero = read(zero_path); bind(zero_path, inputs)
    require(zero['passed'] and zero['branch'] == branch and zero['mode'] == 'direct7' and zero['normalization_frozen'], 'Wrong zero audit')
    require(set(zero['zero']) == {'train','validation'} and all(r['passed'] for r in zero['zero'].values()), 'Both zero splits required')
    verify_inputs(zero, inputs)
    for split in ('train','validation'):
        for run in (directory, reference):
            for name in ('rollout.json','rollout.npz','rollout.mjb'):
                path = str(run/'eval'/split/'zero/episode_00000'/name)
                require(path in zero['input_sha256'], 'Zero audit does not bind both original runs')
    # The old zero report did not include the reference manifest; bind it explicitly.
    ref_manifest = read(reference/'manifest.json'); ref_complete = read(reference/'COMPLETE.json')
    require(not (reference/'FAILED.json').exists(), 'Reference training failed')
    require(ref_manifest['mode'] == ref_complete['mode'] == 'direct7' and ref_manifest['training']['seed'] == ref_complete.get('seed',20260923) == 20260923 and ref_complete['status'] == 'complete', 'Wrong zero reference identity')
    require(bind(reference/'ppo_final.zip',inputs)==ref_complete['checkpoint_sha256'],'Reference final model changed')
    with zipfile.ZipFile(reference/'ppo_final.zip') as archive:ref_model=json.loads(archive.read('data'))
    require(ref_model['seed']==20260923 and ref_model['num_timesteps']==8192 and ref_model['_n_updates']==384,'Reference actual model identity differs')
    for name in ('manifest.json','COMPLETE.json'): bind(reference/name, inputs)
    replay_path = absolute(spec['replay']); replay = read(replay_path); bind(replay_path, inputs)
    require(replay['passed'] and replay['branch'] == branch and replay['mode'] == 'direct7' and replay['samples'] == 600 and replay['end_to_end_exact'], 'Wrong full600 SAC adapter replay')
    meta = replay['metadata']
    require(meta['algorithm'] == 'standard SAC' and meta['branch'] == branch and meta['mode'] == 'direct7' and meta['device'] == 'cuda', 'Wrong replay algorithm/branch/device')
    require(meta['training_manifest_sha256'] == sha(directory/'manifest.json') and meta['training_complete_sha256'] == sha(directory/'COMPLETE.json'), 'Replay origin drift')
    for name in ('checkpoint_sha256','normalizer_sha256'): require(meta[name] == complete[name], 'Replay final artifacts differ')
    require(set(replay['splits']) == {'train','validation'}, 'Replay missing split')
    for item in replay['splits'].values():
        require(item['actual_evaluation']['samples'] == 600 and item['fallback'] is None and item['end_to_end_exact'], 'This plan admits only actual full600 evaluations')
        require(all(c['passed'] and c['exact'] for c in item['actual_evaluation']['checks'].values()), 'Replay/reset numerical mismatch')
    require(all(c['passed'] and c['exact'] for c in replay['normalizer_checks'].values()), 'RMS mutated')
    verify_inputs(replay, inputs)
    for split in ('train','validation'):
        for name in ('rollout.json','rollout.mjb'):
            require(str(directory/'eval'/split/'sac/episode_00000'/name) in replay['input_sha256'], 'Final SAC eval unbound')
    return manifest, dict(directory=str(directory), branch=branch, algorithm='standard SAC', mode='direct7', device='cuda', seed=20260923,
        training_steps=8192, training_updates=8092, data_budget=manifest['data_budget'], nominal_options=manifest['nominal_options'],runtime=manifest['runtime'],
        manifest_sha256=sha(directory/'manifest.json'), complete_sha256=sha(directory/'COMPLETE.json'),
        checkpoint_sha256=complete['checkpoint_sha256'], normalizer_sha256=complete['normalizer_sha256'],
        final_audit_sha256=sha(final_path), replay_sha256=sha(replay_path), zero_parity_sha256=sha(zero_path))


def build_jobs(rows, training, zero_command, output):
    jobs = []
    for row in rows:
        for branch in BRANCHES:
            folder = output/branch/str(row['fixture']['seed']); params = list(row['command'][row['command'].index('--')+1:])
            require('--model' not in params and '--settle-only' not in params, 'Not original VMC task')
            params[params.index('--output')+1] = str(folder/'rollout/rollout')
            params += ['--sac-branch',branch,'--training-directory',training[branch]['directory'],'--deployment-device','cuda']
            jobs.append(dict(method=branch, algorithm='standard SAC', training_seed=20260923, fixture=row['fixture'], job=str(folder),
                result=str(folder/'rollout/rollout.json'), command=[sys.executable,str(ROOT/'scripts/run_with_substep_metrics_20260923.py'),
                '--runner',str(ROOT/'scripts/run_panel_sac_deployment_20260925.py'),'--metrics-output',str(folder/'metrics'),'--',*params],
                environment=dict(row['environment'],PRIMITIVE_RUNNER_PATH=str(ROOT/'scripts/run_primitive_teacher_v7_20260917.py')),
                expected_mjb_sha256=row['model_mjb_sha256'],reference_result=row['result'],reference_result_sha256=row['result_sha256']))
    zero = copy.deepcopy(zero_command); folder = output/'zero7/9400'
    zero.update(method='zero7',algorithm='zero action7',training_seed=None,job=str(folder),result=str(folder/'rollout/rollout.json'))
    cmd=zero['command'];cmd[0]=sys.executable;cmd[1]=str(ROOT/'scripts/run_with_substep_metrics_20260923.py')
    for flag,value in (('--runner',ROOT/'scripts/run_panel_zero_20260924.py'),('--metrics-output',folder/'metrics'),('--output',folder/'rollout/rollout')):
        require(cmd.count(flag)==1,'Ambiguous zero flag');cmd[cmd.index(flag)+1]=str(value)
    zero['environment']['PRIMITIVE_RUNNER_PATH']=str(ROOT/'scripts/run_primitive_teacher_v7_20260917.py')
    jobs.insert(0,zero);matrix_keys(jobs);return jobs


def prepare(request_path, output):
    request_path=absolute(str(request_path));request=read(request_path);output=absolute(str(output));inputs={}
    require(not output.exists(),'Fresh execution directory required');bind(request_path,inputs)
    old_path=absolute(request['old_report']);require(bind(old_path,inputs)==OLD_HASH,'Pinned old18 report differs');old=read(old_path)
    zero_report_path=absolute(request['zero_report']);require(bind(zero_report_path,inputs)==ZERO_REPORT_HASH,'Pinned zero7 report differs');zero_report=read(zero_report_path)
    matched_path=absolute(request['matched_report']);require(bind(matched_path,inputs)==zero_report['old_report_sha256'],'Original matched report lineage differs');matched=read(matched_path)
    zero_archive=absolute(request['zero_archive']);require(not (zero_archive/'FAILED.json').exists(),'Old zero archive failed')
    for name in ('COMPLETE.json','FINAL_RESULT.json','protocol.json'):bind(zero_archive/name,inputs)
    reference=absolute(request['reference_training'])
    specs=request['runs'];require(len(specs)==2 and {s['branch'] for s in specs}==set(BRANCHES),'Exactly two fixed SAC runs required')
    training={};manifests={}
    for spec in specs:manifests[spec['branch']],training[spec['branch']]=check_run(spec,reference,inputs)
    a,b=[manifests[x] for x in BRANCHES]
    for field in ('source_hashes','fixture_specs','asset_hashes','runtime','reward','nominal_options','training','base_protocol_sha256'):
        require(a[field]==b[field],'SAC pairing differs: '+field)
    startup_path=absolute(request['startup_audit']);startup=read(startup_path);bind(startup_path,inputs)
    training_root=Path(training['online_only']['directory']).parents[1]
    require(Path(training['demo_prefill']['directory']).parents[1]==training_root,'Different training campaign')
    demo=training_root/'demo';demo_manifest=read(demo/'manifest.json')
    require(bind(demo/'manifest.json',inputs)==b['demo']['manifest_sha256'] and demo_manifest['artifact_sha256']==b['demo']['artifact_sha256'],'Training-only demo lineage differs')
    for name,value in b['demo']['artifact_sha256'].items():require(bind(demo/name,inputs)==value,'Demo bytes differ')
    transfer_path=absolute(request['archive_verification']);transfer=read(transfer_path)
    require(bind(transfer_path,inputs)=='9b3a6f0d06dae480f15233f9cd4232b200377dd88e9c56a5d430d29f78a64d79','Archive verification differs')
    require(transfer['passed'] and transfer['both_training_complete'] and not transfer['branch_failed_markers'] and transfer['both_timeout_returncodes']==[0,0],'Training archive incomplete')
    require(transfer['remote_root']=='arm1@192.168.31.70:'+str(training_root),'Archive remote origin differs')
    require(transfer['local_file_count']==transfer['remote_file_count']==769 and transfer['local_total_bytes']==transfer['remote_total_bytes']==2168627284,'Archive scope differs')
    checksum=transfer['checksum_verification'];require(transfer['copy_returncode']==checksum['returncode']==0 and checksum['stdout']=='' and checksum['itemized_difference_count']==0,'Archive checksum comparison incomplete')
    for name,value in transfer['sha256'].items():require(bind(training_root/name,inputs)==value,'Archived training artifact drift')
    require(startup['passed'] and startup_audit(training_root)==startup,'Actual paired startup audit does not reproduce')
    require(bind(training_root/'PREFLIGHT.json',inputs)==startup['preflight_sha256'],'Startup preflight differs')
    sources=dict(a['source_hashes'])
    for name in ADDITIONS:
        value=sha(ROOT/name);require(name not in sources or sources[name]==value,'Cannot override training source');sources[name]=value
    for name,value in sources.items():require((ROOT/name).resolve().is_relative_to(ROOT) and sha(ROOT/name)==value,'Use unchanged training source snapshot: '+name)
    baseline=absolute(request['baseline_results']);require(bind(baseline,inputs)==request['baseline_results_sha256'],'Original six fixture aggregate changed')
    rows=sorted([r for r in read(baseline)['rows'] if r.get('candidate',{}).get('family')=='vmc'],key=lambda r:r['fixture']['seed'])
    require([r['fixture']['seed'] for r in rows]==list(FIXTURES),'Original six VMC fixtures required')
    historical={(r['method'],r['fixture']['seed']):r for r in old['old_eight_method_rows']}
    zero_reaudits={};construct_goal=metrics.goal_constructor(ROOT/'scripts')
    for row in rows:
        fixture=row['fixture']['seed'];require(bind(row['result'],inputs)==row['result_sha256']==historical[('vmc',fixture)]['result_sha256'],'Original VMC result changed')
        for field in ('command','environment','fixture','model_mjb_sha256'):require(row[field]==historical[('vmc',fixture)][field],'Original VMC command/environment changed')
        for name,value in read(row['result'])['source_sha256'].items():require(sources.get('scripts/'+name)==value,'Original physics source differs')
        cmd=row['command'];menagerie=absolute(cmd[cmd.index('--menagerie')+1])
        for name,value in a['asset_hashes'].items():require(bind(menagerie/name,inputs)==value,'Original asset changed')
        folder=zero_archive/'zero'/str(fixture)
        require(bind(folder/'rollout/rollout.json',inputs)==historical[('zero',fixture)]['result_sha256'],'Old zero report/result binding differs')
        require(sha(folder/'rollout/rollout.mjb')==row['model_mjb_sha256'],'Old zero MJB differs')
        zero_result=read(folder/'rollout/rollout.json');physical=read(folder/'metrics/episode_0/substep_metrics.json')
        require(physical==historical[('zero',fixture)]['physical'],'Old zero physical summary differs from pinned report')
        raw=physics.physical_raw_audit(folder/'metrics/episode_0/substep_metrics.npz',physical,zero_result['duration_s'])
        goal=construct_goal(json.loads(row['environment']['PANEL_CONFIG']))
        with np.load(folder/'rollout/rollout.npz',allow_pickle=False) as trace:
            require(trace['action'].shape==(600,7) and not np.any(trace['action']),'Old zero not full600 zero7')
            diagnosis=metrics.failure_diagnostics(zero_result,trace,goal)
        require(zero_result['success']==historical[('zero',fixture)]['task_success'] and diagnosis['strict_success_recomputed']==historical[('zero',fixture)]['strict_success'],'Old zero gates differ from pinned audit')
        zero_reaudits[str(fixture)]=dict(raw_metric_audit=raw,diagnosis=diagnosis,
            provenance='New preparation recomputation against pinned result and metric summaries; original matched report did not retain all six NPZ hashes')
        for p in sorted(folder.rglob('*')):
            if p.is_file():bind(p,inputs)
    for report in (zero_report,):
        for name,value in report['artifact_sha256'].items():
            if name.startswith('zero/'):
                require('..' not in Path(name).parts and bind(zero_archive/name,inputs)==value,'Old zero raw changed since pinned audit')
    require({r['fixture']['seed'] for r in matched['rows'] if r['method']=='zero'}==set(FIXTURES),'Original matched zero six coverage missing')
    zero_command=read(zero_archive/'zero/9400/command.json')
    for field in ('command','environment','fixture'):require(zero_command[field]==historical[('zero',9400)][field],'Old zero command/environment drift')
    original_zero_runner=Path(zero_command['command'][zero_command['command'].index('--runner')+1])
    require(bind(original_zero_runner,inputs)==sha(ROOT/'scripts/run_panel_zero_20260924.py'),'Must use exact old zero7 runner')
    jobs=build_jobs(rows,training,zero_command,output)
    return dict(status='prepared_not_started',simulations_started=0,total_new_episodes=13,learned_episodes=12,parity_episodes=1,
        algorithm='standard SAC',jobs=jobs,training=training,output=str(output),request=str(request_path),
        old_report=str(old_path),old_report_sha256=OLD_HASH,zero_report=str(zero_report_path),zero_report_sha256=ZERO_REPORT_HASH,
        matched_report=str(matched_path),matched_report_sha256=sha(matched_path),
        zero7_six_fixture_preparation_reaudits=zero_reaudits,
        zero_archive=str(zero_archive),zero_reference=str(zero_archive/'zero/9400'),source_sha256=sources,
        protocol_sha256=sha(ROOT/PROTOCOL),input_sha256=inputs,global_worker_cap=4,max_workers=2,job_timeout_s=1800,
        first_phase='zero7/9400 parity; then both learned9400; then remaining10',preconditions_all_passed=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('request','jobs-output','plan-output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();require(not args.plan_output.exists(),'Fresh plan required')
    plan=prepare(args.request,args.jobs_output);require(not args.plan_output.resolve().is_relative_to(Path(plan['output'])),'Plan outside execution root required')
    args.plan_output.parent.mkdir(parents=True,exist_ok=True)
    with args.plan_output.open('x') as stream:json.dump(plan,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status='prepared_not_started',jobs=13,simulations_started=0,plan_sha256=sha(args.plan_output))))


if __name__=='__main__':main()
