from pathlib import Path
import hashlib,json,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R=B/'repository/SII_compliance';OUT=R/'docs/evidence/rl_parameter18_exploration_20261026';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
records=[]
def copy(p,rel):
    data=p.read_bytes();target=OUT/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    h=hashlib.sha256(data).hexdigest();assert sha(p)==h==sha(target)
    records.append(dict(source=str(p),destination=str(target.relative_to(R)),sha256=h,bytes=len(data)))
names=['parameter_batch65536_cycle17_review_20261026_v1','parameter_cycle17_loss_summary_20261026_v1','parameter_batch65536_cycle18_20261026_v1','parameter_batch65536_cycle18_review_20261026_v1','serl_cycle12_constant_noise_representatives_20261026_v1','parameter_pool30_preparation_20261026_v1','batch13_parameter18_gpu_profile_20261026_v1','serl_multistep_batch65536_cycle13_review_deadline_guard_20261026_v1']
for name in names:
    root=B/'runs'/name
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(root)
        if len(rel.parts)>3 or any(part in rel.parts for part in ['train','__pycache__']):continue
        if 'evaluation' in rel.parts and p.name not in ['EVALUATION.json','EXTERNAL_ACTION_RNG_GATE.json','POLICY_UNCHANGED.json','RESULTS.json']:continue
        if p.suffix in ['.json','.png','.py'] or (len(rel.parts)==1 and p.name.endswith('_value_return.npz')):
            assert p.stat().st_size<15_000_000;copy(p,Path(name)/rel)
        elif p.name=='check_only.log':copy(p,Path(name)/rel.with_suffix('.txt'))
for name in ['prepare_parameter18_20261026.py','setup_parameter18_monitors_20261026.py','prepare_serl12_constant_noise_20261026.py','guard_direct13_review_deadline_20261026.py','check_parameter_pool30_20261026.py',Path(__file__).name]:copy(B/'runtime'/name,Path('preparation_sources')/name)
for name in ['evaluate_serl_seeded_multistep_20261026.py','parameter_shared_sampler_pool_20261026.py']:copy(R/'code/mujoco_6d_vmc_benchmark/tools'/name,Path('candidate_sources')/name)
copy(B/'runtime/serl_cycle12_constant_noise_representatives_20261026_v1/evaluate_serl_seeded_multistep_20261026.py',Path('frozen_evaluation_source/evaluate_serl_seeded_multistep_20261026.py'))
status=dict(time=time.time(),processes={},progress={},gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv'],text=True))
for pid in [2652800,2652802,2652804,1280297,2652915,2652985,1328360,1328362,1328394,2542683,2680231,2427730,2427731,2872195]:
    p=Path('/proc')/str(pid);status['processes'][str(pid)]=dict(alive=p.exists(),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode() if p.exists() else None)
for m in ['impedance','admittance','vmc']:status['progress'][m]=read(B/'runs/parameter_batch65536_cycle18_20261026_v1'/m/'train/PROGRESS.json')
status['progress']['direct']=read(B/'runs/serl_multistep_batch65536_cycle13_20261026_v1/direct/PROGRESS.json')
write(OUT/'LIVE_STATUS.json',status)
profile=B/'runs/batch13_parameter18_gpu_profile_20261026_v1/PROFILE.json'
if profile.exists():
    d=read(profile);assert len(d['samples'])==180;write(OUT/'GPU_PROFILE_SUMMARY.json',{k:v for k,v in d.items() if k!='samples'})
write(OUT/'SOURCES.json',dict(time=time.time(),files=records,copied_files=len(records),large_artifacts='Full state/replay/raw physics SSD only; HDD quota prevents full backup; no verified arm1 copy'))
print(json.dumps(dict(copied_files=len(records),bytes=sum(v['bytes'] for v in records),output=str(OUT))))
