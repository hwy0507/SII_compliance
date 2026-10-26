"""Pin completed learning diagnostics, draw unsmoothed loss, freeze seen grid."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from run_nonrl_spt_matrix_20261025 import read, write, sha, now, load_diagnostic_models


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('parent','constant','cosine','output'):
        parser.add_argument('--'+key,type=Path,required=True)
    a = parser.parse_args()
    out = a.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    data_hash = sha(a.parent/'data/training_data.npz')
    fits = []; models = []
    for schedule,root in (('constant',a.constant.resolve()),('cosine',a.cosine.resolve())):
        state = read(root/'execution.json')
        assert state['status'] == 'complete' and state['completed'] == state['expected']
        shutil.copy2(root/'execution.json',out/(schedule+'_execution.json'))
        shutil.copy2(root/'REGISTRATION.json',out/(schedule+'_REGISTRATION.json'))
        for job in state['jobs']:
            directory = root/job['name']; meta_path = directory/'TRAINING_COMPLETE.json'
            meta = read(meta_path)
            assert sha(meta_path) == job['completion_sha256']
            assert sha(directory/'checkpoint.npz') == meta['checkpoint_sha256']
            assert meta['training_data_sha256'] == data_hash
            assert meta.get('learning_rate_schedule','constant') == schedule
            label = f"{job['family']}_{schedule}_{job['updates']}"
            shutil.copy2(meta_path,out/(label+'.json'))
            fits.append(dict(label=label,schedule=schedule,**{k:v for k,v in job.items() if k != 'command'},
                             metadata_sha256=sha(meta_path),history=meta['history']))
            if job['updates'] == 32000:
                models.append(dict(name=label,family=job['family'],seed=job['seed'],worker_kind='office',config={},
                                   checkpoint=str(directory/'checkpoint.npz'),checkpoint_sha256=meta['checkpoint_sha256'],
                                   metadata=str(meta_path),metadata_sha256=sha(meta_path),
                                   selected_update=meta['selected_update'],validation_mse=meta['validation_mse'],
                                   group='matched_'+schedule+'_32000'))
    original = read(a.parent/'MODEL_LOCK.json')
    ridge = next(m for m in original['models'] if m['name'] == 'esn_ridge_s2026101301')
    assert sha(Path(ridge['checkpoint'])) == ridge['checkpoint_sha256']
    models.append(dict(ridge,group='analytic_auxiliary'))
    lock = dict(schema='sii-nonrl-learning-diagnostic-lock-v1',status='frozen',created_utc=now(),
                training_data_sha256=data_hash,models=models,
                comparison='Three shared-data same-seed families at constant/cosine 32k, plus analytic ESN auxiliary. No selection by closed-loop scores; all seven evaluated on all eight already-seen conditions. Per-fit checkpoint chosen only by imitation validation. One global T_ref within this new grid; do not compare raw SPT with the old grid without a common reference.',
                physical_budget=dict(methods=7,conditions=8,episodes=56,concurrent_workers=1,threads=1,
                                     memory_max_bytes=3*1024**3,swap_max_bytes=0,horizon_s=55,physics_dt_s=5e-5))
    write(out/'MODEL_LOCK.json',lock); load_diagnostic_models(out/'MODEL_LOCK.json')
    free = shutil.disk_usage(a.parent.resolve().parent).free
    required = 56*192*1024**2 + 1024**3
    write(out/'PHYSICS_PREFLIGHT.json',dict(created_utc=now(),status='admitted' if free>=required else 'blocked_storage',
                                          execution_started=False,free_bytes=free,required_bytes=required,
                                          estimate='192 MiB per episode (previous maximum about 152 MiB) plus 1 GiB reserve',
                                          model_lock_sha256=sha(out/'MODEL_LOCK.json')))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(15,8),sharex=True)
    for column,family in enumerate(('esn_gradient','rnn_scratch','mlp_scratch')):
        for fit in [f for f in fits if f['family'] == family]:
            x=[h['update'] for h in fit['history']]
            label=f"{fit['schedule']} {fit['updates']//1000}k"
            for row,key in enumerate(('full_train_objective','validation_mse')):
                axes[row,column].plot(x,[h[key] for h in fit['history']],label=label,linewidth=1.5)
        for row in (0,1):
            axes[row,column].set_yscale('log'); axes[row,column].grid(alpha=.25)
            axes[row,column].set_title(family); axes[row,column].legend(fontsize=8)
        axes[1,column].set_xlabel('Optimizer updates')
    axes[0,0].set_ylabel('Full-train weighted raw objective + ridge')
    axes[1,0].set_ylabel('Validation clipped action MSE')
    fig.suptitle('Fresh non-RL learning diagnostics | same data / seed | no smoothing\nOffline loss is not task success; snapshots every 1,000 updates')
    fig.tight_layout(); fig.savefig(out/'learning_repair_loss.png',dpi=160); plt.close(fig)
    write(out/'SUMMARY.json',dict(created_utc=now(),data_sha256=data_hash,
                                source_sha256=sha(Path(__file__)),fits=fits,
                                model_lock_sha256=sha(out/'MODEL_LOCK.json')))
    print(json.dumps({f['label']:{k:f[k] for k in ('validation_mse','last4_full_train_relative_range','diagnostic_plateau')} for f in fits},indent=2))


if __name__ == '__main__':
    main()
