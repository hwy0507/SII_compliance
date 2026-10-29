"""Saved-trajectory ball recovery diagnosis; no fitting or dynamics integration.

Exact nearest-neighbour distances describe observed feature support, not a
proof of recoverability, causal attribution, or calibrated OOD probability.
Teacher replay on student observations is counterfactual, never training data.
"""
import json
import hashlib
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.distance import cdist
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]
from vertical_stage_scrape_teacher_20261030 import VerticalStageScrapeTeacher
from current_student_policy_20260921 import load_current
FIELDS=np.array([14,15,16,20,21,22,26,27,28,39,40,41,42,43,44,45,46,47])
TRAIN=ROOT/'outputs/contact_yield_scrape_retrain_20261030_v1'
DEVELOPMENT=ROOT/'outputs/contact_yield_student_development_20261030_v1'
DEST=ROOT.parents[1]/'docs/evidence/nonrl_v9_candidate_catalogue_20261029'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def nearest(x,reference):
    # At most 64*12600 doubles; no full pairwise matrix or state mutation.
    return np.concatenate([np.sqrt(cdist(x[i:i+64],reference,'sqeuclidean').min(axis=1)/x.shape[1]) for i in range(0,len(x),64)])
def stats(x):return dict(mean=float(np.mean(x)),median=float(np.median(x)),p95=float(np.quantile(x,.95)),maximum=float(np.max(x)))

def main():
    reg=read(DEVELOPMENT/'REGISTRATION.json');review=read(DEVELOPMENT/'REVIEW.json')
    assert review['status']=='verified_fixed27_development_diagnosis'
    assert review['registration_sha256']==sha(DEVELOPMENT/'REGISTRATION.json')
    assert review['execution_sha256']==sha(DEVELOPMENT/'execution.json')
    with np.load(TRAIN/'data/training_data.npz') as z:
        train=z['train'].copy();dataset_obs=z['observation'].copy(); target=z['requested_teacher_action'].copy();episode=z['episode'].copy()
    assert sha(TRAIN/'data/training_data.npz')==read(TRAIN/'data/DATA_COMPLETE.json')['training_data_sha256']
    scale=np.maximum(dataset_obs[train][:,FIELDS].std(0),.005)
    features=np.clip(dataset_obs[:,FIELDS]/scale,-12,12)
    # The neural checkpoints use absolute-input expansion. This is the exact
    # instantaneous representation only; RNN hidden history is not measured.
    features=np.c_[features,np.abs(features)]
    reference=features[train];validation_dist=nearest(features[~train],reference)
    threshold=float(np.quantile(validation_dist,.95))
    ball_val=np.isin(episode,[18,19]) & ~train
    # Identify ball validation by dataset lineage, not assumed integer order.
    meta=read(TRAIN/'data/DATA_COMPLETE.json')
    ball_ids=[r['episode'] for r in meta['lineage'] if r['scene']=='ball' and r['split']=='validation']
    ball_val=np.isin(episode,ball_ids)&~train
    assert int(ball_val.sum())==1500
    ball_val_dist=nearest(features[ball_val],reference)
    rows=[];curves=[];train_errors=[]
    for case in reg['cases']:
        if case['condition']['scene']!='ball':continue
        model=case['model'];folder=DEVELOPMENT/'episodes'/case['id']/'ball'
        assert sha(Path(model['checkpoint']))==model['checkpoint_sha256']
        metrics=read(folder.parent/'METRICS.json')
        assert metrics==next(r for r in review['rows'] if r['method']==model['name'] and r['condition']=='ball_00')
        with np.load(folder/'trajectory.npz') as z:obs=z['observation'].copy(); action=z['action'].copy()
        assert len(obs)==750
        actor=load_current(Path(model['checkpoint']));actor.reset()
        np.testing.assert_array_equal(np.asarray([actor.act(o.copy()) for o in obs]),action)
        teacher=VerticalStageScrapeTeacher(read(folder/'teacher.json'));teacher.reset();ta=[]
        for o in obs:teacher.observe(o.copy());ta.append(teacher.act(o[39:45].copy(),.04))
        ta=np.asarray(ta);x=np.clip(obs[:,FIELDS]/scale,-12,12);x=np.c_[x,np.abs(x)]
        distance=nearest(x,reference);windows=[]
        for begin,end in [(0,2),(2,5),(5,10),(10,20),(20,30)]:
            mask=(np.arange(750)*.04>=begin)&(np.arange(750)*.04<end)
            windows.append(dict(start_s=begin,end_s=end,frames=int(mask.sum()),counterfactual_action_mse=float(np.mean((action[mask]-ta[mask])**2)),
                student_mean_z_yield_mps=float(np.mean(action[mask,3])*.32),counterfactual_teacher_mean_z_yield_mps=float(np.mean(ta[mask,3])*.32),
                pose_error_norm_m=stats(np.linalg.norm(obs[mask,20:23],axis=1)),nearest_train_distance=stats(distance[mask]),fraction_above_validation_p95=float(np.mean(distance[mask]>threshold))))
        # Full real teacher-history prediction error, reset at every episode.
        errors=[]
        for identity in np.unique(episode[train]):
            actor.reset();mask=episode==identity
            pred=np.asarray([actor.act(o.copy()) for o in dataset_obs[mask]])
            errors.append(pred-target[mask])
        err=np.concatenate(errors)
        train_errors.append(dict(method=model['name'],frames=len(err),requested_action_mse=float(np.mean(err**2)),z_action_mse=float(np.mean(err[:,3]**2))))
        rows.append(dict(id=case['id'],family=model['family'],seed=model['seed'],task_success=metrics['task_success'],strict_success=metrics['strict_success'],windows=windows,
            input_hashes={n:sha(folder/n) for n in ['trajectory.npz','teacher.json','student_checkpoint.npz']},metrics_sha256=sha(folder.parent/'METRICS.json')))
        curves.append((model['family'],model['seed'],obs,action,ta,distance,metrics['strict_success']))
    result=dict(status='complete_saved_history_ball_support_diagnosis',dataset_sha256=sha(TRAIN/'data/training_data.npz'),development_review_sha256=sha(DEVELOPMENT/'REVIEW.json'),analyzer_sha256=sha(Path(__file__)),
        fields=FIELDS.tolist(),normalization='train-only std floored0.005, clip[-12,12], absolute expansion: matches instantaneous MLP/RNN input; excludes recurrent hidden history',
        nearest_distance='minimum RMS Euclidean distance to any training frame in the 36-dimensional normalized representation; exact chunked search',
        validation_reference=dict(all_validation=stats(validation_dist),ball_validation=stats(ball_val_dist),all_validation_p95=threshold),
        training_history_errors=train_errors,rows=rows,limitations=['Train00 development trajectories only; no unseen tests or new selection.','Counterfactual teacher replay is not actual teacher recovery or eligible data.','Instantaneous distance omits recurrent history, joint geometry and unselected canonical fields; not a calibrated OOD detector.','Action component converted with0.32 is requested yield velocity, not executed end-effector velocity.','Association between support, action bias and failure does not prove a unique cause.'],new_physical_steps=0,new_optimizer_updates=0)
    path=DEST/'CONTACT_YIELD_BALL_SUPPORT_DIAGNOSIS_20261030.json';assert not path.exists();path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,3,figsize=(14,9),sharex=True)
    colors=['#247ba0','#df7b20','#5b9279'];families=['esn_ridge','rnn_scratch','mlp_scratch']
    for family,seed,obs,act,ta,distance,passed in curves:
        col=families.index(family);color=colors[seed-2026102801];t=np.arange(750)*.04
        label=f'Seed {seed-2026102800}: '+('pass' if passed else 'fail')
        axes[0,col].plot(t,np.linalg.norm(obs[:,20:23],axis=1)*1000,color=color,label=label,lw=1.4)
        axes[1,col].plot(t,act[:,3]*.32,color=color,lw=1.3)
        axes[1,col].plot(t,ta[:,3]*.32,color=color,ls='--',lw=.8,alpha=.65)
        axes[2,col].plot(t,distance,color=color,lw=1.2)
    for col,name in enumerate(['ESN ridge','RNN','MLP']):
        axes[0,col].set_title(name);axes[0,col].legend(fontsize=8)
        axes[2,col].axhline(threshold,color='black',ls=':',label='All-val p95');axes[2,col].set_xlabel('Time (s)');axes[2,col].legend(fontsize=8)
        for row in range(3):axes[row,col].grid(alpha=.2)
    axes[0,0].set_ylabel('Reference position error (mm)')
    axes[1,0].set_ylabel('Requested vertical yield (m/s)\nsolid: student; dashed: teacher replay')
    axes[2,0].set_ylabel('Nearest training-frame RMS distance')
    fig.suptitle('Ball train00 development: real saved student rollouts, three seeds per family',fontsize=14)
    fig.text(.5,.015,'Teacher replay is counterfactual. Distances exclude recurrent history. This is not unseen evaluation or actual teacher takeover.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.96))
    for suffix in ['png','pdf']:fig.savefig(DEST/f'CONTACT_YIELD_BALL_SUPPORT_DIAGNOSIS_20261030.{suffix}',dpi=160)
    print(path)
    for r in rows:
        w=r['windows'][-1];print(r['id'],r['strict_success'],'late action mse',w['counterfactual_action_mse'],'late distance',w['nearest_train_distance']['median'],'above valp95',w['fraction_above_validation_p95'])
if __name__=='__main__':main()
