"""Selection/locking regressions: no heldout read and no silent method fallback."""
import copy
import tempfile
from pathlib import Path
from unittest.mock import patch
import evaluate_baseline_repair_20261008 as evaluation
from continue_baseline_repair_campaign_20261008 import score
from office_v7_uniform24_20261008 import read,write,sha,FAMILIES


def main():
    with tempfile.TemporaryDirectory(prefix='sii-repair-lock-') as temporary:
        root=Path(temporary);source=root/'source';source.mkdir()
        reference=[dict(family=f,name=f,config={}) for f in FAMILIES]
        write(root/'REFERENCE_MODELS.json',dict(candidates=reference))
        write(root/'PROTOCOL.json',dict(reference_models_sha256=sha(root/'REFERENCE_MODELS.json')))
        models=root/'models.json';write(models,dict(candidates=reference))
        # No sealed/HELDOUT exists: freeze must finish before any such access.
        with patch.object(evaluation,'validate_candidate'):
            evaluation.freeze(root,models,source)
        assert read(root/'FINAL_MODEL_LOCK.json')['status']=='frozen'
        try:evaluation.freeze(root,models,source)
        except AssertionError:pass
        else:raise AssertionError('Model lock can be overwritten')
    for family in ('direct_metric','parameter_impedance'):
        try:evaluation.validate_candidate(dict(family=family,name='bad',parameter_source='/unused'))
        except (KeyError,AssertionError):pass
        else:raise AssertionError('RL family silently became a teacher/nominal actor')
    base=dict(strict_success=False,task_success=False,full_horizon=True,stages={'0':1,'4':1},
        penetration_mm=0.,rmse_mm=1.,peak_torque_nm=1.,placement_distance_m=.1)
    good=copy.deepcopy(base);good.update(strict_success=True,task_success=True,rmse_mm=50.,peak_torque_nm=60.)
    assert score([good])>score([base]), 'Low-force failure must not beat a strict success'
    dropped=copy.deepcopy(base);dropped.update(stages={'7':1},placement_distance_m=.25)
    assert score([base])>score([dropped]), 'Empty-handed retreat must not masquerade as payload progress'
    print('PASS: freeze-before-unseal, immutable lock, missing RL adapter rejected, success-first/payload-aware ranking')


if __name__=='__main__':main()
