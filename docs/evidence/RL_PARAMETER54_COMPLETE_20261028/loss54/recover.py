from pathlib import Path
import subprocess,json,time,os
os.sched_setaffinity(0,{0})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent
for name in ['audit.py','paired_gate.py']:subprocess.run([str(B/'env/bin/python'),str(OUT/name)],check=True)
(OUT/'RECOVERY_FINISHED.json').write_text(json.dumps(dict(time=time.time(),completed=True,original_failure_preserved=True)))
