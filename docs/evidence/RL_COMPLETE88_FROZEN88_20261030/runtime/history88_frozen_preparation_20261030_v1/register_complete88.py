"""Create final frozen88 registrations only after complete scientific review.

No physics dispatch. Run evaluator --check-only for each final registration next.
"""
from pathlib import Path
import json,time
from frozen_helpers import sha
D=Path(__file__).resolve().parent;B=D.parents[1]
R=B/'runs/parameter88_history_frozen_full30_20261030_v1'
O=B/'runs/parameter_history_cycle88_review_20261030_v2'
read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def validate_inputs():
    plan=read(R/'PRE_REGISTRATION.json')
    assert plan['parent_cycle']==88 and plan['automatic_evaluation'] is False
    assert read(D/'UPDATED_FROZEN_REVIEW.json')['passed']
    required=[O/'FINISHED.json',O/'REVIEW.json',O/'health/DIAGNOSIS.json',O/'loss/REVIEW.json',O/'PLOT_INSPECTION.json']
    absent=[str(p) for p in required if not p.exists()]
    if absent:raise ValueError('Complete88 scientific prerequisites absent: '+', '.join(absent))
    assert read(required[0])['completed'] and read(required[1])['passed'] and read(required[3])['passed']
    health=read(required[2]);review=read(required[1]);loss=read(required[3]);plots=read(required[4])
    assert health['cycle']==88 and health['optimizer_updates_performed']==0
    assert plots['actual_visual_inspection'] is True
    expected_plots=[O/'health/training_diagnostics.png',O/'loss/loss88.png']
    for path in expected_plots:
        item=next(p for p in plots['plots'] if p['path']==str(path))
        assert item['inspected'] is True and item['sha256']==sha(path)
    assert loss['plot_sha256']==sha(expected_plots[1])
    registrations={}
    for method,original in plan['methods'].items():
        reg=dict(original);cp=Path(reg['checkpoint']);cp_sha=sha(cp)
        assert cp_sha==review['methods'][method]['checkpoint_sha256']==health['methods'][method]['checkpoint_sha256']
        assert loss['methods'][method]['rows']==41250 and loss['methods'][method]['all_finite']
        assert sha(reg['training_registration'])==reg['training_registration_sha256']
        for name,h in reg['source_hashes'].items():assert sha(D/name)==h
        protocol=read(reg['training_registration'])
        assert protocol['history_critic_amendment']['binding']==reg['history_binding']
        journal=B/'runs/parameter_history_cycle88_20261030_v2'/method/'train/cycle_00088'/reg['gate_case_id']/'actor_intervals.jsonl'
        assert journal.is_file()
        reg.update(checkpoint_sha256=cp_sha,required_review_sha256=sha(required[1]),
            gate_observations=str(journal),gate_observations_sha256=sha(journal),
            prospective_plan_sha256=sha(R/'PRE_REGISTRATION.json'),
            scientific_prerequisites=[dict(path=str(p),sha256=sha(p)) for p in required])
        registrations[method]=reg
    return registrations

def main():
    registrations=validate_inputs()
    # All three inputs pass before creating any final registration.
    for method in registrations:assert not (R/method).exists()
    for method,reg in registrations.items():
        folder=R/method;folder.mkdir();put(folder/'REGISTRATION.json',reg)
    put(R/'REGISTERED.json',dict(time=time.time(),methods=list(registrations),
        physical_steps=0,optimizer_updates=0,exact_restore_check_only_still_required=True,
        explicit_launch_receipt_still_required=True))
if __name__=='__main__':main()
