from pathlib import Path
import json,os,subprocess,time,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
name='parameter_capacity_pool30_cycle24_20261026_v1';out=B/'runs'/name;rt=B/'runtime'/name
archive=B/'runs/parameter_capacity_pool30_cycle24_archive_20261026_v1';view=B/'runs'/(archive.name+'_view');view.mkdir()
launch=json.loads((out/'LAUNCH.json').read_text())
for m in ['impedance','admittance','vmc']:(view/m).symlink_to(out/m/'train')
(view/'LAUNCH.json').write_text(json.dumps(launch,indent=2)+'\n')
oldreview=B/'runs/parameter_pool30_cycle23_review_20261026_v1';review=B/'runs/parameter_capacity_pool30_cycle24_review_20261026_v1';review.mkdir()
def adapt(s):
 return s.replace('parameter_pool30_cycle23','parameter_capacity_pool30_cycle24').replace('cycle_00023','cycle_00024').replace("['cycle']==23","['cycle']==24").replace("'--cycle','23'","'--cycle','24'").replace('Cycle23 archive','Cycle24 archive')
imports="sys.path.insert(0,str(B/'runtime/parameter_capacity_pool30_cycle24_20261026_v1'))\nfrom parameter_replay_capacity_20261026 import MARKER as CAPACITY_MARKER\n"
checks="assert x['replay']['capacity']==2_000_000 and x['replay']['replay_capacity_extension']==CAPACITY_MARKER\n    assert old['replay']['capacity']==1_000_000 and 'replay_capacity_extension' not in old['replay']\n    assert x['replay']['size']==x['replay']['cursor']==x['steps'] and x['steps']>1_000_000\n    "
for src in oldreview.glob('*.py'):
 s=adapt(src.read_text())
 if src.name=='review.py':
  s=s.replace('from spt_rl_reward_20261025 import SPTReward',imports+'from spt_rl_reward_20261025 import SPTReward')
  s=s.replace("assert x['cycle']==24",checks+"assert x['cycle']==24")
  s=s.replace('new_transitions=len(transitions),','replay_capacity_extension=CAPACITY_MARKER, replay_size=x[\'replay\'][\'size\'], crossed_original_capacity=True, new_transitions=len(transitions),')
 ast.parse(s);(review/src.name).write_text(s)
s=adapt((B/'runs/parameter_pool30_cycle23_20261026_v1/startup_review.py').read_text())
s=s.replace('from spt_rl_reward_20261025 import SPTReward',imports+'from spt_rl_reward_20261025 import SPTReward')
s=s.replace(" assert x['steps']>old['steps']", " assert x['replay']['capacity']==2_000_000 and x['replay']['replay_capacity_extension']==CAPACITY_MARKER and x['replay']['cursor']==x['replay']['size']\n assert old['replay']['capacity']==1_000_000 and 'replay_capacity_extension' not in old['replay']\n assert x['steps']>old['steps']")
s=s.replace('added_steps=x[\'steps\']-old[\'steps\'],','added_steps=x[\'steps\']-old[\'steps\'],replay_capacity_extension=CAPACITY_MARKER,')
ast.parse(s);(out/'startup_review.py').write_text(s)
boundary=s.replace("/'startup';OUT.mkdir", " /'capacity_boundary';OUT.mkdir").replace('time.monotonic()+300','time.monotonic()+1500')
boundary=boundary.replace(' while not cp.exists():'," while not (cp.exists() and (run/'PROGRESS.json').exists() and json.loads((run/'PROGRESS.json').read_text())['steps']>=1_001_000):")
boundary=boundary.replace(" assert x['steps']>old['steps']", " assert x['steps']>=1_001_000\n assert x['steps']>old['steps']")
ast.parse(boundary);(out/'capacity_boundary_review.py').write_text(boundary)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
def start(cmd,log):
 with log.open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 return dict(pid=p.pid,time=time.time(),command=cmd)
monitors={}
monitors['startup']=start([str(B/'env/bin/python'),str(out/'startup_review.py')],out/'startup_review.log')
monitors['capacity_boundary']=start([str(B/'env/bin/python'),str(out/'capacity_boundary_review.py')],out/'capacity_boundary_review.log')
monitors['archive']=start([str(B/'env/bin/python'),str(rt/'archive_published_cycle_checkpoints_20261025.py'),'--run',str(view),'--output',str(archive)],out/'archive.log')
monitors['review']=start([str(B/'env/bin/python'),str(review/'coordinator.py')],review/'driver.log')
(out/'MONITORS.json').write_text(json.dumps(monitors,indent=2)+'\n');print({k:v['pid'] for k,v in monitors.items()})
