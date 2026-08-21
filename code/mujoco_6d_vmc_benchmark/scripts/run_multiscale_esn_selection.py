#!/usr/bin/env python3
"""Fresh validation/test comparison of single- versus multi-time-scale ESN."""
from __future__ import annotations
import argparse, json, sys, time
from dataclasses import replace
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_benchmark import TORQUE_LIMITS
from run_paper_mpc_benchmark import run_rollout
from vmc_compliance_baseline import SpringCarriageConfig, load_controller
from vmc_torque_baseline import VMCTorqueBaseline
from wbc_velocity_residual_env import VelocityResidualFixture

def ints(v):
    x=list(dict.fromkeys(int(a.strip()) for a in v.split(',') if a.strip()))
    if not x: raise argparse.ArgumentTypeError('empty seed list')
    return x
def floats(v):
    x=list(dict.fromkeys(float(a.strip()) for a in v.split(',') if a.strip()))
    if not x or any((not np.isfinite(a) or a<=0) for a in x): raise argparse.ArgumentTypeError('invalid float list')
    return x
def fx(rng):
    return VelocityResidualFixture(float(rng.uniform(.160,.176)),float(rng.uniform(.539,.542)),float(rng.uniform(.90,1.03)),rod_approach_side='positive_y',impactor_type='hand_proxy',rod_cycles=2,cycle_period_s=float(rng.uniform(.66,.72)),impactor_mass_kg=float(rng.uniform(.18,.50)),rod_slide_damping=float(rng.uniform(.6,4.0)),rod_driver_kp=float(rng.uniform(2500,9000)),rod_driver_force_limit_n=float(rng.uniform(150,300)),contact_time_constant_s=float(rng.uniform(.008,.025)))
def fixtures(seed,count): return [fx(np.random.default_rng(np.uint64(seed)*8191+i+1)) for i in range(count)]
def agg(rows): return {'count':len(rows),'success_rate':float(np.mean([r['task_success'] for r in rows])),'mean_at_grasp_err_mm':float(np.mean([r['at_grasp_err_mm'] for r in rows])),'mean_peak_force_n':float(np.mean([r['obstacle_force_n'] for r in rows])),'mean_peak_torque_nm':float(np.mean([r['peak_torque_nm'] for r in rows])),'mean_contact_bout_count':float(np.mean([r['contact_bout_count'] for r in rows])),'hard_limit_count':int(sum(r['hard_limit'] for r in rows))}
def score(s): return s['success_rate'],-s['mean_at_grasp_err_mm']
def esn(men,path,budget,seeds,count,label):
    c=load_controller(path); rows=[]
    for seed in seeds:
        for i,f in enumerate(fixtures(seed,count)):
            c.reset(); r=run_rollout(men,f,impactor_kind='multicontact_hand_proxy',controller=c,residual_scale=budget,seed=seed,verbose_name=f'{label}/fx{i}'); r['fixture_index']=i; rows.append(r)
    return rows
def vmc(men,k,budget,seeds,count,label):
    base=SpringCarriageConfig(k_translation_base=2.2,k_rotation_base=.18); cfg=replace(base,k_translation_base=k,k_rotation_base=base.k_rotation_base*k/base.k_translation_base); rows=[]
    for seed in seeds:
        for i,f in enumerate(fixtures(seed,count)):
            r=run_rollout(men,f,impactor_kind='multicontact_hand_proxy',controller=VMCTorqueBaseline(cfg,TORQUE_LIMITS*budget),residual_scale=budget,seed=seed,verbose_name=f'{label}/fx{i}'); r['fixture_index']=i; rows.append(r)
    return rows
def main():
    p=argparse.ArgumentParser(); p.add_argument('--menagerie',type=Path,required=True); p.add_argument('--single-esn',type=Path,required=True); p.add_argument('--multiscale-esn',type=Path,required=True); p.add_argument('--esn-budget',type=float,default=.05); p.add_argument('--validation-seeds',type=ints,required=True); p.add_argument('--test-seeds',type=ints,required=True); p.add_argument('--fixture-count',type=int,default=4); p.add_argument('--vmc-budgets',type=floats,default=[.02,.03,.05]); p.add_argument('--vmc-k-values',type=floats,default=[1.,1.5,2.2,3.2]); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    if set(a.validation_seeds)&set(a.test_seeds): raise SystemExit('overlapping seeds')
    start=time.time(); es=[]
    for name,path in [('single_scale_esn',a.single_esn),('multi_scale_esn',a.multiscale_esn)]:
        rr=esn(a.menagerie,path,a.esn_budget,a.validation_seeds,a.fixture_count,name+'_validation'); ss=agg(rr); es.append({'model':name,'path':str(path),'budget':a.esn_budget,'summary':ss}); print(name,ss,flush=True)
    vs=[]
    for k in a.vmc_k_values:
        for b in a.vmc_budgets:
            ss=agg(vmc(a.menagerie,k,b,a.validation_seeds,a.fixture_count,f'vmc_k{k:g}_b{b:g}_validation')); vs.append({'k':k,'budget':b,'summary':ss}); print('vmc',k,b,ss,flush=True)
    se=max(es,key=lambda x:score(x['summary'])); sv=max(vs,key=lambda x:score(x['summary'])); print('selected',se,sv,flush=True)
    ep=next(x['path'] for x in es if x['model']==se['model']); tr_es=esn(a.menagerie,Path(ep),a.esn_budget,a.test_seeds,a.fixture_count,'selected_esn_test'); tr_vm=vmc(a.menagerie,sv['k'],sv['budget'],a.test_seeds,a.fixture_count,'selected_vmc_test')
    out={'schema_version':1,'protocol':'multicontact_train_single_vs_multiscale_esn_then_vmc_selection_then_heldout','status':'confirmatory_esn_dynamics_variant','observation_contract':'q,qdot,nominal_twist,pose_error,wbc_twist_error only; no force/apparatus/obstacle/timing/future input','train_note':'both checkpoints use the same successful multi-contact traces, 320 units, same seed/readout fitting, target budget 5%; only reservoir leak dynamics differ','validation_seeds':a.validation_seeds,'test_seeds':a.test_seeds,'fixture_count_per_seed':a.fixture_count,'fixture_generator':'fx(seed*8191 + fixture_index + 1)','esn_candidates':es,'vmc_candidates':vs,'selected':{'esn':se,'vmc':sv},'test_summary':{'esn':agg(tr_es),'vmc':agg(tr_vm)},'test_rows':tr_es+tr_vm}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps({'elapsed_s':time.time()-start,'selected':out['selected'],'test_summary':out['test_summary']},indent=2),flush=True)
if __name__=='__main__': main()
