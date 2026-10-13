"""Controls that would catch false matched/RNN, export or split claims."""
import copy
import numpy as np
import pytest
import torch

from train_fair_students_20261013 import (
    initial_actor, encoded, history_features, RawNetwork, bounded, export, check_split, FIELDS)
from fair_comparison_20261013 import selection, FAMILIES, SEEDS, RATES


@pytest.mark.parametrize('family', ['esn_gradient', 'rnn_scratch', 'mlp_scratch'])
def test_deployment_and_gradient(family, tmp_path):
    torch.set_num_threads(1)
    rng = np.random.default_rng(72); obs = rng.normal(0, .02, (45, 48)); obs[:, 39:45] *= 30
    ep = np.repeat([0, 1, 2], 15)
    actor = initial_actor(42)
    f = history_features(actor, obs, ep); norm = np.maximum(f[:30].std(0), .005)
    actor.weights = rng.normal(0, .0001, (552, 7))/norm[:, None]; actor.weights[-12:] = 0
    model = RawNetwork(actor, 'mlp' if family == 'mlp_scratch' else 'rnn', norm)
    if family == 'esn_gradient':model.win.requires_grad_(False);model.echo.requires_grad_(False)
    inputs = [torch.from_numpy(x[:15])[None] for x in encoded(obs,actor.scale)]
    prediction, _ = model(*inputs)
    loss = (prediction-.1).square().mean(); loss.backward()
    expected = ['coeff'] if family == 'esn_gradient' else ['win','coeff'] if family == 'mlp_scratch' else ['win','echo','coeff']
    assert {n for n,p in model.named_parameters() if p.requires_grad} == set(expected)
    for n,p in model.named_parameters():
        if n in expected:assert torch.isfinite(p.grad).all() and p.grad.norm() > 0
    # An actual optimizer update must change each declared learned matrix.
    before = copy.deepcopy(model.state_dict())
    torch.optim.Adam([p for p in model.parameters() if p.requires_grad],lr=1e-4).step()
    for n,p in model.named_parameters():assert bool(torch.any(p != before[n])) == (n in expected)
    np.testing.assert_array_equal(model.coeff.detach().numpy()[-12:], 0)
    deployed = export(model, actor, family, tmp_path/'checkpoint.npz')
    with torch.no_grad():raw = model(*inputs)[0][0].numpy()
    actions = np.array([deployed.act(o) for o in obs[:15]])
    np.testing.assert_allclose(actions,bounded(raw),atol=1e-12,rtol=1e-12)
    deployed.reset();other=export(model,actor,family,tmp_path/'other.npz')
    for o in obs:
        altered=o.copy();altered[sorted(set(range(48))-set(FIELDS))]=999
        np.testing.assert_array_equal(deployed.act(o),other.act(altered))
    deployed.reset()
    for o in obs:
        o=o.copy();o[39:45]=0;np.testing.assert_array_equal(deployed.act(o),0)


def test_no_clamp_dead_gradient():
    actor=initial_actor(8);actor.weights[:6]=1e3
    model=RawNetwork(actor,'rnn',np.ones(552))
    obs=np.ones((3,48)); inputs=[torch.from_numpy(x)[None] for x in encoded(obs,actor.scale)]
    raw,_=model(*inputs);assert raw.abs().max()>1
    raw.square().mean().backward();assert model.coeff.grad.norm()>0


def test_reject_identity_leakage_and_noncontiguous_history():
    check_split(np.array([0,0,1,1]),np.array([1,1,0,0],bool))
    with pytest.raises(AssertionError):check_split(np.array([0,0,1,1]),np.array([1,0,1,0],bool))
    with pytest.raises(AssertionError):check_split(np.array([0,1,0,2]),np.array([1,0,1,0],bool))


def test_selection_keeps_every_seed_and_does_not_exclude_update_zero():
    rows=[dict(family=f,seed=s,rate=r,validation_mse=(0 if r==.0001 else 1),selected_update=0)
          for f in FAMILIES for s in SEEDS for r in ([None] if f=='esn_ridge' else RATES)]
    chosen=selection(rows)
    assert len(chosen)==15
    for f in FAMILIES:assert {r['seed'] for r in chosen if r['family']==f}==set(SEEDS)
    with pytest.raises(ValueError):selection(rows[:-1])
