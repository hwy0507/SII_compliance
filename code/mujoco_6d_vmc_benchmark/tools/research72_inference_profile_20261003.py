"""Replay known training observations for capacity/latency accounting, no fitting.

Actor-only NumPy wall time excludes WBC, physics, filtering, loading and reset.
Timing does not certify real-time deadlines and never selects a checkpoint.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
from office_context_network_20261003 import OfficeContextNetwork
from office_mlp_rnn_20261002 import OfficeMLPRNN


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--metadata',type=Path,required=True)
    parser.add_argument('--learning',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    assert all(os.environ.get(k)=='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'))
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    limit=(cg/'memory.max').read_text().strip()
    assert limit!='max' and int(limit)<=3*1024**3
    metadata=read(args.metadata);assert sha(args.data)==metadata['training_data_sha256']
    assert metadata['lineage'][0]['data_role']=='train'
    with np.load(args.data) as z:
        indices=np.flatnonzero(z['episode']==0)
        observations=z['observation'][indices].copy()
    assert observations.shape==(1375,48)
    models=[]
    for folder in args.learning:
        assert read(folder/'execution.json')['status']=='complete'
        spec=read(folder/'SPECIFICATION.json')
        assert spec['data_sha256']==metadata['training_data_sha256']
        models.extend((job,folder/job['name']) for job in spec['jobs'])
    # Stable shuffled interleaving, instead of timing all instances of one
    # family together. Three complete reset-at-episode sequence passes.
    order=np.random.default_rng(2026100373).permutation(len(models))
    args.output.mkdir(parents=True,exist_ok=False);rows=[];timings={}
    for index in order:
        job,folder=models[index];cp=folder/'checkpoint.npz';meta=read(folder/'TRAINING_COMPLETE.json')
        assert sha(cp)==meta['checkpoint_sha256']
        with np.load(cp) as z:
            contract=str(z['contract'])
            shapes={k:list(z[k].shape) for k in z.files if z[k].ndim>=2}
        cls={OfficeVMCMemoryESN.contract:OfficeVMCMemoryESN,
             OfficeContextNetwork.contract:OfficeContextNetwork,
             OfficeMLPRNN.contract:OfficeMLPRNN}[contract]
        actor=cls(cp);core=getattr(actor,'core',actor)
        if cls==OfficeMLPRNN:
            trainable=actor.input_w.size+actor.output_w.size+(actor.recurrent_w.size if actor.kind=='rnn' else 0)
            fixed=actor.scale.size
        else:
            trainable=core.weights.size-core.context_dimension*7
            fixed=core.win.size+core.w.size+core.leak.size+core.scale.size
            fixed+=core.context_gate_w.size if core.context_gate_w is not None else 0
            if cls==OfficeContextNetwork:
                learned_hidden=core.win.size+(core.w.size if actor.kind=='rnn' else 0)
                trainable+=learned_hidden;fixed-=learned_hidden
        if 'trainable_parameters' in meta:
            assert trainable==meta['trainable_parameters']
        with np.load(folder/'exported_replay.npz') as z:
            expected=z['prediction'][indices].copy()
        actor.reset();warm=np.asarray([actor.act(o) for o in observations])
        maximum=float(np.max(np.abs(warm-expected)))
        assert maximum<1e-11
        latency=[]
        for repeat in range(3):
            actor.reset()
            for obs in observations:
                start=time.perf_counter_ns();action=actor.act(obs);latency.append(time.perf_counter_ns()-start)
        timings[job['name']]=np.asarray(latency,dtype=np.int64)
        us=np.asarray(latency)/1000.
        rows.append(dict(name=job['name'],family=job['family'],seed=job['seed'],
            checkpoint=str(cp),checkpoint_sha256=sha(cp),training_metadata_sha256=sha(folder/'TRAINING_COMPLETE.json'),
            trainable_coefficients=trainable,fixed_numeric_coefficients=fixed,stored_matrix_shapes=shapes,
            replay_max_abs=maximum,samples=len(us),median_us=float(np.median(us)),p95_us=float(np.percentile(us,95)),
            p99_us=float(np.percentile(us,99)),max_us=float(us.max())))
    np.savez_compressed(args.output/'latency_ns.npz',**timings)
    source=[Path(__file__),ROOT/'scripts/office_vmc_memory_esn_20260927.py',
            ROOT/'scripts/office_context_network_20261003.py',ROOT/'scripts/office_mlp_rnn_20261002.py']
    result=dict(created_utc=datetime.now(timezone.utc).isoformat(),host=platform.node(),python=sys.executable,
        numpy=np.__version__,platform=platform.platform(),memory_max=limit,rows=rows,
        data_sha256=sha(args.data),data_metadata_sha256=sha(args.metadata),
        input_identity=metadata['lineage'][0]['condition_id'],physics_steps=0,training_updates=0,
        latency_trace_sha256=sha(args.output/'latency_ns.npz'),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in source},
        caveats=['Actor-only single-thread wall latency includes Python timing overhead; not end-to-end control or hard real-time.',
                 'Width128 does not mean equal trainable parameters or arithmetic.',
                 'Fixed numeric count includes stored recurrent coefficients even when memoryless reset makes them inactive; matrix shapes disclosed.',
                 'Same known training identity for timing/parity only. No architecture or weight is chosen by latency.'])
    for p in source:
        (args.output/p.name).write_bytes(p.read_bytes())
    (args.output/'PROFILE.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(models=len(rows),profile_sha256=sha(args.output/'PROFILE.json'))))


if __name__=='__main__':
    main()
