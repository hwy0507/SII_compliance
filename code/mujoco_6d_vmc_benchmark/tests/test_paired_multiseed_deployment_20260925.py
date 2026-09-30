"""No physics: matrix integrity, exact parity, and training-seed statistics."""
import copy
import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py')
    loaded=importlib.util.module_from_spec(spec);spec.loader.exec_module(loaded);return loaded
prep=module('prepare_paired_multiseed_deployment_20260925')
report=module('report_paired_multiseed_deployment_20260925')
driver=module('run_paired_multiseed_deployment_20260925')


def matrix():
    rows=[dict(training_seed=s,method=m,fixture=dict(seed=f)) for s in prep.SEEDS for m in prep.MODES for f in prep.FIXTURES]
    return rows+[dict(training_seed=20260924,method='nominal_train_vmc',fixture=dict(seed=9400))]


def test_exact24_plus_one_parity_matrix():
    rows=matrix();assert len(prep.matrix_keys(rows))==25
    with pytest.raises(ValueError,match='25-job'):prep.matrix_keys(rows[:-1])
    wrong=copy.deepcopy(rows);wrong[-1]['fixture']['seed']=9401
    with pytest.raises(ValueError,match='25-job'):prep.matrix_keys(wrong)
    wrong=copy.deepcopy(rows);wrong[1]=wrong[0]
    with pytest.raises(ValueError,match='25-job'):prep.matrix_keys(wrong)


def row(mode,seed,fixture,value):
    return dict(training_seed=seed,method=mode,fixture=dict(seed=fixture),task_success=False,strict_success=False,
        physical=dict(samples=480000,timestep_s=5e-5,position_rmse_3d_m=value/1000,
            generalized_actuator_torque_peak_nm=30.,linear_speed_peak_mps=.12),
        final_stage=3,fixture_triggered=True,rod_contact_s=1.,non_target_external_contacts={'rod':{}},
        diagnosis=dict(final_goal_diagnostic=dict(trace_final_distance_3d_mm=10.,last6s_absolute_window=dict(rmse_3d_mm=11.))))


def results():
    rows=[row(m,s,f,100*(i+1)+(f-9402.5)*10) for i,s in enumerate((20260923,*prep.SEEDS)) for m in prep.MODES for f in prep.FIXTURES]
    controls={m:[row(m,None,f,50.) for f in prep.FIXTURES] for m in ('nominal_train_vmc','zero')}
    return rows,controls


def test_statistics_use_three_seed_means_not18_correlated_fixtures():
    rows,controls=results();data=report.seed_statistics(rows,controls)
    result=data['across_training_seeds']['parameter6']['waypoint_rmse_mm']
    assert result['values']==pytest.approx([100.,200.,300.])
    assert result['std_population']==pytest.approx(np.std([100.,200.,300.]))
    assert result['std_population']!=pytest.approx(np.std([r['physical']['position_rmse_3d_m']*1000 for r in rows if r['method']=='parameter6']))
    deltas=data['paired_learning_deltas']
    assert len(deltas)==6 and deltas[0]['seed_mean_deltas']['waypoint_rmse_mm']==pytest.approx(50.)
    assert all(d['shared_control_not_new_training_seed'] for d in deltas)


def test_safety_short_failure_stays_in_denominator_and_tail_becomes_missing():
    rows,controls=results();rows[0]['physical']['samples']=800
    rows[0]['diagnosis']['final_goal_diagnostic']['last6s_absolute_window']=None
    data=report.seed_statistics(rows,controls)
    summary=data['by_training_seed']['parameter6']['20260923']
    assert summary['episodes']==6 and summary['full24']==5 and summary['task_rate']==0.
    assert summary['waypoint_rmse_mm']['mean']==pytest.approx(100.)
    assert summary['last6s_goal_rmse_mm'] is None
    assert data['across_training_seeds']['parameter6']['last6s_goal_rmse_mm'] is None


def test_missing_seed_duplicate_fixture_and_execution_error_are_not_failures():
    rows,controls=results()
    with pytest.raises(ValueError,match='exact3seed'):report.seed_statistics(rows[:-1],controls)
    wrong=copy.deepcopy(rows);wrong[1]=wrong[0]
    with pytest.raises(ValueError,match='exact3seed'):report.seed_statistics(wrong,controls)
    rows[0]['execution_error']='incomplete raw'
    with pytest.raises(ValueError,match='Execution errors'):report.seed_statistics(rows,controls)


def test_parity_canonicalization_only_allows_output_and_known_sets():
    first=dict(arguments=dict(output='a',duration=24),contact=dict(pairs=[[2,1],[1,1]],robot_geoms=['b','a'],robot_bodies=['x'],other_contacts=[]),success=False)
    second=copy.deepcopy(first);second['arguments']['output']='b';second['contact']['pairs'].reverse()
    assert prep.canonical_result(first)==prep.canonical_result(second)
    second['success']=True
    assert prep.canonical_result(first)!=prep.canonical_result(second)
    second=copy.deepcopy(first);second['arguments']['duration']=12
    assert prep.canonical_result(first)!=prep.canonical_result(second)


def nominal_tree(root):
    folder=root/'rollout';folder.mkdir(parents=True)
    result=dict(arguments=dict(output=str(folder/'rollout'),duration=24),contact=dict(pairs=[],robot_geoms=[],robot_bodies=[],other_contacts=[]),success=False)
    (folder/'rollout.json').write_text(json.dumps(result))
    (folder/'rollout.mjb').write_bytes(b'synthetic-model-not-physics')
    (folder/'rollout.paired_deployment.json').write_text(json.dumps(dict(mode='nominal_train_vmc',nominal_options={'K':1})))
    np.savez(folder/'paired_policy_trace.npz',policy_action=np.zeros((600,6)),log_scale=np.zeros((600,6)))
    for name in ('rollout','physics_states','contact_samples'):
        np.savez(folder/(name+'.npz'),numeric=np.array([1.,2.]),labels=np.array(['rod','hand']))
    metrics=root/'metrics/episode_0';metrics.mkdir(parents=True)
    (metrics/'substep_metrics.json').write_text(json.dumps(dict(samples=480000)))
    np.savez(metrics/'substep_metrics.npz',time=np.array([.00005,.0001]))


def test_nominal_parity_checks_all_raw_including_string_metadata(tmp_path):
    first=tmp_path/'first';second=tmp_path/'second';nominal_tree(first);nominal_tree(second)
    result=prep.nominal_parity(first,second)
    assert result['passed'] and result['full600']
    np.savez(second/'rollout/contact_samples.npz',numeric=np.array([1.,2.]),labels=np.array(['desk','hand']))
    with pytest.raises(ValueError,match='raw values'):prep.nominal_parity(first,second)


def test_nominal_parity_rejects_physics_drift_not_just_summary(tmp_path):
    first=tmp_path/'first';second=tmp_path/'second';nominal_tree(first);nominal_tree(second)
    np.savez(second/'metrics/episode_0/substep_metrics.npz',time=np.array([.00005,.000100001]))
    with pytest.raises(ValueError,match='raw values'):prep.nominal_parity(first,second)


def test_nominal_parity_rejects_nonzero_requests_and_partial_control(tmp_path):
    first=tmp_path/'first';second=tmp_path/'second';nominal_tree(first);nominal_tree(second)
    for folder in (first,second):
        np.savez(folder/'rollout/paired_policy_trace.npz',policy_action=np.ones((600,6)),log_scale=np.zeros((600,6)))
    with pytest.raises(ValueError,match='full600 zero6'):prep.nominal_parity(first,second)


def test_audit_input_hash_drift_is_rejected(tmp_path):
    file=tmp_path/'record.json';file.write_text('{}')
    evidence=dict(input_sha256={str(file):prep.sha(file)})
    prep.verify_inputs(evidence,{})
    file.write_text('{"changed":true}')
    with pytest.raises(ValueError,match='Audit input changed'):prep.verify_inputs(evidence,{})


def test_no_execution_command_in_preparation_module():
    # Preparation imports loaders/checkers but never owns a simulator subprocess.
    import ast
    tree=ast.parse(Path(prep.__file__).read_text())
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('Popen','step','mj_step','learn') for n in ast.walk(tree))


@pytest.mark.parametrize('stuck',[False,True])
def test_owned_process_kill_reap_is_bounded_and_unreaped_pid_remains(stuck):
    import subprocess
    class Process:
        pid=731
        returncode=None
        def __init__(self):self.actions=[];self.timeouts=[]
        def poll(self):return self.returncode
        def terminate(self):self.actions.append('terminate')
        def kill(self):self.actions.append('kill')
        def wait(self,timeout):
            self.timeouts.append(timeout)
            if self.actions[-1]=='terminate' or stuck:raise subprocess.TimeoutExpired('synthetic',timeout)
            self.returncode=-9;return -9
    process=Process();result=driver.stop_owned_process(process)
    assert process.actions==['terminate','kill'] and process.timeouts==[15,15]
    assert result['pid']==731 and result['kill_sent'] and result['reaped']==(not stuck)
    assert ('kill reap exceeded15s' in result['errors'])==stuck
