"""Consolidate all bandwidth probes with parity/rate checks and raw hashes."""
import hashlib
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]


def main():
    base=ROOT/'outputs/esn_office_impact_bandwidth_20260927'
    rows=[]
    for p in sorted((base/'results').glob('*/rollout.json')):
        result=json.loads(p.read_text());meta=json.loads((p.parent/'reflex_manifest.json').read_text())
        with np.load(p.parent/'reflex_substeps.npz') as z:
            pre=z['time']<.05
            span=float(np.max(np.ptp(z['command'][pre],axis=0)))
        rows.append(dict(case=p.parent.name,penetration_mm=1000*result['stats']['max_external_penetration_m'],
            first_contact_s=result['stats']['events']['ball']['first_s'],
            peak_force_n=result['stats']['events']['ball']['peak_n'],
            reflex=meta['arguments'],rate_bounds_obeyed=meta['rate_bounds_obeyed'],
            precontact_command_span_nm=span,
            hash={name:hashlib.sha256((p.parent/name).read_bytes()).hexdigest() for name in
                  ('rollout.json','rollout.npz','reflex_manifest.json','reflex_substeps.npz')}))
    zero=next(r for r in rows if r['case']=='parity_zero')
    expected=.20737013438008847
    assert abs(zero['penetration_mm']-expected)<1e-10
    for row in rows:
        row['delta_from_zero_mm']=row['penetration_mm']-zero['penetration_mm']
        if row['case']!='parity_zero':assert row['rate_bounds_obeyed']
    record=dict(parity_pass=True,gate_mm=.2,episodes=rows,
        conclusion='All tested causal high-rate reflexes fail the unchanged .2mm gate; no first-impact reduction found. Not a proof against every conceivable controller.',
        scope='0.2s development diagnostic, not task success; no proposed ESN candidate promoted',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (base/'BANDWIDTH_RESULTS.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
