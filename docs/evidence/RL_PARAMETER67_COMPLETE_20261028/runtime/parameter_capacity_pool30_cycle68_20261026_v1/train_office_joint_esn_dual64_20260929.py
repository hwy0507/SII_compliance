"""Train a matched-budget dual-readout ESN from frozen office-v5 traces.

The shared reservoir is fixed at 128 units and each route/recovery readout has
64 hidden units.  Recovery labels use only the fixed damped-VMC teacher and
the selector uses the causal proprioceptive qvel transient.
"""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
import torch
from torch import nn

ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def trace_path(case):
    p=ROOT/'outputs'/case
    candidates=[p/'results'/'rollout.npz',p/'rollout.npz',p/'rollout'/'rollout.npz']
    for c in candidates:
        if c.exists():return c
    matches=list(p.glob('*/rollout.npz'))
    if len(matches)!=1:raise FileNotFoundError(f'{case}: {matches}')
    return matches[0]

def load_case(case,label_mode='saved',teacher_config=None):
    p=trace_path(case)
    with np.load(p,allow_pickle=False) as z:
        obs=z['observation'].astype(np.float32);saved=z['applied_action'].astype(np.float32)
    if obs.shape[1]!=48 or saved.shape!=(len(obs),7):raise ValueError(f'bad trace {case}')
    action=saved
    if label_mode=='dagger':
        teacher=SixDVirtualDynamics(teacher_config.get('options',teacher_config))
        scale=float(teacher_config.get('action_scale',1.0))
        action=np.asarray([teacher.act(x[39:45],.04)*scale for x in obs],dtype=np.float32)
    return dict(case=case,path=str(p),sha256=digest(p),observation=obs,action=action,label_mode=label_mode)

def feature_rows(rows,actor):
    feats=[];trans=[]
    for row in rows:
        actor.reset();prev=np.zeros(7);f=[];t=[]
        for obs in row['observation']:
            f.append(actor.features(obs))
            q=obs[7:14].astype(float);t.append(float(np.linalg.norm(q-prev)));prev=q
        feats.append(np.asarray(f,dtype=np.float32));trans.append(np.asarray(t,dtype=np.float32))
    return feats,trans

def fit_head(x,y,seed):
    torch.set_num_threads(1);torch.manual_seed(seed);rng=np.random.default_rng(seed)
    model=nn.Sequential(nn.Linear(x.shape[1],64),nn.Tanh(),nn.Linear(64,7))
    opt=torch.optim.AdamW(model.parameters(),lr=2e-3,weight_decay=1e-5)
    tx,ty=torch.from_numpy(x),torch.from_numpy(y);best=float('inf');best_state=None
    for epoch in range(160):
        model.train()
        for _ in range(48):
            idx=torch.from_numpy(rng.integers(0,len(tx),size=2048))
            raw=model(tx[idx]);pred=torch.cat((torch.sigmoid(raw[:,:1]),torch.tanh(raw[:,1:])),1)
            loss=((pred-ty[idx])**2).mean();opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.);opt.step()
        if epoch==0 or (epoch+1)%5==0:
            model.eval()
            with torch.no_grad():
                raw=model(tx);pred=torch.cat((torch.sigmoid(raw[:,:1]),torch.tanh(raw[:,1:])),1);m=float(((pred-ty)**2).mean())
            if m<best:best=m;best_state={k:v.detach().numpy().copy() for k,v in model.state_dict().items()}
    return best_state,best

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--seed',type=int,default=2026092938);a=ap.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    a.output.mkdir(parents=True);np.random.seed(a.seed);torch.set_num_threads(1)
    stiff=json.loads((ROOT/'configs/office_joint_teacher_stiff_20260927.json').read_text())
    damped=json.loads((ROOT/'configs/office_joint_teacher_damped_20260927.json').read_text())
    fixed=[
      'esn_office_joint_teacher_j1_20260927/results/j1_stiff_original',
      'esn_office_joint_teacher_j1_20260927/results/j1_stiff_hard',
      'esn_office_joint_teacher_j3_20260927/results/j3_stiff_rod_start7',
      'esn_office_joint_teacher_j3_20260927/results/j3_stiff_rod_hold6',
      'esn_office_joint_teacher_j3_20260927/results/j3_stiff_shift_plus']
    # These are the retained, independently audited DAgger3 rollouts.  Keep
    # paths relative to ROOT/outputs so the training manifest points to the
    # exact raw traces rather than the old temporary public-results aliases.
    dagger=[
      'esn_joint_stiff_dagger2_eval_20260927/eval_v1/results/dagger3_student_original',
      'esn_joint_stiff_dagger2_eval_20260927/eval_v1/results/dagger3_student_rod_start7',
      'esn_joint_stiff_dagger2_eval_20260927/eval_v1/results/dagger3_student_rod_start9',
      'esn_joint_stiff_dagger2_eval_20260927/eval_v1/results/dagger3_student_rod_hold6',
      'esn_joint_stiff_dagger2_eval_20260927/eval_v1/results/dagger3_student_shift_plus',
      'esn_joint_stiff_dagger2_eval_20260927/eval_v1/results/dagger3_student_hard']
    recovery_raw=[
      'esn_office_joint_esn_stiff_20260929/teacher_probes_20260929/damped/teacher_damped_rod_start9',
      'esn_office_joint_esn_stiff_20260929/teacher_probes_20260929/damped/teacher_damped_shift_plus']
    route=[load_case(x) for x in fixed]+[load_case(x,'dagger',stiff) for x in dagger]
    recovery=[load_case(x) for x in recovery_raw]+[load_case(x,'dagger',damped) for x in dagger]
    all_rows=route+recovery
    mean=np.concatenate([r['observation'] for r in all_rows]).mean(0).astype(np.float32)
    std=np.concatenate([r['observation'] for r in all_rows]).std(0).clip(min=.03).astype(np.float32)
    actor=ESN128Proprio48Action7(mean,std,seed=a.seed);rf,rt=feature_rows(route,actor);xf,xt=feature_rows(recovery,actor)
    fcat=np.concatenate(rf+xf);fmean=fcat.mean(0).astype(np.float32);fstd=fcat.std(0).clip(min=.03).astype(np.float32)
    route_x=np.concatenate([(f-fmean)/fstd for f in rf]).astype(np.float32);route_y=np.concatenate([r['action'] for r in route]).astype(np.float32)
    impact_x=np.concatenate([(f-fmean)/fstd for f in xf]).astype(np.float32);impact_y=np.concatenate([r['action'] for r in recovery]).astype(np.float32)
    route_state,route_mse=fit_head(route_x,route_y,a.seed+1);impact_state,impact_mse=fit_head(impact_x,impact_y,a.seed+2)
    transient=np.concatenate(rt+xt);center=float(np.percentile(transient,90));width=max(.25*center,.02)
    ck=dict(contract='proprio48_esn_dual64_action7_v1',seed=np.int64(a.seed),mean=mean,std=std,win=actor.win,w=actor.w,leak=actor.leak,input_mask=np.ones(48,dtype=np.float32),alpha=np.float64(1.),output_gain=np.float64(1.),fmean=fmean,fstd=fstd,route_w1=route_state['0.weight'],route_b1=route_state['0.bias'],route_w2=route_state['2.weight'],route_b2=route_state['2.bias'],impact_w1=impact_state['0.weight'],impact_b1=impact_state['0.bias'],impact_w2=impact_state['2.weight'],impact_b2=impact_state['2.bias'],transient_center=np.float64(center),transient_width=np.float64(width),attack_tau=np.float64(.04),release_tau=np.float64(.64))
    np.savez_compressed(a.output/'best.npz',**ck)
    manifest=dict(contract='proprio48_esn_dual64_action7_v1',seed=a.seed,reservoir_units=128,route_readout_units=64,recovery_readout_units=64,hidden_state_units_total=256,route_cases=[r['case'] for r in route],recovery_cases=[r['case'] for r in recovery],route_trace_hashes=[(r['case'],r['sha256'],r['label_mode']) for r in route],recovery_trace_hashes=[(r['case'],r['sha256'],r['label_mode']) for r in recovery],teacher_configs={'route':'configs/office_joint_teacher_stiff_20260927.json','recovery':'configs/office_joint_teacher_damped_20260927.json'},forbidden_inputs=['contact truth','ball state','event time','task stage','visual/range'],transient_selector='norm(qvel_t-qvel_{t-1})',transient_center=center,transient_width=width,route_train_mse=route_mse,recovery_train_mse=impact_mse,checkpoint_sha256=digest(a.output/'best.npz'),source_sha256={str(Path(__file__)):digest(Path(__file__)),str(ROOT/'scripts/esn128_proprio48_action7_20260921.py'):digest(ROOT/'scripts/esn128_proprio48_action7_20260921.py'),str(ROOT/'scripts/current_student_policy_20260921.py'):digest(ROOT/'scripts/current_student_policy_20260921.py')})
    (a.output/'TRAINING_COMPLETE.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
