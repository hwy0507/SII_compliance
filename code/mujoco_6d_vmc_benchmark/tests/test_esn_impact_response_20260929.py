import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from current_student_policy_20260921 import ImpactResponseProprio48ESN
def test_impact_response_checkpoint(tmp_path):
    z=dict(mean=np.zeros(48),std=np.ones(48),win=np.zeros((128,49)),w=np.zeros((128,128)),leak=np.ones(128),input_mask=np.ones(48),alpha=np.float64(1),output_gain=np.float64(1),fmean=np.zeros(176),fstd=np.ones(176),w1=np.zeros((128,176)),b1=np.zeros(128),route_w2=np.zeros((7,128)),route_b2=np.r_[0.,np.ones(6)],impact_w2=np.zeros((7,128)),impact_b2=np.r_[0.,-np.ones(6)],impact_scale=np.float64(.12),impact_center=np.float64(.8),impact_width=np.float64(.2),impact_attack_tau=np.float64(.04),impact_release_tau=np.float64(.16),impact_hold_tau=np.float64(.64))
    p=tmp_path/'x.npz';np.savez_compressed(p,contract='proprio48_esn128_action7_impact_response_v1',**z);a=ImpactResponseProprio48ESN(p);quiet=np.zeros(48);hit=quiet.copy();hit[7]=1.;q=a.act(quiet);h=a.act(hit);assert np.isfinite(h).all();assert a.impact_gate>0
