from pathlib import Path
import hashlib
import json
import math
import os
import time
os.sched_setaffinity(0, {53})
import numpy as np
OUT = Path(__file__).parent
PRIOR = OUT.parent / 'admittance66_terminal_diagnosis_20261028_v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


review = json.loads((PRIOR / 'REVIEW.json').read_text())
saved = json.loads((PRIOR / 'SAVED_REVIEW.json').read_text())
assert review['passed'] and saved['passed'] and saved['report_sha256'] == sha(PRIOR / 'REVIEW.json')
assert review['values_sha256'] == sha(PRIOR / 'values.npz')
assert not (OUT / 'anchor66.npz').exists()
with np.load(PRIOR / 'values.npz', allow_pickle=False) as values:
    assert values['features'].shape == (2004, 57) and values['q'].shape == (5, 2004)
    np.savez_compressed(OUT / 'anchor66.npz', **{k: values[k] for k in ['indices', 'features', 'rewards', 'masks', 'denominator']}, q_after=values['q'])
with np.load(OUT / 'anchor66.npz', allow_pickle=False) as anchor, np.load(PRIOR / 'values.npz', allow_pickle=False) as source:
    for key in ['indices', 'features', 'rewards', 'masks', 'denominator']:
        np.testing.assert_array_equal(anchor[key], source[key])
    np.testing.assert_array_equal(anchor['q_after'], source['q'])
    sse = math.fsum(float(anchor['masks'][h, i]) * (float(anchor['q_after'][h, i]) - float(anchor['rewards'][i])) ** 2 for h in range(5) for i in range(2004))
    assert math.isclose(sse, review['all2004_sse'], rel_tol=1e-12, abs_tol=1e-12)
result = dict(passed=True, time=time.time(), terminal_rows=2004, features_shape=[2004, 57],
              groups=dict(all2004=dict(masked_sse_after=sse)), anchor_sha256=sha(OUT / 'anchor66.npz'),
              inputs={name: dict(path=str(PRIOR / name), sha256=sha(PRIOR / name)) for name in ['PLAN.json', 'REVIEW.json', 'SAVED_REVIEW.json', 'values.npz']},
              source_sha256=sha(Path(__file__)), all2004_saved_arrays_exact=True,
              new_network_forward=0, new_physics=0, optimizer_updates=0,
              limitation='Exact saved complete66 admittance all2004 arrays and independently reviewed CPU Q; newfocus selected posthoc66, before67 completion.')
(OUT / 'ANCHOR_REVIEW.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
