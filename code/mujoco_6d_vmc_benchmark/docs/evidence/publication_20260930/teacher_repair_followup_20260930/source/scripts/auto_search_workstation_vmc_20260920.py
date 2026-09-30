"""Resumable, bounded overnight VMC search with feasibility-first elites.

Runs fixed controllers independently in five frozen contact conditions. No
scene labels or contact clocks enter the VMC action. Mixture sampling uses
local perturbations, diagonal CEM proposals and broader exploration. The
displayed best never replaces a feasible teacher with an infeasible trial.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import copy
import fcntl
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
import tune_workstation_vmc_20260920 as tuning
from refine_workstation_vmc_20260920 import assembly_metrics

ROOT=Path(__file__).resolve().parents[1]
LABELS={'rod':'持续棍推','rear':'后板单接触','front':'前板单接触','combined':'棍推＋后板','rear_combined':'棍推＋后移取件'}
FIELDS=[
    ('stiffness_6d',[120,25,500,5,5,5],[1600,600,2600,60,60,70]),
    ('damping_6d',[12,4,24,1,1,1.2],[70,55,110,12,12,14]),
    ('mass_6d',[.15,.15,.3,.02,.02,.02],[1.3,1.3,1.8,.16,.16,.20]),
    ('wrench_limit_6d',[15,15,25,.8,.8,.8],[60,60,85,6,6,7]),
    ('velocity_limit_6d',[.05,.05,.06,.15,.15,.15],[.18,.18,.22,.9,.9,1.]),
    ('deadband_6d',[.05,.05,.05,.005,.005,.005],[1.5,1.5,1.5,.12,.12,.12]),
    ('offset_tracking_gain_6d',[.25],[1.6]),('filter_tau',[.008],[.06]),
    ('axis_rotation_rpy',[-.35,-.35,-.5],[.35,.35,.3])]


def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(value,indent=2));os.replace(temp,path)


def encode(config):
    pieces=[]
    for name,lo,hi in FIELDS:
        x=np.atleast_1d(config[name]).astype(float);lo=np.array(lo);hi=np.array(hi)
        if name!='axis_rotation_rpy':x,lo,hi=np.log(x),np.log(lo),np.log(hi)
        pieces.extend((x-lo)/(hi-lo))
    return np.clip(np.asarray(pieces),0.,1.)


def decode(vector,base):
    config=copy.deepcopy(base);offset=0
    for name,lower,upper in FIELDS:
        n=len(lower);x=vector[offset:offset+n];offset+=n;lo=np.array(lower);hi=np.array(upper)
        y=lo+x*(hi-lo) if name=='axis_rotation_rpy' else np.exp(np.log(lo)+x*np.log(hi/lo))
        config[name]=float(y[0]) if n==1 else y.tolist()
    return config


def sources():
    names=['run_panel_push_20260920.py','workstation_scene_20260920.py','run_vmc_6d_constrained_push_20260918.py',
        'run_primitive_teacher_v7_20260917.py','primitive_contact_scene_v7_20260917.py',
        'haptic_vmc_teacher_20260916.py','audited_velocity_env.py','fixed_panda_wbc.py','wbc_velocity_residual_core.py']
    out={}
    for name in names:
        p=ROOT/'scripts'/name
        if not p.exists():p=ROOT/name
        out[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--hours',type=float,default=10.)
    parser.add_argument('--workers',type=int,default=12)
    parser.add_argument('--population',type=int,default=10)
    parser.add_argument('--rounds',type=int,default=80)
    parser.add_argument('--seed',type=int,default=20260920)
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/vmc_auto_search_20260920')
    parser.add_argument('--self-check',action='store_true')
    args=parser.parse_args()
    if args.hours<=0 or not 1<=args.workers<=16 or args.population<2:raise ValueError('Invalid resource limits')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    lock=(out/'search.lock').open('a+')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('Search already running; refusing a duplicate launch.')
    release=ROOT/'outputs/workstation_teacher_release_20260920/summary.json'
    seed_summary=json.loads(release.read_text())
    if not seed_summary['all_primary_contacts_covered']:raise RuntimeError('Missing feasible warm starts')
    for group in LABELS:
        if group not in seed_summary['selected']:raise RuntimeError('Missing seed for '+group)
    templates={g:seed_summary['selected'][g]['parameters'] for g in LABELS}
    tuning.FIXTURES={g:dict(focus=seed_summary['selected'][g]['row']['focus']) for g in LABELS}
    if args.self_check:
        for group,template in templates.items():
            cfg=template['controller'];decoded=decode(encode(cfg),cfg)
            for key,_,_ in FIELDS:
                if not np.allclose(cfg[key],decoded[key]):raise AssertionError((group,key))
        print(json.dumps(dict(self_check='passed',groups=list(LABELS),search_dimensions=sum(len(lo) for _,lo,_ in FIELDS))))
        return
    current_sources=sources();manifest_path=out/'source_manifest.json'
    if manifest_path.exists() and json.loads(manifest_path.read_text())!=current_sources:
        raise RuntimeError('Control/physics source changed; use a new output directory to avoid mixing versions.')
    atomic_json(manifest_path,current_sources)
    snapshot=out/'source';snapshot.mkdir(exist_ok=True)
    for p in current_sources:shutil.copy2(p,snapshot/Path(p).name)
    shutil.copy2(__file__,snapshot/Path(__file__).name)
    atomic_json(out/'protocol.json',dict(hours_per_launch=args.hours,workers=args.workers,population_per_group=args.population,
        max_rounds=args.rounds,seed=args.seed,parameter_bounds=FIELDS,templates=templates,
        method='Feasibility-first mixed local / diagonal CEM / broad exploration; constant parameters per episode.',
        objectives='Contact-specific force, worst force, impulse, stage-goal RMSE, speed peak and joint torque peak; same fixed score as calibration.',
        limits='Finite development search, not a proof of global optimality; frozen fixture conditions, no formal test-set tuning.'))
    state_path=out/'state.json'
    if state_path.exists():state=json.loads(state_path.read_text())
    else:
        state=dict(round=0,completed=0,accepted=0,best={},history=[],started_at=time.time())
        for g in LABELS:
            row=seed_summary['selected'][g]['row'];state['best'][g]=dict(id='seed_'+g,score=row['score'],config=templates[g]['controller'],metrics=row)
    deadline=time.time()+args.hours*3600
    state.update(status='running',pid=os.getpid(),session_started_at=time.time(),deadline=deadline)
    web=ROOT/'web_demo';assets=web/'assets/vmc_auto_search_20260920';assets.mkdir(parents=True,exist_ok=True)
    def publish():
        state['updated_at']=time.time();atomic_json(state_path,state)
        compact={k:v for k,v in state.items()if k!='history'}
        atomic_json(assets/'status.json',compact)
        rows=[]
        for group,label in LABELS.items():
            best=state['best'][group];r=best['metrics'];contacts=r['contacts']
            dest=assets/group;dest.mkdir(exist_ok=True)
            atomic_json(dest/'best_controller.json',best['config']);atomic_json(dest/'best_metrics.json',r)
            group_history=[h for h in state['history'] if h['group']==group]
            feasible=[h for h in group_history if h.get('accepted')]
            front=tuning.pareto([h['metrics'] for h in feasible]) if feasible else []
            atomic_json(out/'pareto'/f'{group}.json',front)
            force=contacts[r['focus']]['peak_resultant_force_n']
            rows.append(f'<tr><td>{label}</td><td>{len(group_history)}/{len(feasible)}</td><td>{force:.1f}</td><td>{r["endpoint_error_m"]*1000:.2f}</td><td>{r["speed_p95_mps"]:.3f}/{r["speed_peak_mps"]:.3f}</td><td>{r["torque_peak_nm"]:.2f}</td><td>{best["score"]:.4f}</td><td><a href="assets/vmc_auto_search_20260920/{group}/best_controller.json">参数</a> · <a href="assets/vmc_auto_search_20260920/{group}/best_metrics.json">指标</a></td></tr>')
        body=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="60"><title>VMC 自动参数搜索</title><style>body{{max-width:1150px;margin:32px auto;padding:0 20px;font:17px/1.7 system-ui;background:#111923;color:#e2edf7}}a{{color:#8ed4ff}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;border-bottom:1px solid #405060;text-align:left;font-size:14px}}</style><h1>开放式取件工位 · VMC 自动搜索</h1><p>状态：{html.escape(state['status'])}；第 {state['round']} 轮；新增完成 {state['completed']} 回合，通过 {state['accepted']} 回合；并行上限 {args.workers}。</p><p>当前最优以已完成的可行标定结果为起点。新结果必须满足抓持、任务完成、真实目标接触、物理压入与接触力约束，才能替换。每回合参数固定，控制器不读取障碍物身份或时钟。</p><div style="overflow:auto"><table><tr><th>工况</th><th>新增尝试/通过</th><th>目标接触合力峰值 N</th><th>最终误差 mm</th><th>速度 P95/峰值 m/s</th><th>力矩 Nm</th><th>综合分↓</th><th>下载配置</th></tr>{''.join(rows)}</table></div><p>页面每 60 秒刷新。数值是当前搜索中的最好候选，不代表全局最优，也不是泛化盲测。各行工况不同，不是不同算法的同条件对比。</p><p><a href="workstation_vmc_20260920.html">查看已完成标定的工位和四组演示</a> · <a href="assets/vmc_auto_search_20260920/status.json">实时状态 JSON</a></p><p>最新写入：{time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(state['updated_at']))}（服务器时间）。过程、断点和原始轨迹保存在服务器。</p></html>'''
        temp=web/'vmc_auto_search_20260920.html.tmp';temp.write_text(body);os.replace(temp,web/'vmc_auto_search_20260920.html')
    publish()
    stop_path=out/'STOP_REQUESTED'
    def trial(spec):
        dest=out/'trials'/spec['id']/'rollout';dest.parent.mkdir(parents=True,exist_ok=True)
        result_file=dest.parent/'search_result.json'
        if result_file.exists():return json.loads(result_file.read_text())
        if time.time()>=deadline or stop_path.exists():return None
        group=spec['group'];template=templates[group];command=copy.deepcopy(template['command'])
        argv=command['argv'];argv[0]=sys.executable;argv[argv.index('--output')+1]=str(dest)
        env=command['environment'];env['CORE_VMC_CONFIG']=json.dumps(spec['config'])
        signature=dict(sources=current_sources,environment=template['environment'],argv=[x for i,x in enumerate(argv)if i not in (argv.index('--output'),argv.index('--output')+1)])
        key=hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()
        env.update(VMC_MODEL_CACHE_DIR=str(out/'model_cache'),VMC_MODEL_CACHE_KEY=key,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        atomic_json(dest.parent/'command.json',dict(argv=argv,environment=env))
        started=time.time()
        try:
            with dest.with_suffix('.log').open('w') as log:
                proc=subprocess.run(argv,cwd=ROOT,env=dict(os.environ,**env),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
            if proc.returncode:raise RuntimeError(dest.with_suffix('.log').read_text()[-1500:])
            row=assembly_metrics(dest,group,spec['id'])
            if group in ('rear','front'):
                raw=json.loads(dest.with_suffix('.json').read_text())
                row['checks']['rod_contact']=row['contacts']['push_rod_geom']['duration_s']==0.
                row['checks']['release']=raw['panel_audit']['final_rod_gap_m']>.002
                row['accepted']=all(row['checks'].values())
            result=dict(**spec,accepted=row['accepted'],metrics=row,wall_s=time.time()-started)
        except Exception as exc:result=dict(**spec,accepted=False,error=str(exc),wall_s=time.time()-started)
        atomic_json(result_file,result);return result
    try:
        while state['round']<args.rounds and time.time()<deadline and not stop_path.exists():
            if sources()!=current_sources:raise RuntimeError('Control/physics source changed while searching; stopping to preserve comparability.')
            round_number=state['round'];spec_path=out/'rounds'/f'{round_number:04d}.json'
            if spec_path.exists():specs=json.loads(spec_path.read_text())
            else:
                rng=np.random.default_rng(args.seed+round_number);specs=[]
                for group in LABELS:
                    best=state['best'][group];anchor=encode(best['config'])
                    feasible=sorted([h for h in state['history'] if h['group']==group and h.get('accepted')],key=lambda h:h['metrics']['score'])[:12]
                    elites=np.asarray([encode(h['config'])for h in feasible]+[anchor])
                    mean=elites.mean(axis=0);std=np.clip(elites.std(axis=0),.018,.16)
                    for i in range(args.population):
                        if i%5==0:
                            x=anchor.copy();indices=rng.choice(len(x),size=2,replace=False);x[indices]+=rng.normal(0,.04,2)
                        elif i%5 in (1,2):x=anchor+rng.normal(0,.025,len(anchor))
                        elif i%5==3:x=mean+rng.normal(0,std)
                        else:x=anchor+rng.normal(0,.12,len(anchor))
                        cfg=decode(np.clip(x,0,1),best['config'])
                        specs.append(dict(id=f'r{round_number:04d}_{group}_{i:02d}',group=group,config=cfg))
                atomic_json(spec_path,specs)
            seen={h['id'] for h in state['history']};complete=True
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                for future in as_completed([pool.submit(trial,s)for s in specs if s['id'] not in seen]):
                    result=future.result()
                    if result is None:complete=False;continue
                    entry={k:result[k] for k in ('id','group','config','accepted','wall_s')}
                    if 'metrics' in result:
                        entry['metrics']={k:result['metrics'][k] for k in ('score','objectives','candidate','fixture','result')}
                    if 'error' in result:entry['error']=result['error']
                    entry['result_file']=str(out/'trials'/result['id']/'search_result.json')
                    state['history'].append(entry);state['completed']+=1
                    if result['accepted']:
                        state['accepted']+=1;g=result['group'];r=result['metrics']
                        if r['score']<state['best'][g]['score']:
                            state['best'][g]=dict(id=result['id'],score=r['score'],config=result['config'],metrics=r)
                    publish()
                    print(json.dumps(dict(id=result['id'],accepted=result['accepted'],completed=state['completed'],score=result.get('metrics',{}).get('score'),error=result.get('error'))),flush=True)
            if complete:state['round']+=1
            publish()
            if not complete:break
        state['status']='stopped_by_request' if stop_path.exists() else 'completed_budget'
    except BaseException as exc:
        state['status']='error';state['error']=str(exc);raise
    finally:publish()


if __name__=='__main__':main()
