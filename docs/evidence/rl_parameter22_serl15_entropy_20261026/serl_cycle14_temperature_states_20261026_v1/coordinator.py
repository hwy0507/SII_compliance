from pathlib import Path
import json,time,subprocess,os,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent;os.sched_setaffinity(0,{54})
reg=json.loads((out/'REGISTRATION.json').read_text());profile=Path(reg['required_pure_formal_profile']);deadline=time.monotonic()+1800
while not profile.exists() or Path(f"/proc/{reg['profile_pid']}").exists():
 if time.monotonic()>deadline:raise TimeoutError('Original pure-formal profile pending; do not start GPU diagnostic')
 time.sleep(2)
p=json.loads(profile.read_text());assert len(p['samples'])==180 and all(v['original_live_all_samples'] for v in p['summary'].values())
(out/'PROFILE_PREREQUISITE.json').write_text(json.dumps(dict(path=str(profile),sha256=hashlib.sha256(profile.read_bytes()).hexdigest()))+'\n')
source=B/'runtime'/out.name/'diagnose_serl_temperature_state_20261026.py'
subprocess.run([str(B/'serl_env/bin/python'),str(source),'--registration',str(out/'REGISTRATION.json'),'--output',str(out)],check=True)
(out/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),completed=True,convergence_claim=False))+'\n')
