"""Independent archive-source and actual-servo bounds checks, no physics."""
import hashlib,json,tarfile
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]/'outputs/original_esn_payload_bridge_20261013'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    receipt=ROOT/'BUNDLE_AUDIT.json'
    if receipt.exists():raise FileExistsError(receipt)
    rows={}
    for arm in ('path_only','path_bridge','path_bridge_v2','path_bridge_friction_probe'):
        run=ROOT/arm/'episode';e=json.loads((run/'execution.json').read_text())
        with tarfile.open(run/'source_overlay.tar.gz') as tar:
            for name,expected in e['source_sha256'].items():
                assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==expected,name
        assert sha(run/'checkpoint.npz')==e['checkpoint_sha256']
        assert sha(run/'rollout.mjb')==e['runtime_provenance']['old_model_sha256']
        row=dict(status=e['status'],source_files_verified=len(e['source_sha256']),
            execution_sha256=sha(run/'execution.json'),source_archive_sha256=sha(run/'source_overlay.tar.gz'))
        if arm=='path_bridge':
            assert e['status']=='failed_preserved'
            row['excluded_reason']='Incorrect scale routing in initial bridge, audit caught it'
        else:
            assert e['status']=='complete'
            with np.load(run/'independent_contacts.npz') as z:
                assert float(z['external_penetration_m'].max()*1000)==e['audit']['penetration_mm']
            if arm!='path_only':
                with np.load(run/'servo_actions.npz') as z,np.load(run/'execution_chain.npz') as c:
                    f=z['fraction'];twist=np.vstack([np.zeros(6),z['yield_twist']]);scale=np.r_[1.,z['wbc_scale']]
                    np.testing.assert_array_equal(z['composition_scale'],np.ones(len(f)))
                    np.testing.assert_allclose(z['wbc_scale'],(1-f)*z['start_scale']+f*z['target_scale'],atol=1e-15)
                    np.testing.assert_array_equal(z['wbc_scale'][9::10],c['wbc_scale'])
                    np.testing.assert_array_equal(z['yield_twist'][9::10],c['yield_twist'])
                    limits=e['action_filter_config']
                    observed=dict(linear_amplitude=float(abs(twist[:,:3]).max()),angular_amplitude=float(abs(twist[:,3:]).max()),
                        linear_rate=float(abs(np.diff(twist[:,:3],axis=0)).max()/.004),
                        angular_rate=float(abs(np.diff(twist[:,3:],axis=0)).max()/.004),
                        scale_rate=float(abs(np.diff(scale)).max()/.004))
                    for key,limit in [('linear_amplitude','maximum_linear_yield_mps'),('angular_amplitude','maximum_angular_yield_radps'),
                        ('linear_rate','maximum_linear_yield_rate_mps2'),('angular_rate','maximum_angular_yield_rate_radps2'),('scale_rate','maximum_scale_rate_per_s')]:
                        assert observed[key]<=limits[limit]+1e-10
                    assert scale.min()>=limits['minimum_wbc_scale']-1e-12 and scale.max()<=1+1e-12
                    row['servo_bounds']=observed;row['feedback_not_double_applied']=True
        rows[arm]=row
    receipt.write_text(json.dumps(dict(runs=rows,auditor_sha256=sha(Path(__file__))),indent=2)+'\n')
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
