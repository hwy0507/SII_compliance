"""Synthetic input-isolation and whole-identity support calibration checks."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from research72_proprio_support_20261003 import features,diagnose,sha,FIELDS


class SupportTests(unittest.TestCase):
    def test_only_existing_actor_fields_and_fixed_clips(self):
        obs=np.zeros((2,48));other=obs.copy()
        other[:,sorted(set(range(48))-set(FIELDS))]=999
        np.testing.assert_array_equal(features(obs)[0],features(other)[0])
        other[0,14]=.6
        self.assertEqual(features(other)[0][0,0],4.)
        self.assertEqual(features(other)[1].tolist(),[True,False])

    def test_leave_entire_history_out_and_never_calibrate_on_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);public=root/'public';public.mkdir()
            def write(path,obj):path.write_text(json.dumps(obj))
            obs=np.zeros((5,48));obs[2:4,14]=.06;obs[4,14]=999
            data=root/'training.npz'
            np.savez(data,observation=obs,episode=[0,0,1,1,2],train=[1,1,1,1,0])
            meta=root/'metadata.json';write(meta,dict(training_data_sha256=sha(data),all_real_execution=True,
                protocol_sha256='protocol',training_identities=2,lineage=[dict(episode=0,data_role='train'),
                    dict(episode=1,data_role='train'),dict(episode=2,data_role='imitation_validation')]))
            query=np.zeros((2,48));query[:,14]=[.12,.18]
            np.savez(public/'public_observations.npz',observation=query,group=[0,0],time=[.04,.08])
            write(public/'MANIFEST.json',dict(protocol_sha256='protocol',
                observations_sha256=sha(public/'public_observations.npz'),rows=[dict(index=0,samples=2)]))
            diagnose(data,meta,public,root/'out')
            report=json.loads((root/'out/SUPPORT.json').read_text())
            self.assertEqual(report['training_samples'],4)
            self.assertEqual(report['threshold'],1.)
            self.assertEqual(report['rows'][0]['fraction_above_training_identity_loo_p95'],.5)
            with np.load(root/'out/distances.npz') as z:
                np.testing.assert_array_equal(z['training_loo'],np.ones(4))
                np.testing.assert_array_equal(z['public_distance'],[1.,2.])


if __name__=='__main__':unittest.main()
