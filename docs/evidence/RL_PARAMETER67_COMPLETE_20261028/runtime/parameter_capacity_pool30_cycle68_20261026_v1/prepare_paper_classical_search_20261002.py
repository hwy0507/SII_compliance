"""Register finite classical development candidates before seeing outcomes."""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
from scipy.stats import qmc
from optimize_tool_contact_20261002 import sha, write, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--priors', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists(): raise FileExistsError(a.output)
    priors = json.loads(a.priors.read_text())
    rows = []
    for kind in ('admittance', 'impedance'):
        prior = priors['methods'][kind]
        values = prior['source_category_values']
        bounds = np.log(np.asarray(prior['bounds']))
        latin = qmc.LatinHypercube(d=len(bounds), seed=2026100301+(kind=='impedance')).random(12)
        values += np.exp(qmc.scale(latin, bounds[:, 0], bounds[:, 1])).tolist()
        for i, theta in enumerate(values):
            rows.append(dict(name=f'{kind}_{i:02d}', controller=kind, category=kind+'_development',
                             config=dict(parameters=theta)))
    vmc = []
    for factor in (.8, 1.25):
        for key, vector in [('stiffness_6d', [400,400,1200,10,8,12]),
                            ('damping_6d', [28,28,55,2.8,2.4,3.])]:
            vmc.append(dict(options={key:(np.array(vector)*factor).tolist()}))
    for gain in (1.2, 2.): vmc.append(dict(options=dict(offset_tracking_gain_6d=gain)))
    for velocity in (.5, .75): vmc.append(dict(velocity_weight=velocity))
    for i, config in enumerate(vmc):
        rows.append(dict(name=f'original_vmc_{i:02d}', category='vmc_development', config=config))
    # Interleave methods to avoid spending the entire wall budget on one family.
    rows.sort(key=lambda r:(int(r['name'].rsplit('_',1)[1]), r['category']))
    write(a.output, dict(created_utc=now(), source_sha256=sha(Path(__file__)), priors_sha256=sha(a.priors),
        candidates=rows, budgets=dict(admittance=15, impedance=15, vmc=8),
        seed=2026100301, selection='original task/strict first; among successes lower maximum penetration, then earlier stable placement, then full-horizon error integral and torque; report all Pareto tradeoffs',
        limitations='Classical 12 log-space LHS plus 3 source-category vectors; original VMC 8 one-factor perturbations around a successful development configuration. Equal budget maxima do not imply equal prior exposure. No environment or safety changes.'))


if __name__ == '__main__': main()
