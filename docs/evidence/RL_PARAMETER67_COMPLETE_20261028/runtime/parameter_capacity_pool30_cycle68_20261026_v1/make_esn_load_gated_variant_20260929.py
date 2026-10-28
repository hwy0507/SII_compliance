"""Build a proprioceptive recovery-gated ESN without touching environment code."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--training-manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--action-threshold',type=float,default=.05)
    p.add_argument('--gate-width',type=float,default=.10)
    p.add_argument('--attack-tau',type=float,default=.04)
    p.add_argument('--release-tau',type=float,default=.64)
    p.add_argument('--quiet-centering-tau',type=float,
                   help='Build a quiet-centered rather than directly load-gated checkpoint.')
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    manifest=json.loads(a.training_manifest.read_text())
    benchmark=Path(__file__).resolve().parents[1]
    observations=[];actions=[];trace_hashes=[]
    for case in manifest['train_cases']:
        case_root=benchmark/'outputs'/case
        trace=case_root/'rollout.npz'
        if not trace.exists():
            matches=list(case_root.glob('**/rollout.npz'))
            if len(matches)!=1:raise FileNotFoundError(f'{case}: {matches}')
            trace=matches[0]
        with np.load(trace,allow_pickle=False) as z:
            observations.append(z['observation'].astype(np.float64))
            actions.append(z['applied_action'].astype(np.float64))
        trace_hashes.append((case,sha(trace)))
    obs=np.concatenate(observations);action=np.concatenate(actions)
    load=np.linalg.norm(obs[:,32:39],axis=1);wrench=np.linalg.norm(obs[:,39:45],axis=1)
    load_scale=float(np.percentile(load,90));wrench_scale=float(np.percentile(wrench,90))
    score=np.hypot(load/load_scale,wrench/wrench_scale)
    active=np.linalg.norm(action,axis=1)>a.action_threshold
    candidates=np.linspace(0.,3.,601)
    best=None
    for center in candidates:
        pred=score>=center
        tpr=float((pred&active).sum()/max(1,active.sum()))
        tnr=float(((~pred)&(~active)).sum()/max(1,(~active).sum()))
        item=(.5*(tpr+tnr),float(center),tpr,tnr)
        if best is None or item[0]>best[0]:best=item
    with np.load(a.base,allow_pickle=False) as z:
        if str(z['contract'])!='proprio48_esn128_action7_v1':raise ValueError('Expected canonical proprio48 ESN')
        payload={key:z[key].copy() for key in z.files if key not in ('contract','metadata')}
    contract=('proprio48_esn128_action7_quiet_centered_v1' if a.quiet_centering_tau
              else 'proprio48_esn128_action7_load_gated_v1')
    metadata=dict(purpose=('quiet-state centered multiscale ESN for combined office task'
                           if a.quiet_centering_tau else 'causal load-gated recovery for combined office task'),
        forbidden_inputs=['contact truth','ball state','event time','task stage','visual/range','geometry'],
        calibration='balanced accuracy on saved teacher action activity; no combined-test labels',
        action_threshold=a.action_threshold,load_scale=load_scale,wrench_scale=wrench_scale,
        gate_center=best[1],gate_width=a.gate_width,attack_tau=a.attack_tau,
        release_tau=a.release_tau,quiet_centering_tau=a.quiet_centering_tau,
        balanced_accuracy=best[0],true_positive_rate=best[2],
        true_negative_rate=best[3],base_sha256=sha(a.base),training_manifest_sha256=sha(a.training_manifest),
        train_trace_hashes=trace_hashes)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    extra=({'centering_tau':np.float64(a.quiet_centering_tau)} if a.quiet_centering_tau else {})
    np.savez_compressed(a.output,contract=contract,
        metadata=json.dumps(metadata),**payload,gate_load_scale=np.float64(load_scale),
        gate_wrench_scale=np.float64(wrench_scale),gate_center=np.float64(best[1]),
        gate_width=np.float64(a.gate_width),gate_attack_tau=np.float64(a.attack_tau),
        gate_release_tau=np.float64(a.release_tau),**extra)
    metadata['output_sha256']=sha(a.output)
    a.output.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata))


if __name__=='__main__':main()
