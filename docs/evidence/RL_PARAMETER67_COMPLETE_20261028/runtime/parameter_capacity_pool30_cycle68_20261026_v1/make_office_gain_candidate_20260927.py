"""One fixed global action-gain candidate, preserving parent and lineage."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--gain',type=float,required=True)
    a=p.parse_args()
    if not 0<a.gain<=1:raise ValueError('Gain in (0,1] required')
    a.output.parent.mkdir(parents=True,exist_ok=False)
    with np.load(a.parent,allow_pickle=False) as z:fields={k:z[k].copy() for k in z.files}
    original_metadata=json.loads(str(fields.get('metadata','{}')))
    record=dict(parent=str(a.parent),parent_sha256=hashlib.sha256(a.parent.read_bytes()).hexdigest(),
        output_gain=a.gain,reason='Fixed global attenuation for load-transfer residual bias, identical in every scene; no event/stage gate',
        original_training_metadata=original_metadata,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    fields['output_gain']=a.gain;fields['metadata']=json.dumps(record)
    np.savez_compressed(a.output,**fields)
    record['checkpoint_sha256']=hashlib.sha256(a.output.read_bytes()).hexdigest()
    (a.output.parent/'lineage.json').write_text(json.dumps(record,indent=2))
    print(record['checkpoint_sha256'])


if __name__=='__main__':main()
