"""Independently check saved trajectory arithmetic; no MuJoCo calls."""
from pathlib import Path
import argparse,hashlib,json,math,os,time
import numpy as np

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def near(a,b):
    assert math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-12),(a,b)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);o=p.parse_args().root
    os.sched_setaffinity(0,{54});reg=json.loads((o/'REGISTRATION.json').read_text());r=json.loads((o/'REVIEW.json').read_text())
    assert r['passed'] and r['static_forward_calls']==reg['max_static_forward_calls']==1930
    assert r['dynamics_integration_steps']==r['optimizer_updates']==r['replay_writes']==0
    for name,h in reg['input_hashes'].items():assert sha(name)==h
    rows={}
    for item in reg['episodes']:
        c=str(item['cycle']);v=r['methods'][c];path=o/f'cycle{c}_saved_contacts.npz';assert sha(path)==v['values_sha256']
        with np.load(path,allow_pickle=False) as z:a={k:z[k] for k in z.files}
        with np.load(Path(item['folder'])/'rollout.npz',allow_pickle=False) as z:
            for k in ['time','object_position','stage']:np.testing.assert_array_equal(a[k],z[k])
            np.testing.assert_array_equal(a['target_qpos'],z['qpos'][:,9:16]);np.testing.assert_array_equal(a['target_qvel'],z['qvel'][:,9:15])
        n=len(a['time']);assert n==v['saved_frames']==item['saved_frames']
        assert all(np.isfinite(x).all() for x in a.values())
        near(a['pair_penetration_m'].max(),v['sampled_pair_max_m']);near(a['global_penetration_m'].max(),v['sampled_global_max_m'])
        assert int(np.sum(a['pair_penetration_m']>.002))==v['sampled_pair_over2mm']
        assert int(np.sum((a['max_axis_separation_m']>1e-8)&(a['pair_penetration_m']>1e-8)))==v['sampled_separated_but_penetrating']
        near(a['forward_saved_position_error_m'].max(),v['max_forward_saved_position_error_m'])
        speed=np.sqrt(np.sum(a['target_qvel'][:,:3]**2,axis=1));angular=np.sqrt(np.sum(a['target_qvel'][:,3:]**2,axis=1));distance=np.sqrt(np.sum(np.diff(a['object_position'],axis=0)**2,axis=1))
        near(speed.max(),v['max_saved_linear_speed_mps']);near(angular.max(),v['max_saved_angular_speed_rps']);near(distance.max(),v['max_frame_displacement_m']);near(distance[-1],v['final_interval']['displacement_m'])
        near(speed[-2],v['final_interval']['linear_speed_before']);near(speed[-1],v['final_interval']['linear_speed_after'])
        original=json.loads((Path(item['folder'])/'rollout.json').read_text());near(original['stats']['max_penetration_m'],v['original_global_peak_m'])
        assert original['stats']['contact_diagnostics']['corner_target_by_stage']==v['original_corner_contact_by_stage']
        rows[c]=dict(frames=n,values_sha256=sha(path),all_saved_trajectory_fields_exact=True,scalar_arithmetic_passed=True)
    out=dict(passed=True,time=time.time(),methods=rows,source_sha256=sha(__file__),input_review_sha256=sha(o/'REVIEW.json'),registration_sha256=sha(o/'REGISTRATION.json'),plot_sha256=sha(o/'saved_collision_comparison.png'),static_forward_calls=0,dynamics_integration_steps=0,optimizer_updates=0,limitation='Saved-value/hash audit only; does not reproduce unsampled substep collision or establish root cause.')
    with (o/'SAVED_REVIEW.json').open('x') as f:f.write(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
