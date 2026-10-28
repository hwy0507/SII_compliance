"""Engineering-only fixed state/context interactions; zero fits or physics.

Random probe readout coefficients are used solely to exercise export/parity.
They are not candidate trained policies and must never enter evaluation.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import numpy as np
import torch
from train_paper_feature_matched_network_20261003 import Network,ROOT,sha,write,now,OfficeVMCMemoryESN


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('learning','data','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);torch.set_num_threads(1)
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'))
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip();assert memory!='max' and int(memory)<=3*1024**3
    with np.load(a.data) as z:obs=z['observation'][:400].copy()
    rows=[]
    for kind,parent in [('rnn','esn_2026100301_point'),('mlp','memoryless_2026100301')]:
        for gated in (False,True):
            actor=OfficeVMCMemoryESN(a.learning/parent/'checkpoint.npz')
            if gated:actor.context_gate_w=np.random.default_rng(123).normal(0,1,(128,12))
            actor.state_context_readout_w=np.random.default_rng(456).normal(0,1/np.sqrt(12),(128,12))
            extra=np.random.default_rng(789).normal(0,.01,(128,7))
            actor.weights=np.r_[actor.weights[:-12],extra,actor.weights[-12:]]
            force=np.clip(obs[:,39:45]/actor.scale,-12,12)
            context=np.c_[np.clip(np.c_[obs[:,14:17]/.06,obs[:,26:29]/.06,obs[:,45:48]],-4,4),np.clip(obs[:,20:23]/.08,-4,4)]
            load=np.c_[force,np.abs(force)];cross=(load[:,:,None]*context[:,None,:]).reshape(len(obs),-1)
            drive=np.c_[load,cross]
            model=Network(actor,kind,np.ones(552))
            expected=np.asarray([actor.act(o) for o in obs]);actor.reset()
            args=[torch.from_numpy(v)[None] for v in (drive,force,cross,context)]
            with torch.no_grad():actual=model(*args)[0][0].numpy()
            maximum=float(np.max(np.abs(actual-expected)));assert maximum<1e-11
            assert 'state_context_readout_w' not in dict(model.named_parameters())
            assert model.state_context_readout_w.requires_grad is False
            expected_trainable=3780+128*156+(128*128 if kind=='rnn' else 0)
            assert sum(p.numel() for p in model.parameters() if p.requires_grad)-84==expected_trainable
            # Export a disposable probe through the real loader. Never save it
            # as a training-complete artifact or attach it to a candidate spec.
            with np.load(a.learning/parent/'checkpoint.npz') as z:values={k:z[k].copy() for k in z.files}
            values.update(weights=actor.weights,state_context_readout_w=actor.state_context_readout_w)
            if gated:values['context_gate_w']=actor.context_gate_w
            probe=a.output/f'ENGINEERING_ONLY_{kind}_{gated}.npz';np.savez_compressed(probe,**values)
            loaded=OfficeVMCMemoryESN(probe)
            np.testing.assert_array_equal(np.asarray([loaded.act(o) for o in obs]),expected)
            actor.reset();zero=obs.copy();zero[:,39:45]=0.
            np.testing.assert_array_equal(np.asarray([actor.act(o) for o in zero]),np.zeros((len(zero),7)))
            actor.reset();reference=np.asarray([actor.act(o) for o in obs]);actor.reset()
            fields=set(range(14,17))|set(range(20,23))|set(range(26,29))|set(range(39,48))
            changed=obs.copy();changed[:,sorted(set(range(48))-fields)]=123.
            np.testing.assert_array_equal(np.asarray([actor.act(o) for o in changed]),reference)
            response_delta=None
            if kind=='rnn' and not gated:
                # Identical stored state and zero current load, differing only
                # in allowed reference-relative position error. State dynamics
                # are identical; the new readout can respond immediately.
                one=copy.deepcopy(actor);two=copy.deepcopy(actor)
                one.state=two.state=np.ones(128)*.2
                one.state=one.state.copy();two.state=two.state.copy()
                o1=np.zeros(48);o2=o1.copy();o2[22]=.04
                out1=one.act(o1);out2=two.act(o2)
                np.testing.assert_array_equal(one.state,two.state)
                response_delta=float(np.max(np.abs(out1-out2)));assert response_delta>1e-6
            rows.append(dict(kind=kind,gated=gated,max_abs_error=maximum,export_exact=True,
                zero_equilibrium=True,unused_field_isolation=True,projection_trainable=False,
                esn_trainable_readout=3780,matched_trainable_parameters=expected_trainable,
                same_state_zero_load_context_response_delta=response_delta,
                engineering_probe_sha256=sha(probe),engineering_probe_not_a_candidate=True))
    sources=[Path(__file__),ROOT/'tools/train_paper_feature_matched_network_20261003.py',
             ROOT/'scripts/office_vmc_memory_esn_20260927.py']
    result=dict(completed_utc=now(),argv=sys.argv,physics_steps=0,training_updates=0,new_fits=0,
        data_sha256=sha(a.data),source_sha256={str(f.relative_to(ROOT)):sha(f) for f in sources},rows=rows,
        limitation='Synthetic coefficients test implementation and expressiveness only, not fit quality, physical success or superiority.')
    for f in sources:(a.output/f.name).write_bytes(f.read_bytes())
    write(a.output/'PARITY.json',result);print(json.dumps(dict(rows=rows,output=str(a.output))))


if __name__=='__main__':
    main()
