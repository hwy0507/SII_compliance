"""Audit all72 top3 archived development horizons against dispatch registration."""
import argparse
from pathlib import Path
from collect_special_scene_actions_20261028 import ROOT,read,sha,write
from audit_special_scene_metrics_v2_20261030 import horizon
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
b=Path(__file__).resolve().parent;index=b/'TOP3_RAW_CASE_INDEX_20261030.json';d=read(index)
reg=ROOT/'outputs/nonrl_v9_common_eligibility_20261029_v3/REGISTRATION.json';r=read(reg)
references={e['identity']:e for e in r['references']}
rows=[]
for case in d['cases']:
 reference=references[case['identity']]
 # Duration comes from the original registered dispatch, not the saved clock.
 scene=reference['scene']
 # Same independently specified 20/30/13s horizons as the frozen final runner.
 # Rod also verifies the explicit registration override, not observed clock.
 expected={'rod':20.,'ball':30.,'corner':13.}[scene]
 if scene=='rod':assert float(reference['parameters']['VMC_SCENE_DURATION_S'])==expected
 assert sha(ROOT/'tools/run_video_reference_coverage_20261029.py')==r['source_sha256']['tools/run_video_reference_coverage_20261029.py']
 result=horizon(Path(case['source_folder']),expected)
 rows.append(dict(family=case['family'],seed=case['seed'],rank=case['rank'],identity=case['identity'],scientifically_qualified=case['qualified'],**result))
assert len(rows)==72
write(a.output,dict(status='all72_registered_horizons_checked' if all(r['full_episode_completed'] for r in rows) else 'incomplete_episodes_preserved',rows=rows,
 case_index_sha256=sha(index),registration_sha256=sha(reg),source_sha256=sha(Path(__file__)),auditor_sha256=sha(ROOT/'tools/audit_special_scene_metrics_v2_20261030.py'),
 final_test_performed=False,limitations=['Full duration does not convert scientific failures into success.','Development raw only; not final unseen108.', 'Ball30/corner13 are independently specified audit horizons matching source/default recipe, not claimed explicit registration overrides.']))
print(len(rows),sum(r['full_episode_completed'] for r in rows))
