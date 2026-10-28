"""Read saved contact scope and task transitions; no fitting or simulation.

The five prior_contact_peak channels omit the separately recorded unexpected
edge. Zero in those channels is not a no-contact state. Event summaries are
not a new integration of contact dynamics or per-substep contact replay.
"""
import argparse
import ast
import hashlib
from pathlib import Path
import tarfile

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write


def audit(output, extra=None):
    assert not output.exists()
    names=[
        'special_scene_regression_controls_20261028_v2/office_teacher_historical',
        'special_teacher_midpoint_office_20261028_v1/office_v075_avg1',
        'special_equilibrium_intent030_20261029_v1/intent030_office000',
        'special_teacher_velocity_units_20261029_v1/velocity_units_office000']
    if extra:names.append(str(extra))
    rows=[];common={}
    modules=('validate_office_apparatus_v5_20260917.py','office_task_v4_20260917.py')
    for name in names:
        folder=ROOT/'outputs'/name
        physical,review=read(folder/'rollout.json'),read(folder/'AUDIT.json')
        assert review['full_horizon']
        for file,key in (('rollout.npz','trace_sha256'),('rollout.mjb','model_sha256'),
                         ('execution_chain.npz','chain_sha256'),
                         ('rollout_metrics/substep_metrics.npz','metrics_sha256')):
            assert sha(folder/file)==review[key]
        assert review['action_replay_max_abs']==review['common_filter_replay_max_abs']==0.
        code={}
        with tarfile.open(folder/'source_overlay.tar.gz') as archive:
            for module in modules:
                matches=[n for n in archive.getnames() if n.endswith('/'+module)]
                assert len(matches)==1
                payload=archive.extractfile(matches[0]).read()
                code[module]=hashlib.sha256(payload).hexdigest()
                if module==modules[0]:
                    tree=ast.parse(payload.decode())
                    assignments=[n for n in ast.walk(tree) if isinstance(n,ast.Assign)
                        and any(isinstance(t,ast.Name) and t.id=='contact_keys' for t in n.targets)]
                    assert len(assignments)==1
                    keys=ast.literal_eval(assignments[0].value)
                    assert keys==('ball','person_hand','rod','cup','office_v5_pillar')
        signature=dict(model=review['model_sha256'],**code)
        if common:assert common==signature,'Different model or task/evaluator code'
        else:common=signature
        with np.load(folder/'rollout.npz',allow_pickle=False) as trace:
            tail=trace['prior_contact_peak'][-250:]
            assert tail.shape==(250,5)
            zero=bool(np.all(tail==0))
            last_time=float(trace['time'][-1])
            late_stage=np.unique(trace['stage'][-250:]).tolist()
        edge=physical['stats']['unexpected_edge']
        events=physical['task_events']
        assert physical['task_success']==review['task_success']
        assert physical['strict_success']==review['strict_success']
        row=dict(folder=str(folder),task=review['task_success'],strict=review['strict_success'],
            final_stage=review['stage'],task_events=events,unexpected_edge=edge,
            recorded_last_frame_s=last_time,last250_stage_ids=late_stage,
            last250_named_five_contact_channels_all_zero=zero,
            named_five_contact_channels=list(keys),
            unexpected_edge_contact_reaches_last_frame=edge['last_s'] is not None and edge['last_s']>=last_time-.04,
            hashes={n:sha(folder/n) for n in ('rollout.json','rollout.npz','AUDIT.json','source_overlay.tar.gz')})
        rows.append(row)
    output.mkdir(parents=True)
    result=dict(status='complete',rows=rows,common_model_and_evaluator_hashes=common,
        source_sha256=sha(Path(__file__)),
        conclusion='Failed office variants retain unexpected-edge contact until the horizon. Historical success clears that contact before load_transfer. Five zero disturbance channels cannot establish absence of edge contact. This localizes a persistent edge interaction, not its causal controller defect.',
        boundary='Previously inspected office000 development regression only, never unseen or fitting labels. No modified model, contacts, actor inputs, gates, or physics rerun. Event summaries do not prove uninterrupted contact or independent physical replay.')
    write(output/'REVIEW.json',result)
    print([{k:r[k] for k in ('folder','task','final_stage','unexpected_edge_contact_reaches_last_frame','last250_named_five_contact_channels_all_zero')} for r in rows])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--extra',type=Path)
    args=parser.parse_args();audit(args.output.resolve(),args.extra)
