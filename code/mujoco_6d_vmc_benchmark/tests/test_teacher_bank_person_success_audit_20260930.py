from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from teacher_bank_person_success_audit_20260930 import independent_runs


def trace():
    t=np.arange(100)*.01
    return np.column_stack((t,np.full(100,.01),np.ones(100),np.zeros((100,3))))


def test_gap_resets_origin_instead_of_crediting_cross_gap_motion():
    raw=trace();raw[:,3]=-np.arange(100)*.00015;raw[50,2]=0.
    runs,details=independent_runs(raw,dict(axis=[1,0,0],start_s=0.,press_s=.5,hold_s=.5))
    assert len(runs)==2 and all(not r['qualified'] for r in details)
    assert raw[0,3]-raw[-1,3]>.01 and max(runs[:,7])<.01


def test_withdraw_and_opposite_direction_cannot_meet_hand_yield():
    raw=trace();raw[:,3]=-np.maximum(0,np.arange(100)-60)*.001
    runs,details=independent_runs(raw,dict(axis=[1,0,0],start_s=0.,press_s=.3,hold_s=.3))
    assert len(runs)==1 and runs[0,7]==0. and not details[0]['qualified']
    raw[:,3]=np.arange(100)*.001
    runs,details=independent_runs(raw,dict(axis=[1,0,0],start_s=0.,press_s=.5,hold_s=.5))
    assert runs[0,7]==0. and not details[0]['qualified']


def test_strict_force_threshold_and_single_run_qualification():
    raw=trace();raw[:,3]=-np.arange(100)*.0002
    fixture=dict(axis=[1,0,0],start_s=0.,press_s=.5,hold_s=.5)
    runs,details=independent_runs(raw,fixture)
    assert len(runs)==1 and details[0]['qualified']
    raw[:,2]=.05
    runs,details=independent_runs(raw,fixture)
    assert len(runs)==0 and not details
