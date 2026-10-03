"""Paired native diagnostic: IPC action execution must reproduce a teacher trace.

This is an explicitly known training-identity replay, not a learned baseline.
It must pass before launching online RL adaptation.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from run_all_methods_formal_20261003 import V6,PARAMETER,MENAGERIE
from run_paper_final_validation_20261003 import ENV


def read_event(stream):
    while True:
        line=stream.readline()
        if not line:raise RuntimeError('Worker closed before terminal')
        try:value=json.loads(line)
        except json.JSONDecodeError:continue
        if not isinstance(value,dict):continue
        if value.get('kind')=='error':raise RuntimeError(value['error'])
        if value.get('kind') in ('observation','terminal'):return value


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--teacher-run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    protocol=a.root/'PROTOCOL.json';role=json.loads((a.teacher_run/'RESEARCH_ROLE.json').read_text())
    assert role['condition']['role']=='train' and role['protocol_sha256']==sha(protocol)
    with np.load(a.teacher_run/'rollout.npz') as z:actions=z['applied_action'].copy();observations=z['observation'].copy()
    env={**os.environ,**ENV,'JAX_PLATFORMS':'cpu','MUJOCO_MENAGERIE_PATH':str(MENAGERIE)}
    command=[sys.executable,str(ROOT/'tools/research72_worker_20261003.py'),'--worker-kind','online',
        '--research-protocol',str(protocol),'--protocol-sha256',sha(protocol),'--research-condition',role['condition']['id'],
        '--v6-input',str(V6),'--reference',str(V6/'esn_original_v2/rollout.json'),'--config',str(a.root/'teacher.json'),
        '--output',str(out/'episode'),'--physics-dt','.00005','--contact-audit','--parameter-source',str(PARAMETER)]
    state=dict(status='running',started_utc=now(),command=command,known_training_trace_sha256=sha(a.teacher_run/'rollout.npz'),
        source_sha256=sha(Path(__file__)),purpose='No learning; predeclared same-actions native IPC parity')
    write(out/'execution.json',state)
    process=None
    try:
        with (out/'stderr.log').open('x') as log:
            process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,bufsize=1,env=env)
            event=read_event(process.stdout)
            for i,action in enumerate(actions):
                assert event['kind']=='observation'
                np.testing.assert_array_equal(event['observation'],observations[i])
                process.stdin.write(json.dumps(dict(action=action.tolist()))+'\n');process.stdin.flush()
                event=read_event(process.stdout)
            assert event['kind']=='terminal'
            process.stdin.close();assert process.wait(timeout=60)==0
        with np.load(a.teacher_run/'rollout.npz') as original,np.load(out/'episode/rollout.npz') as replay:
            keys=['observation','applied_action','qpos','qvel','ctrl','object_pos','stage']
            # Actual log schemas use object_position in some versions. Compare
            # all shared physical keys, and fail if mandatory state is absent.
            keys=['observation','applied_action','qpos','qvel','ctrl']+[k for k in ('object_pos','object_position','stage') if k in original.files]
            for key in keys:np.testing.assert_array_equal(original[key],replay[key])
        with np.load(a.teacher_run/'rollout_metrics/substep_metrics.npz') as original,np.load(out/'episode/rollout_metrics/substep_metrics.npz') as replay:
            for key in original.files:np.testing.assert_array_equal(original[key],replay[key])
        a1=json.loads((a.teacher_run/'AUDIT.json').read_text());a2=json.loads((out/'episode/AUDIT.json').read_text())
        for key in ('task_success','strict_success','rmse_mm','peak_torque_nm','peak_speed_mps','penetration_mm','edge_penetration_mm'):
            assert a1[key]==a2[key],key
        intervals=json.loads((out/'episode/RL_INTERVALS.json').read_text())
        assert intervals[0] is None and len(intervals)==len(actions)+1
        assert abs(sum(x['elapsed_s'] for x in intervals[1:])-55)<1e-8
        state.update(status='complete',observations_and_physics_exact=True,steps=len(actions),
            replay_trace_sha256=sha(out/'episode/rollout.npz'),result=event['result'],
            reward_interval_sha256=sha(out/'episode/RL_INTERVALS.json'))
        print(json.dumps(state))
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        if process is not None and process.poll() is None:
            process.stdin.close()
            try:process.wait(timeout=60)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=60)
        state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':main()
