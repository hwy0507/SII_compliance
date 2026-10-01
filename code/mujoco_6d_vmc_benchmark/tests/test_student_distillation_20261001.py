"""Regression tests for held-out normalization and checkpoint selection."""
import sys
from pathlib import Path
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'scripts'))
import train_vmc_teacher_esn_mlp_weighted_20261001 as train
from current_student_policy_20260921 import load_current


def test_loader_uses_filtered_action_and_pins_execution_chain(tmp_path):
    root = tmp_path / "bank"; folder = root / "collection" / "x" / "vmc"; folder.mkdir(parents=True)
    obs = np.zeros((3, 48), np.float64)
    raw = np.zeros((3, 7), np.float64); filtered = raw.copy(); filtered[1, 2] = .25
    np.savez(folder / "rollout.npz", observation=obs, applied_action=raw)
    np.savez(folder / "execution_chain.npz", filtered_action=filtered)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(__import__('json').dumps({"categories": {"passive_corner": [{"folder": "collection/x/vmc", "fixture_id": "x", "model_sha256": "m"}]}}))
    rows, _ = train.base.load_rows(manifest, root)
    np.testing.assert_array_equal(rows[0]["raw_action"], raw.astype(np.float32))
    np.testing.assert_array_equal(rows[0]["action"], filtered.astype(np.float32))
    assert rows[0]["execution_chain_sha256"]


def test_validation_uses_training_normalization_and_resets_each_episode():
    rng=np.random.default_rng(16)
    training=[{'observation':rng.normal(size=(20,48)).astype(np.float32)}]
    validation=[{'observation':rng.normal(8,3,size=(13,48)).astype(np.float32)}]*2
    norm=train.esn_features(training,17)[:4]
    *actual_norm,features=train.esn_features(validation,17,norm)
    for actual,expected in zip(actual_norm,norm): np.testing.assert_array_equal(actual,expected)
    actor=train.ESN128Proprio48Action7(norm[0],norm[1],seed=17)
    expected=np.stack([actor.features(x) for x in validation[0]['observation']]).astype(np.float32)
    for f in features: np.testing.assert_array_equal(f,expected)


def test_selected_torch_model_matches_exported_inference(tmp_path):
    rng=np.random.default_rng(19)
    rows=[{'observation':rng.normal(size=(30,48)).astype(np.float32)}]
    mean,std,fmean,fstd,fs=train.esn_features(rows,23)
    y=rng.uniform(-.1,.1,(30,7)).astype(np.float32);y[:,0]=.2
    w=train.weights(rows)[0]
    for kind in ('esn','mlp'):
        x=((fs[0]-fmean)/fstd if kind=='esn' else (rows[0]['observation']-mean)/std).astype(np.float32)
        state,_,loss,pred=train.fit_model(x,y,w,x,y,w,kind,23,epochs=2)
        if kind=='esn':
            ck=train.pack_esn(state,(mean,std,fmean,fstd),train.ESN128Proprio48Action7(mean,std,23),23)
        else: ck=train.pack_mlp(state,mean,std,24)
        path=tmp_path/(kind+'.npz');np.savez_compressed(path,**ck)
        actor=load_current(path);replay=np.stack([actor.act(o) for o in rows[0]['observation']])
        np.testing.assert_allclose(replay,pred,atol=2e-6,rtol=0)
        assert abs(np.average(np.mean((replay-y)**2,axis=1),weights=w)-loss)<1e-8
        assert int(ck['seed'])==(23 if kind=='esn' else 24)


def test_training_weight_is_finite_bounded_and_ignores_other_channels():
    x=np.zeros((4,48),np.float32);x[:,39]=[0,1,10,100]
    before=train.weights([{'observation':x}])[0]
    x[:,:39]=1000;x[:,45:]=1000
    np.testing.assert_array_equal(before,train.weights([{'observation':x}])[0])
    np.testing.assert_array_equal(train.weights([{'observation':x}],0)[0],np.ones(4))
    assert np.all((before>=1)&(before<=4))
