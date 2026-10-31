from pathlib import Path
import hashlib

def check_fixed_report(aggregate, row, method, checkpoint_sha256, values_path):
    # Per-method fixed-terminal reports do not have a passed field.
    assert aggregate['passed'] is True
    assert row == aggregate['methods'][method]
    assert row['checkpoint_sha256'] == checkpoint_sha256
    assert row['full_learner_optimizer_replay_rng_unchanged'] is True
    assert row['saved_scalar_arithmetic_verified'] is True
    with Path(values_path).open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == row['values_sha256']
    return True
