"""Reproduce actual v1 horizontal-projection shutdown from saved closed-loop observations."""
from pathlib import Path
import numpy as np
from collect_special_scene_actions_20261028 import ROOT,read,write,sha
from diagnose_v9_teacher_handoff_recovery_20261030 import summarize
from cross_track_recovery_teacher_20261030 import CrossTrackRecoveryTeacher


def diagnose(output):
    assert not output.exists()
    rows=[]
    for prefix in (175,275):
        f=ROOT/'outputs/cross_track_teacher_development_20261030_v1'/('rod_prefix'+str(prefix))/'rod';r=summarize(f)
        with np.load(f/'trajectory.npz') as z:obs=z['observation'].copy();time=z['time'].copy();action=z['action'].copy()
        actor=CrossTrackRecoveryTeacher(read(f/'teacher.json'));actor.reset();restore=[];gate=[];pred=[]
        for o in obs:
            actor.observe(o);pred.append(actor.act(o[39:45]));restore.append(actor.last_cross_track_velocity.copy());gate.append(actor.last_cross_track_load_gate)
        np.testing.assert_array_equal(np.asarray(pred)[prefix:],action[prefix:])
        window=(time>=max(prefix*.04,r['pass_s'] or 0))&(time<r['retract_start_s'])
        assert window.any()
        restore=np.asarray(restore);gate=np.asarray(gate)
        r['zero_direction_evidence']=dict(samples=int(window.sum()),
            all_horizontal_direction_zero=bool(np.all(obs[window,45:47]==0)),
            all_full_direction_zero=bool(np.all(obs[window,45:48]==0)),
            maximum_abs_y_reference_error_m=float(np.max(np.abs(obs[window,21]))),
            maximum_abs_new_restore_velocity_mps=float(np.max(np.abs(restore[window]))),
            maximum_new_load_gate=float(np.max(gate[window])))
        assert r['zero_direction_evidence']['all_horizontal_direction_zero']
        assert not r['zero_direction_evidence']['all_full_direction_zero']
        np.testing.assert_array_equal(obs[window,45:48],np.tile([0.,0.,1.],(int(window.sum()),1)))
        r['zero_direction_evidence']['observed_full_direction']=[0.,0.,1.]
        assert r['zero_direction_evidence']['maximum_abs_new_restore_velocity_mps']==0
        rows.append(r)
    result=dict(status='verified_actual_history_vertical_direction_horizontal_shutdown',rows=rows,
        source_sha256=sha(Path(__file__)),no_integration=True,no_fitting_or_test=True,
        interpretation='Actual post-pass direction is vertical [0,0,1], not a full zero vector/pause. v1 and v2 disable horizontal correction despite nonzero reference error; v2 clears remembered horizontal direction on vertical input. The earlier all-full-direction-zero assertion failed and wrote no result; corrected here. This saved-history diagnosis is not dynamic recovery proof.')
    write(output,result);return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(diagnose(p.parse_args().output.resolve())['status'])
