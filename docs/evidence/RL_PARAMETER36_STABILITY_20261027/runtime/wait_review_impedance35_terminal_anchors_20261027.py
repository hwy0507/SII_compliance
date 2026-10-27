from pathlib import Path
import json,os,time,subprocess,hashlib
out=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/impedance35_terminal_anchor_followup_20261027_v1');script=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/review_parameter_terminal_anchor_followup_20261027.py');os.sched_setaffinity(0,{52})
assert hashlib.sha256(script.read_bytes()).hexdigest()=='e3aef31f36c51cbc5f4eed194f510a4f6ba7eb2bc51b799a213de8e91588c513'
deadline=time.monotonic()+7200
while not (out/'REVIEW.json').exists():
 assert time.monotonic()<deadline,'Saved-review wait expired'
 assert not (out/'FAILURE.json').exists() and not (out/'WAIT_FAILURE.json').exists()
 assert Path('/proc/2103843/stat').read_text().rsplit(')',1)[1].split()[19]=='576851521','Original followup process identity lost'
 time.sleep(5)
assert json.loads((out/'REVIEW.json').read_text())['passed']
subprocess.run(['/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python',str(script),'--root',str(out)],check=True,timeout=120)
