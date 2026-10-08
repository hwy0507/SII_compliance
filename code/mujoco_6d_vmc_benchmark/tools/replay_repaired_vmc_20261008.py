"""Recompute repaired VMC recurrence/actions from saved canonical48 observations.

No MuJoCo model, scene state, contact labels or event timestamps are available
to this replay actor. Checks virtual storage, parameter shield and raw action;
the worker's separate common-filter audit covers the following action stages.
"""
import argparse
import copy
from dataclasses import replace
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np
from office_v7_uniform24_20261008 import read,write,sha,now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True);p.add_argument('--parameter-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
    sys.path.insert(0,str(a.parameter_source))
    from controllers import ParameterController
    from wbc_velocity_residual_core import VelocityResidualSafetyConfig
    prior=copy.deepcopy(read(a.parameter_source/'PRIORS.json')['methods']['vmc'])
    config=read(a.run/'config.json')
    if 'parameters' in config:prior['center']=config['parameters']
    # Office runtime overrides the panel default .16 m/s with .32 m/s.
    # Replay the archived physical units, never silently assume panel defaults.
    units=np.asarray(read(a.run/'CONTROLLER_REPAIR.json')['physical_action_units'])
    assert units.shape==(6,) and np.all(units[:3]==units[0]) and np.all(units[3:]==units[3])
    env=SimpleNamespace(safety_config=replace(VelocityResidualSafetyConfig(),
        maximum_linear_yield_mps=float(units[0]),maximum_angular_yield_radps=float(units[3])))
    actor=ParameterController(env,'vmc',prior)
    trace=read(a.run/'parameter_trace.json');z=np.load(a.run/'baseline_policy.npz')
    raw=z['raw_action'] if 'raw_action' in z else np.zeros((len(z['observation']),prior['action_dimension']))
    assert len(trace)==len(raw)
    errors={k:0. for k in ('action','offset','velocity','parameters','energy')}
    for obs,theta_action,expected,record in zip(z['observation'],raw,z['action'],trace):
        offset,velocity=actor.storage_state()
        errors['offset']=max(errors['offset'],float(np.max(abs(offset-record['offset']))))
        errors['velocity']=max(errors['velocity'],float(np.max(abs(velocity-record['velocity']))))
        action=actor.act(obs,theta_action)
        errors['action']=max(errors['action'],float(np.max(abs(action-expected))))
        errors['parameters']=max(errors['parameters'],float(np.max(abs(actor.shield.theta-record['applied_parameters']))))
        errors['energy']=max(errors['energy'],abs(actor.shield.energy-record['energy_after_j']))
    assert max(errors.values())<1e-10,errors
    write(a.output,dict(status='passed',created_utc=now(),steps=len(raw),max_abs=errors,physics_steps=0,
        actor_inputs='Recorded canonical48 only; VMC recurrence consumes estimated wrench39:45. No environment object except fixed public safety units.',
        scope='Independent chronological actor/state replay; not independent implementation or full new physics',
        physical_action_units=units.tolist(),
        evidence={str(p):sha(p) for p in [a.run/'baseline_policy.npz',a.run/'parameter_trace.json',a.run/'config.json',a.run/'CONTROLLER_REPAIR.json',Path(__file__)]}))


if __name__=='__main__':main()
