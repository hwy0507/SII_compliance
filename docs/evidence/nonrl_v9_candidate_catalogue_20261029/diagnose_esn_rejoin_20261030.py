"""Read-only ESN rod00 diagnosis; no integration, fitting, or final test access."""
import argparse
from pathlib import Path
import numpy as np
from diagnose_v9_rod_rejoin_margin_20261030 import summarize
from collect_special_scene_actions_20261028 import ROOT, read, sha, write

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
plan = read(ROOT/'outputs/special_scene_direction_collection_20261029_v9/COLLECTION_PLAN.json')
teacher = Path(next(e['folder'] for e in plan['episodes'] if e['id']=='rod_00'))
b = ROOT/'outputs/nonrl_v9_common_eligibility_20261029_v3/evaluations'
folders = [('teacher', teacher),
 ('esn_seed01_rank1_failed', ROOT/'outputs/nonrl_v9_paired_scene_priority_20261029_v5/rod_00_esn_ridge/rod'),
 ('esn_seed01_rank2_rod_passed_ball09_failed', b/'esn_ridge_s2026102801_rank2/rod_00/rod'),
 ('esn_seed01_rank3_failed', b/'esn_ridge_s2026102801_rank3/rod_00/rod'),
 ('esn_seed02_rank1_passed', b/'esn_ridge_s2026102802_rank1/rod_00/rod')]
rows = [summarize(label, folder) for label, folder in folders]
for row in rows[1:]:
 assert row['model_sha256'] == rows[0]['model_sha256']
 np.testing.assert_array_equal(row['first_observation'], rows[0]['first_observation'])
write(a.output, dict(status='same_identity_esn_development_rejoin_diagnosis_no_physics', rows=rows,
 same_initial_canonical48_and_mjb=True, source_sha256=sha(Path(__file__)),
 imported_diagnostic_sha256=sha(ROOT/'tools/diagnose_v9_rod_rejoin_margin_20261030.py'),
 limitations=['Different closed-loop histories; not a common-input accuracy ranking.',
 'First crossing until retract is diagnostic, not a replacement for original per-sample behavior gating.',
 'No integration, fitting, final test access, or proof of teacher recovery on failed student histories.']))
print([(r['label'],r['qualified'],r['best_transverse_error_m'],r['saturation_fraction']) for r in rows])
