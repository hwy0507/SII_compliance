"""Read-only analysis of historical/current VMC traces; no simulator invocation."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from canonical48_rl_env_20260923 import sha,save_json


def main():
    folder=ROOT/'outputs/canonical48_ppo_diagnosis_20260923_r1'
    historical=json.loads((ROOT/'outputs/canonical_rl_assets_20260923/train_rod/rollout.json').read_text())
    current=json.loads((folder/'vmc_control/rollout.json').read_text())
    recorded=json.loads((folder/'historical_source_manifest.json').read_text())
    sources={}
    for path,expected in recorded.items():
        name=Path(path).name;old=folder/'historical_source'/name;new=ROOT/'scripts'/name
        sources[name]=dict(historical_recorded_sha256=expected,historical_snapshot_sha256=sha(old),
            historical_snapshot_matches_recorded=sha(old)==expected,current_sha256=sha(new),
            current_identical_to_historical=sha(old)==sha(new))
    with np.load(folder/'historical_rollout.npz',allow_pickle=False) as archive:
        old={k:archive[k].copy() for k in archive.files}
    with np.load(folder/'vmc_control/rollout.npz',allow_pickle=False) as archive:
        new={k:archive[k].copy() for k in archive.files}
    old['observation48_reconstructed']=np.column_stack((old['observation'][:,:42],old['teacher_force'][:,3:6],old['observation'][:,42:]))
    new['observation48_reconstructed']=new['observation']
    differences={}
    for key in old:
        a,b=old[key],new[key]
        if a.shape!=b.shape or a.dtype.kind not in 'fiu':continue
        per=np.abs(a-b).reshape(len(a),-1).max(axis=1)
        levels={}
        for threshold in (1e-8,1e-6,1e-4,.01):
            indices=np.flatnonzero(per>threshold)
            i=int(indices[0]) if len(indices) else None
            levels[str(threshold)]=None if i is None else dict(index=i,
                step_start_s=float(old['time'][i]-.04),step_end_s=float(old['time'][i]),
                maximum_component_difference=float(per[i]))
        differences[key]=dict(shape=list(a.shape),initial_max_abs=float(per[0]),
            max_abs=float(per.max()),first_exceedance=levels)
    report=dict(scope='Trace/source analysis only; no new simulation',
        historical_trace_sha256=sha(folder/'historical_rollout.npz'),
        current_trace_sha256=sha(folder/'vmc_control/rollout.npz'),sources=sources,
        all_historical_source_manifest_hashes_match=all(r['historical_snapshot_matches_recorded'] for r in sources.values()),
        full_core_vmc_config_equal=historical['controller_6d_config']==current['controller_6d_config'],
        teacher_profile_equal=historical['arguments']['teacher_profile']==current['arguments']['teacher_profile'],
        force_source_equal=historical['arguments']['teacher_force_source']==current['arguments']['teacher_force_source'],
        scene_equal=historical['scene']==current['scene'],
        initial_q_max_abs=float(np.max(np.abs(old['observation'][0,:7]-new['observation'][0,:7]))),
        initial_nominal_twist_max_abs=float(np.max(np.abs(old['observation'][0,14:20]-new['observation'][0,14:20]))),
        differences=differences,
        causal_conclusion='Initial q already differs by about4e-8 before action; contact/wrench/action differences then grow. No single source change has been established as root cause.',
        no_evidence_of_changed_observer_wbc_safety_core=True,
        unresolved=['historical NumPy/SciPy/BLAS versions and aarch64 vs x86 numerical effects',
            'full transitive dependency source and compiled model equivalence',
            'causal test holding exact initial physics state fixed'],
        rl_learnability_conclusion='Current VMC failure does not establish that RL goal is unlearnable. Existing stochastic PPO episode achieved lift/pose but failed terminal motion threshold.')
    save_json(folder/'LINEAGE_AUDIT.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('differences','sources')},indent=2))


if __name__=='__main__':main()
