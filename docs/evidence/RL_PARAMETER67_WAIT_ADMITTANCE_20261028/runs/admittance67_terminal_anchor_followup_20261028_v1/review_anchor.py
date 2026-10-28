from pathlib import Path
import hashlib
import json
import math
import os
import time
os.sched_setaffinity(0, {53})
import numpy as np
OUT = Path(__file__).parent
review = json.loads((OUT / 'ANCHOR_REVIEW.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


assert review['passed'] and sha(OUT / 'anchor66.npz') == review['anchor_sha256']
for ref in review['inputs'].values():
    assert sha(ref['path']) == ref['sha256']
with np.load(OUT / 'anchor66.npz', allow_pickle=False) as anchor, np.load(review['inputs']['values.npz']['path'], allow_pickle=False) as source:
    for key in ['indices', 'features', 'rewards', 'masks', 'denominator']:
        np.testing.assert_array_equal(anchor[key], source[key])
    np.testing.assert_array_equal(anchor['q_after'], source['q'])
    squared = anchor['masks'].astype(np.float64) * np.square(anchor['q_after'].astype(np.float64) - anchor['rewards'].astype(np.float64)[None])
    total = float(squared.sum())
    assert math.isclose(total, review['groups']['all2004']['masked_sse_after'], rel_tol=1e-12, abs_tol=1e-12)
result = dict(passed=True, time=time.time(), all2004_arrays_exact=True, independent_vector_sse=total,
              anchor_sha256=sha(OUT / 'anchor66.npz'), source_sha256=sha(Path(__file__)),
              new_network_forward=0, new_physics=0, optimizer_updates=0)
(OUT / 'ANCHOR_SAVED_REVIEW.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
