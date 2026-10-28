"""Report the fixed completed budget and training signals, retaining all failures."""
import argparse
import json
from pathlib import Path
import sys
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from canonical48_rl_env_20260923 import save_json,sha
from diagnose_canonical48_ppo_20260923 import trace_diagnostics


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/canonical48_ppo_8192_20260923_r2')
    args=parser.parse_args();folder=args.output
    final=json.loads((folder/'COMPLETE.json').read_text())
    if final['status']!='complete':raise RuntimeError('Budget/evaluation not complete')
    training=[];partial=[];steps=0
    for episode in sorted((folder/'train').glob('episode_*')):
        trace=episode/'actor_trace.npz'
        with np.load(trace,allow_pickle=False) as archive:count=len(archive['action'])
        steps+=count
        if (episode/'partial_episode.json').exists():
            partial.append(dict(path=str(episode),samples=count,scored=False));continue
        result=json.loads((episode/'rollout.json').read_text())
        detail=trace_diagnostics(episode)
        training.append(dict(episode=episode.name,samples=count,duration_s=result['duration_s'],
            task_success=result['success'],invalid_physics=result['invalid_physics'],
            upstream_contact=result.get('upstream_contact',False),lift_m=result['lift_m'],
            endpoint_error_m=result['endpoint_error_m'],reward_total=detail['reward_total'],
            reward_terms=detail['reward_terms'],phase_counts=detail['phase_counts'],
            slowdown_mean=detail['slowdown_mean'],slowdown_zero_fraction=detail['slowdown_zero_fraction']))
    data=json.loads(zipfile.ZipFile(folder/'ppo_final.zip').read('data'))
    manifest=json.loads((folder/'manifest.json').read_text())
    entrypoint=Path(manifest['argv'][0])
    if not entrypoint.is_absolute():entrypoint=ROOT/entrypoint
    snapshot=entrypoint.parents[1]
    changed_sources=[name for name,expected in manifest['source_hashes'].items()
        if sha(snapshot/name)!=expected]
    if sha(entrypoint)!=manifest['runner_hash']:changed_sources.append(str(entrypoint))
    checkpoints={p.stem:json.loads(p.read_text()) for p in sorted((folder/'checkpoints').glob('*.json'))}
    report=dict(complete=final,checkpoint_metadata={k:data[k] for k in ('num_timesteps','_n_updates','seed')},
        archived_train_samples=steps,training_episodes=training,partial_episodes=partial,
        complete_train_episodes=len(training),training_task_successes=sum(r['task_success'] for r in training),
        training_invalid_episodes=sum(r['invalid_physics'] for r in training),periodic_checkpoints=checkpoints,
        final_model_sha256=sha(folder/'ppo_final.zip'),normalizer_sha256=sha(folder/'vecnormalize_train_only.pkl'),
        source_snapshot=str(snapshot),changed_snapshot_sources=changed_sources,
        source_snapshot_unchanged=not changed_sources,
        interpretations=['Training episode scores are on-policy exploratory signals, not frozen-policy evaluation.',
            'All completed/invalid/partial episodes retained; no validation-based selection.',
            'Local development metrics must not be merged into DGX matched-physics tables.'])
    if steps!=8192 or data['num_timesteps']!=8192 or data['_n_updates']!=384:
        raise AssertionError('Fixed budget accounting mismatch')
    if changed_sources:raise AssertionError('Running source snapshot changed')
    save_json(folder/'TRAINING_REPORT.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('complete','training_episodes','periodic_checkpoints')},indent=2))


if __name__=='__main__':main()
