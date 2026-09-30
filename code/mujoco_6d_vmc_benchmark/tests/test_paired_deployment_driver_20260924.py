"""Offline execution-driver checks: no subprocesses or simulator construction."""
import importlib.util
from pathlib import Path
import threading
import time
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('paired_driver',ROOT/'tools/run_paired_six_fixture_deployment_20260924.py')
driver=importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def test_task_failures_continue_and_worker_cap_is_enforced():
    lock=threading.Lock();active=0;peak=0;results=[];stop=threading.Event()
    jobs=[dict(method='fake',fixture=dict(seed=i)) for i in range(9)]
    def worker(job):
        nonlocal active,peak
        with lock:active+=1;peak=max(peak,active)
        time.sleep(.005)
        with lock:active-=1
        return dict(job,task_success=False,strict_success=False)
    driver.run_stage(jobs,worker,2,stop,results.append)
    assert len(results)==9 and peak<=2 and not stop.is_set()


def test_alignment_error_stops_new_launches_but_drains_started_jobs():
    stop=threading.Event();started=[];rows=[];barrier=threading.Barrier(2)
    jobs=[dict(method='fake',fixture=dict(seed=i)) for i in range(6)]
    def worker(job):
        seed=job['fixture']['seed'];started.append(seed)
        barrier.wait(timeout=2)
        if seed==0:return dict(job,execution_error='alignment failure')
        time.sleep(.03)
        return dict(job,task_success=False,strict_success=False)
    driver.run_stage(jobs,worker,2,stop,rows.append)
    assert sorted(started)==[0,1] and len(rows)==2 and stop.is_set()


def test_existing_job_directory_is_never_written(tmp_path,monkeypatch):
    root=tmp_path/'execution';job=root/'parameter6/9400';job.mkdir(parents=True)
    (job/'command.json').write_text('existing user evidence')
    instance=driver.Execution({},tmp_path/'plan.json','hash',root,2,1)
    monkeypatch.setattr(driver.subprocess,'Popen',lambda *a,**kw:pytest.fail('No process may launch'))
    row=instance.worker(dict(method='parameter6',fixture=dict(seed=9400),job=str(job)))
    assert 'execution_error' in row
    assert (job/'command.json').read_text()=='existing user evidence'
    assert not (job/'result.json').exists()


def synthetic_physics(tmp_path,count=800):
    path=tmp_path/'raw.npz'
    raw=dict(time=np.arange(1,count+1)*5e-5,stage=np.zeros(count,dtype=np.int16),
        error=np.zeros((count,3),dtype=np.float32),twist=np.zeros((count,6),dtype=np.float32),
        qfrc_actuator=np.zeros((count,7),dtype=np.float32),actuator_force=np.zeros((count,7),dtype=np.float32))
    physical=dict(timestep_s=5e-5,samples=count,position_rmse_3d_m=0.,position_rmse_xyz_m=[0.,0.,0.],
        linear_speed_peak_mps=0.,generalized_actuator_torque_peak_nm=0.,stages={'0':dict(count=count,position_rmse_3d_m=0.)})
    np.savez_compressed(path,**raw)
    return path,raw,physical


def test_short_actual_physics_window_keeps_original50us_definition(tmp_path):
    path,_,physical=synthetic_physics(tmp_path)
    result=driver.physical_raw_audit(path,physical,.04)
    assert result['passed'] and result['samples']==800


@pytest.mark.parametrize('kind',['time','nonfinite','count'])
def test_physical_alignment_errors_are_rejected(tmp_path,kind):
    path,raw,physical=synthetic_physics(tmp_path)
    if kind=='time':raw['time'][4]+=.00001
    if kind=='nonfinite':raw['actuator_force'][4,1]=np.inf
    if kind=='count':physical['samples']-=1
    np.savez_compressed(path,**raw)
    with pytest.raises(ValueError):driver.physical_raw_audit(path,physical,.04)
