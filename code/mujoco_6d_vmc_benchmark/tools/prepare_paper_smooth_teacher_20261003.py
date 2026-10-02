"""Register causal teacher readout smoothing, with unmodified virtual mechanics."""
import argparse
from pathlib import Path
from optimize_tool_contact_20261002 import write,sha,now

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise FileExistsError(a.output)
rows=[]
for velocity in (0.,.25,.5,.75):
    for pair in (False,True):
        rows.append(dict(name=f'smooth_velocity{velocity}_pair{int(pair)}',category='vmc_development',
                         config=dict(velocity_weight=velocity,pair_average=pair)))
rows.append(dict(name='smooth_velocity1_pair1',category='vmc_development',config=dict(velocity_weight=1.,pair_average=True)))
write(a.output,dict(created_utc=now(),source_sha256=sha(Path(__file__)),candidates=rows,
                   limitation='Teacher-only causal readout ablation; static compliance and common filter unchanged; not a closed-loop safety guarantee. Counts against original 48-teacher physical budget.'))
