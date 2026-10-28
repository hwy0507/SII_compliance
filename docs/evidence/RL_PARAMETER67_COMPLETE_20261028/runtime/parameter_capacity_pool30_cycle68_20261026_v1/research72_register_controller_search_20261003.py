"""Outcome-blind finite teacher/classical candidate registration on two dev IDs."""
import argparse
import copy
from datetime import datetime,timezone,timedelta
import hashlib
import json
import math
from pathlib import Path
import random


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lhs(seed,bounds,count):
    rng=random.Random(seed);columns=[]
    for lo,hi in bounds:
        strata=list(range(count));rng.shuffle(strata)
        columns.append([math.exp(math.log(lo)+(math.log(hi)-math.log(lo))*(i+rng.random())/count) for i in strata])
    return list(zip(*columns))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--priors',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    protocol=json.loads((a.root/'PROTOCOL.json').read_text());priors=json.loads(a.priors.read_text())
    assert datetime.now(timezone.utc)<datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48)
    teacher=json.loads((a.root/'teacher.json').read_text());candidates=[]
    teacher_keys=['threshold_n','attack_s','release_s','offset_m','gain_per_s','velocity_mps','progress_distance_m']
    teacher_bounds=[(.25,1.),(.06,.24),(.5,1.5),(.025,.045),(2.5,5.5),(.08,.16),(.012,.04)]
    variants=[teacher]
    for values in lhs(2026100373,teacher_bounds,11):
        config=copy.deepcopy(teacher);config['recovery'].update(dict(zip(teacher_keys,values)));variants.append(config)
    for i,config in enumerate(variants):
        candidates.append(dict(name=f'teacher_{i:02d}',category='enhanced_teacher',config=config))
    for index,method in enumerate(('admittance','impedance','vmc')):
        prior=priors['methods'][method]
        values=[prior['center'],*lhs(2026100374+index,prior['bounds'],11)]
        for i,value in enumerate(values):
            candidates.append(dict(name=f'{method}_{i:02d}',category='classical_'+method,controller=method,config=dict(parameters=list(value))))
    assert len(candidates)==48
    result=dict(registered_utc=datetime.now(timezone.utc).isoformat(),protocol_sha256=sha(a.root/'PROTOCOL.json'),
        source_sha256=sha(Path(__file__)),baseline_priors_sha256=sha(a.priors),
        conditions=['development_000','development_001'],candidates=candidates,
        budgets=dict(candidates_per_family=12,screen_episodes=96,advance_per_family=2,confirmation_conditions=8,maximum_confirmation_episodes=64),
        sampling='One existing center plus 11 deterministic log-uniform Latin-hypercube candidates per family. No development or heldout outcomes read by registration.',
        teacher_keys=teacher_keys,teacher_bounds=teacher_bounds,
        selection='Per family: descending strict count, descending task count, ascending worst external/edge penetration, ascending mean full-horizon RMSE, ascending mean peak actuator torque, lexical name. Speed reported, never maximized. All early aborts retained and rank below full-horizon candidates with same success counts.',
        confirmation='Evaluate top two per family on all eight registered development identities, then freeze one by the same rule. Repeated screen conditions not independent new tests.',
        roles='Development only. These outcome-informed configurations are not assessed on final heldout identities until all methods freeze.',
        unchanged=['controller equations except explicit bounded parameters','environment','gates','actor inputs','actuator limits'])
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(candidates=len(candidates),episodes=96,sha256=sha(a.output))))


if __name__=='__main__':main()
