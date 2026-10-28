"""Register a small proprioceptive progress-decayed VMC recovery study."""
import argparse
from pathlib import Path
from optimize_tool_contact_20261002 import sha,write,now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    rows=[]
    for lift in (.02,.035,.05):
        for distance in (.02,.06):
            config=dict(recovery=dict(threshold_n=.5,attack_s=.12,release_s=1.,offset_m=lift,
                gain_per_s=4.,velocity_mps=.12,activation_mode='progress',progress_distance_m=distance))
            rows.append(dict(name=f'recovery_lift{lift}_distance{distance}',category='vmc_development',config=config))
    write(a.output,dict(created_utc=now(),source_sha256=sha(Path(__file__)),candidates=rows,
        purpose='Teacher-only causal active recovery around unchanged original VMC, not passive safety or an ESN hybrid',
        input='Existing estimated wrench, reference-relative error and measured/commanded motion; no event clock, contact truth, obstacle identity or world geometry',
        selection='task/strict first, then safety margin and efficiency/Pareto diagnostics; all failures retained',
        limitation='Different structural prior from passive classical controllers; register as a stronger model-based baseline. No online use by pure ESN. Counts against VMC development budget.'))


if __name__=='__main__':main()
