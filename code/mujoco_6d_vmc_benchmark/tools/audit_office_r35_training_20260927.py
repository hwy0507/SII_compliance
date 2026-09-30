"""Offline R35 provenance/invariant audit; never substitutes for closed loop."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    base=ROOT/'outputs/esn_office_r35_stress_20260927'
    models={'r34':base/'models/r34.npz','r35':base/'models/r35/model.npz'}
    with np.load(models['r34']) as old,np.load(models['r35']) as new:
        for k in ('win','w','leak','scale','output_gain'):
            np.testing.assert_array_equal(old[k],new[k])
    old_data=ROOT/'outputs/esn_office_recovery_20260927/r33_axis_memory/training_data.npz'
    new_data=base/'r35_training/training_data.npz'
    with np.load(old_data) as old,np.load(new_data) as new:
        np.testing.assert_array_equal(old['wrench'][:38400],new['wrench'][:38400])
        np.testing.assert_allclose(old['teacher_action'][:38400],new['teacher_action'][:38400],atol=1e-12,rtol=1e-12)
        np.testing.assert_array_equal(old['train'][:38400],new['train'][:38400])
        valid=~old['train'][:38400]
        validation={}
        for name,z in (('r34',old),('r35',new)):
            e=.5*(z['prediction'][:38400][valid]-z['teacher_action'][:38400][valid])
            validation[name]=dict(rmse=float(np.sqrt(np.mean(e*e))),by_channel=np.sqrt(np.mean(e*e,axis=0)).tolist())
    rows=[]
    for trace_path in sorted((base/'source_snapshot_v2/training_traces').glob('*.npz')):
        with np.load(trace_path) as trace:observations=trace['observation'].copy()
        teacher=SixDVirtualDynamics({});target=.5*np.array([teacher.act(o[39:45],.04) for o in observations])
        row=dict(trace=trace_path.name,sha256=sha(trace_path),samples=len(observations))
        for name,model in models.items():
            actor=OfficeVMCMemoryESN(model)
            prediction=np.array([actor.act(o) for o in observations])
            e=prediction-target
            row[name+'_rmse']=float(np.sqrt(np.mean(e*e)))
        rows.append(row)
    assert len(rows)==14
    record=dict(exact_frozen_reservoir_and_gain=True,synthetic_validation_inputs_and_labels_match=True,
                synthetic_validation=validation,development_histories=rows,
                hashes={k:sha(v) for k,v in models.items()},source_sha256=sha(Path(__file__)),
                training_data_sha256=sha(new_data),
                caveat='All14 histories are development training inputs. Offline improvement does not establish task or safety improvement; synthetic validation is not office withheld validation.')
    (base/'R35_OFFLINE_AUDIT.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Synthetic validation (deployed gain.5):',json.dumps(validation))
    for row in rows:
        print(row['trace'],row['r34_rmse'],row['r35_rmse'])


if __name__=='__main__':main()
