from pathlib import Path
import json,time,subprocess
p=Path(__file__).parent
out=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/serl_cycle16_actor_floor_physical_prefix_20261026_v1')
end=time.monotonic()+3600
while not (out/'REVIEW.json').exists():
 assert not (out/'FAILURE.json').exists(), 'Original physical probe failed'
 assert time.monotonic()<end
 time.sleep(5)
subprocess.run(['/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python',str(p/'review_serl_actor_floor_physical_prefix_20261026.py'),'--run',str(out)],check=True)
