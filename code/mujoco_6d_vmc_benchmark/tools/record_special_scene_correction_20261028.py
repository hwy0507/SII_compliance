"""Record superseded diagnostic runs without rewriting historical execution."""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    runs=[ROOT/'outputs'/f'special_scene_test_shard{i}_20261028_v1' for i in range(4)]
    runs += [ROOT/'outputs'/f'special_scene_vmc_actions_20261028_v{i}' for i in (1,2)]
    runs += [ROOT/'outputs/video_reference_vmc_20261028_v5']
    runs += sorted((ROOT/'outputs').glob('special_scene_rod_dev*_20261028'))
    rows=[];manifest={}
    for run in runs:
        record=dict(path=str(run),role='diagnostic_only_not_main_result',receipts=[])
        for path in sorted(run.rglob('*.json')):
            # Capture execution and scientific results, not frozen source trees.
            if any(x in path.relative_to(run).parts for x in ('source','physics_source','configs')): continue
            if path.name not in ('execution.json','progress.json','legacy.json','teacher.json','recipe.json',
                                 'MODEL_LOCK.json','DATA_COMPLETE.json','REGISTRATION.json','AUDIT.json',
                                 'INDEPENDENT_AUDIT.json','ROD_YIELD_REJOIN_AUDIT.json','ROD_YIELD_REJOIN_AUDIT_V2.json','ROD_YIELD_REJOIN_AUDIT_V3.json'): continue
            relative=Path(run.name)/path.relative_to(run)
            target=out/'receipts'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
            manifest[str(relative)]=dict(sha256=sha(path),bytes=path.stat().st_size)
            record['receipts'].append(str(relative))
        record['finished_rollouts']=[str(p.parent.relative_to(run)) for p in sorted(run.rglob('rollout.json')) if 'source' not in p.parts]
        rows.append(record)
    result=dict(schema='special-scene-correction-receipt-v1',created_utc=datetime.now(timezone.utc).isoformat(),
                status='correction_in_progress_no_qualified_main_dataset',runs=rows,files=manifest,
                diagnostic_dispatch_stop=dict(coordinators=[629828,629838,629856,629846],
                    action='SIGSTOP coordinators only; observed all four children Z after natural completion; TERM then CONT coordinators',
                    final_worker_pids=[636104,637204,637334,638015],
                    historical_execution_files_unchanged=True,
                    limitation='Coordinator state may still say running and omit its final child; use child receipts, do not resume old four-way dispatch'),
                known_errors=['v1 rod audit wrong hardcoded trigger/retract-end and pass=rejoin',
                              'three demonstration traces, invalid scene split and unqualified corner in v2 dataset',
                              '12 ESN candidates vs4 neural candidates in diagnostic fits',
                              'environment variables did not enforce memory limits; four concurrent local evaluators',
                              'v4 partial evaluation was interrupted mid-episode before correction; failures retained',
                              'shards duplicated earlier diagnostic condition000 results',
                              'dev09 wrapper source changed after launch; diagnostic only',
                              'dev10 failed before physics: optional cgroup cpu.max was absent'])
    (out/'INDEX.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(output=str(out),files=len(manifest),runs=len(rows),index_sha256=sha(out/'INDEX.json'))))


if __name__=='__main__':main()
