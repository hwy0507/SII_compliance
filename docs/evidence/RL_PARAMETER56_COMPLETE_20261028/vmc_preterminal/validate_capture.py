from pathlib import Path
import hashlib
import json
import os
import time
os.sched_setaffinity(0, {53})
import numpy as np
import torch
torch.set_num_threads(1)
B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT = Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
snapshot = OUT/'preterminal56.pt'
health_path = B/'runs/parameter_capacity_pool30_cycle55_review_20261026_v1/health/DIAGNOSIS.json'
health = json.loads(health_path.read_text())['methods']['vmc']
parent = B/'runs/parameter_capacity_pool30_cycle55_archive_20261026_v1/vmc/cycle_00055.pt'
assert sha(parent) == health['checkpoint_sha256']
x = torch.load(snapshot, map_location='cpu', weights_only=False)
old = torch.load(parent, map_location='cpu', weights_only=False)
assert x['controller'] == old['controller'] == 'vmc' and old['cycle'] == 55
n = old['replay']['size']
assert n == 2307000 and x['steps'] == x['replay']['size'] == 2334000
a = x['replay']['arrays']
for k, v in old['replay']['arrays'].items():
    np.testing.assert_array_equal(v, a[k][:n])
old_count = int(np.count_nonzero(old['replay']['arrays']['dones'][:, 0]))
assert old_count == health['terminal_count'] == 1674
assert np.count_nonzero(a['dones'][n:, 0]) == 0
assert np.count_nonzero(a['dones'][:, 0]) == old_count
assert x['replay']['capacity'] == 4_000_000
assert x['learner']['terminal_loss_weight'] == 128
assert x['learner']['target_pair_reduction']['target'] == 'mean'
assert x['cycles'] == old['cycles']
report = dict(passed=True, time=time.time(), snapshot=str(snapshot), snapshot_sha256=sha(snapshot),
              snapshot_file_mtime=snapshot.stat().st_mtime,
              steps=x['steps'], parent55_rows=n, new56_rows=x['steps']-n,
              old_terminal_count=old_count, new56_terminal_count=0,
              parent55_replay_all_fields_exact=True, history_retained=True,
              parent55_checkpoint=dict(path=str(parent),sha256=sha(parent)),
              parent55_health=dict(path=str(health_path),sha256=sha(health_path)),
              new_physics=0, optimizer_updates=0, replay_writes=0,
              initial_wrong_impedance_count_retained_in_failure_receipt=True)
(OUT/'CAPTURE_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
