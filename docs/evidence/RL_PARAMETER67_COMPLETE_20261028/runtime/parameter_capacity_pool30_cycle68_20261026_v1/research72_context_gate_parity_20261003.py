"""No-fit NumPy/Torch fixed-gate parity and input-contract engineering check."""
import argparse,json
from pathlib import Path
import numpy as np
import torch
from train_paper_feature_matched_network_20261003 import Network,ROOT,sha,write,now,OfficeVMCMemoryESN


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('learning','data','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);torch.set_num_threads(1)
    with np.load(a.data) as z:obs=z['observation'][:400].copy()
    rows=[]
    for kind,parent in [('rnn','esn_2026100301_point'),('mlp','memoryless_2026100301')]:
        for gated in (False,True):
            actor=OfficeVMCMemoryESN(a.learning/parent/'checkpoint.npz')
            if gated:actor.context_gate_w=np.random.default_rng(2026140301).normal(0,1,(128,12))
            force=np.clip(obs[:,39:45]/actor.scale,-12,12)
            context=np.c_[np.clip(np.c_[obs[:,14:17]/.06,obs[:,26:29]/.06,obs[:,45:48]],-4,4),np.clip(obs[:,20:23]/.08,-4,4)]
            load=np.c_[force,np.abs(force)];cross=(load[:,:,None]*context[:,None,:]).reshape(len(obs),-1)
            drive=np.c_[load,cross]
            model=Network(actor,kind,np.ones(actor.weights.shape[0]))
            expected=np.asarray([actor.act(o) for o in obs]);actor.reset()
            with torch.no_grad():actual=model(*[torch.from_numpy(v)[None] for v in (drive,force,cross,context)])[0][0].numpy()
            maximum=float(np.max(np.abs(actual-expected)));assert maximum<1e-11
            assert 'context_gate_w' not in dict(model.named_parameters())
            zero=obs.copy();zero[:,39:45]=0.
            np.testing.assert_array_equal(np.asarray([actor.act(o) for o in zero]),np.zeros((len(zero),7)))
            actor.reset();reference=np.asarray([actor.act(o) for o in obs]);actor.reset()
            changed=obs.copy();fields=set(range(14,17))|set(range(20,23))|set(range(26,29))|set(range(39,48))
            changed[:,sorted(set(range(48))-fields)]=123.
            np.testing.assert_array_equal(np.asarray([actor.act(o) for o in changed]),reference)
            rows.append(dict(kind=kind,gated=gated,max_abs_error=maximum,zero_equilibrium=True,unused_field_isolation=True,gate_trainable=False))
    result=dict(completed_utc=now(),source_sha256={str(f.relative_to(ROOT)):sha(f) for f in [Path(__file__),
        ROOT/'tools/train_paper_feature_matched_network_20261003.py',ROOT/'scripts/office_vmc_memory_esn_20260927.py']},
        physics_steps=0,gradient_updates=0,rows=rows)
    write(a.output/'PARITY.json',result);print(json.dumps(result))


if __name__=='__main__':main()
