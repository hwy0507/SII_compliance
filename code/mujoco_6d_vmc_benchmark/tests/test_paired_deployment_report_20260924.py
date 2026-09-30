"""Offline aggregation boundaries; no actual results are invented or written."""
import copy
import importlib.util
from pathlib import Path
import pytest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('paired_report',ROOT/'tools/report_paired_six_fixture_20260924.py')
report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)


def rows():
    return [dict(method=method,fixture=dict(seed=seed),task_success=False,strict_success=False,
        physical=dict(samples=480000,timestep_s=5e-5,position_rmse_3d_m=.1,
            generalized_actuator_torque_peak_nm=30.,linear_speed_peak_mps=.12),
        final_stage=1,fixture_triggered=False,rod_contact_s=0.,non_target_external_contacts={})
        for method in report.NEW for seed in report.SEEDS]


def test_exact_method_fixture_identity_rejects_duplicate_or_renamed_vmc():
    data=rows()
    assert len(report.index_rows(data,report.NEW))==18
    duplicate=copy.deepcopy(data);duplicate[1]=duplicate[0]
    with pytest.raises(ValueError,match='matrix'):report.index_rows(duplicate,report.NEW)
    mislabeled=copy.deepcopy(data);mislabeled[-1]['method']='vmc'
    with pytest.raises(ValueError,match='matrix'):report.index_rows(mislabeled,report.NEW)


def test_summary_retains_failed_and_safety_short_episodes_in_denominator():
    data=rows();data[0]['physical']['samples']=800
    data[0]['physical']['position_rmse_3d_m']=.7
    summary=report.summarize(data)['parameter6']
    assert summary['episodes']==6 and summary['full24']==5
    assert summary['task']==summary['strict']==summary['rod_triggered']==0
    assert summary['waypoint_rmse_mm']['mean']==pytest.approx(200.)


def test_execution_error_is_not_a_valid_task_failure():
    data=rows();data[0]['execution_error']='missing raw data'
    with pytest.raises(ValueError,match='Execution errors'):report.index_rows(data,report.NEW)


def passing_episode():
    goal=np.array([.54,0.,.785]);position=np.repeat(goal[None],600,axis=0)
    objects=np.repeat(np.array([[.54,0.,.54]]),600,axis=0)
    trace=dict(position=position,target=position.copy(),object_position=objects,time=np.arange(1,601)*.04)
    rod=dict(duration_s=.4,last_s=21.,bodies=['fr3_link7'],max_penetration_m=.000199)
    result=dict(arguments=dict(scene='push',duration=24.),endpoint_error_m=0.,lift_m=float(.54-.425),
        success=True,grasp_lift_success=True,invalid_physics=False,upstream_contact=False,final_stage=3,
        cup_safe=True,cup_stable=True,cup_support_contact=False,real_contact=True,accepted_panel_demo=True,
        contact=dict(duration_s=.4),panel_audit=dict(contacts={'push_rod_geom':rod},final_rod_gap_m=.003,final_bilateral_grasp=True))
    return result,trace,goal


@pytest.mark.parametrize('boundary',['rod_duration','penetration'])
def test_original_strict_inequalities_are_not_relaxed(boundary):
    result,trace,goal=passing_episode()
    if boundary=='rod_duration':result['panel_audit']['contacts']['push_rod_geom']['duration_s']=.3
    else:result['panel_audit']['contacts']['push_rod_geom']['max_penetration_m']=.0002
    result['accepted_panel_demo']=False
    diagnosis=report.failure_diagnostics(result,trace,goal)
    assert not diagnosis['strict_success_recomputed']
    assert diagnosis['task_failure_reasons']==[]
    assert len(diagnosis['contact_failure_reasons'])==1


def test_cup_metadata_and_external_upstream_have_original_gate_scope():
    result,trace,goal=passing_episode()
    diagnosis=report.failure_diagnostics(result,trace,goal)
    assert diagnosis['strict_success_recomputed']  # No cup_support gate invented.
    result['panel_audit']['contacts']['office_desk_top']=dict(duration_s=.2,bodies=['fr3_link2'],max_penetration_m=.00001)
    diagnosis=report.failure_diagnostics(result,trace,goal)
    assert diagnosis['raw_flags']['accepted_panel_demo']
    assert not diagnosis['strict_success_recomputed']
    assert not diagnosis['task_failure_reasons']
    assert diagnosis['contact_failure_reasons']==['任意非目标外物发生上游接触']


def test_small_stage1_waypoint_error_does_not_hide_final_goal_residual():
    result,trace,goal=passing_episode()
    trace['position'][:,2]=.5279;trace['target'][:,2]=.5279;trace['object_position'][:,2]=.425
    result.update(success=False,grasp_lift_success=False,accepted_panel_demo=False,final_stage=1,lift_m=0.)
    diagnosis=report.failure_diagnostics(result,trace,goal)
    assert diagnosis['values']['last10_current_waypoint_mean_error_mm']==0.
    assert diagnosis['final_goal_diagnostic']['trace_final_distance_3d_mm']==pytest.approx(257.1)
    assert '未到loaded-lift阶段3' in diagnosis['task_failure_reasons']
