"""Wait for the registered85-87 window; no training or automatic stop."""
from pathlib import Path
import hashlib
import json
import subprocess
import time

B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
root = Path(__file__).parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    plan = json.loads((root/'PLAN.json').read_text())
    assert plan['cycles'] == [85, 86, 87]
    source = root/'audit.py'
    assert sha(source) == plan['source_sha256']
    deadline = time.monotonic() + plan['wait_deadline_seconds']
    while True:
        complete = True
        for cycle in plan['cycles']:
            review = Path(plan['review_paths'][str(cycle)])
            for failure in review.rglob('*FAILURE.json'):
                raise RuntimeError(f'Original review failed: {failure}')
            for method in ['impedance', 'admittance', 'vmc']:
                failure = Path(plan['run_paths'][str(cycle)])/method/'train/FAILURE.json'
                assert not failure.exists(), str(failure)
            finished = review/'FINISHED.json'
            if not finished.exists():
                complete = False
            else:
                assert json.loads(finished.read_text())['completed']
                assert json.loads((review/'REVIEW.json').read_text())['passed']
        if complete:
            break
        assert time.monotonic() < deadline, 'Fixed14400-second audit wait expired; no automatic extension'
        time.sleep(5)
    reg = dict(cycles=plan['cycles'], seed=plan['bootstrap_seed'],
               bootstrap_replicates=plan['replicates'], near_zero_guard=plan['near_zero_guard'],
               relative_limit=plan['relative_limit'], source_sha256=sha(source), followup_marker=plan['followup_marker'], anchor_protocol55=plan['anchor_protocol55'], inputs={})
    assert reg['source_sha256'] == plan['source_sha256']
    for method in ['impedance', 'admittance', 'vmc']:
        for cycle in plan['cycles']:
            run = Path(plan['run_paths'][str(cycle)])/method
            review = Path(plan['review_paths'][str(cycle)])
            refs = dict(protocol=run/'REGISTRATION.json', review=review/'REVIEW.json',
                        health=review/'health/DIAGNOSIS.json', finished=review/'FINISHED.json',
                        episodes=run/'train/episodes.jsonl', optimizer=run/'train/optimizer.jsonl')
            reg['inputs'][f'{method}:{cycle}'] = {
                k: dict(path=str(p), sha256=sha(p)) for k, p in refs.items()}
    with (root/'REGISTRATION.json').open('x') as stream:
        stream.write(json.dumps(reg, indent=2)+'\n')
    subprocess.run([str(B/'env/bin/python'), str(source), '--root', str(root)], check=True)
    assert sha(root/'review_saved.py') == plan['saved_review_source_sha256']
    subprocess.run([str(B/'env/bin/python'), str(root/'review_saved.py')], check=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        (root/'WAIT_FAILURE.json').write_text(json.dumps(dict(error=repr(error), time=time.time()))+'\n')
        raise
