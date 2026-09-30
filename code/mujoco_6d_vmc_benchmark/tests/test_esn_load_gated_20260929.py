import sys
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from current_student_policy_20260921 import LoadGatedProprio48ESN,QuietCenteredProprio48ESN


def checkpoint(path):
    rng=np.random.default_rng(7)
    np.savez_compressed(path,contract='proprio48_esn128_action7_load_gated_v1',
        mean=np.zeros(48),std=np.ones(48),win=np.zeros((128,49)),w=np.zeros((128,128)),
        leak=np.ones(128),input_mask=np.ones(48),alpha=np.float64(1),output_gain=np.float64(1),
        fmean=np.zeros(176),fstd=np.ones(176),w1=np.zeros((128,176)),b1=np.zeros(128),
        w2=np.zeros((7,128)),b2=np.r_[0.,np.ones(6)],gate_load_scale=np.float64(1),
        gate_wrench_scale=np.float64(1),gate_center=np.float64(.64),gate_width=np.float64(.1),
        gate_attack_tau=np.float64(.04),gate_release_tau=np.float64(.64))


def test_load_gate_attacks_and_recovers(tmp_path):
    path=tmp_path/'model.npz';checkpoint(path);actor=LoadGatedProprio48ESN(path)
    quiet=np.zeros(48);loaded=quiet.copy();loaded[39]=2.
    q0=actor.act(quiet);active=actor.act(loaded);after=actor.act(quiet)
    assert np.linalg.norm(active)>np.linalg.norm(q0)
    assert np.linalg.norm(after)<np.linalg.norm(active)
    assert actor.state.shape==(128,)


def test_quiet_centering_removes_constant_bias_but_freezes_under_load(tmp_path):
    path=tmp_path/'centered.npz';checkpoint(path)
    with np.load(path,allow_pickle=False) as z: payload={k:z[k] for k in z.files if k!='contract'}
    np.savez_compressed(path,contract='proprio48_esn128_action7_quiet_centered_v1',
                        **payload,centering_tau=np.float64(.16))
    actor=QuietCenteredProprio48ESN(path);quiet=np.zeros(48);loaded=quiet.copy();loaded[39]=2.
    initial=np.linalg.norm(actor.act(quiet))
    for _ in range(30): late=np.linalg.norm(actor.act(quiet))
    assert late<initial*.1
    before=actor.quiet_baseline.copy();actor.act(loaded)
    assert np.linalg.norm(actor.quiet_baseline-before)<.05
