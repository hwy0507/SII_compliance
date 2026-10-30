"""Versioned deployment loader that adds the audited wide office MLP contract."""
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from current_student_policy_20260921 import load_current as _load_legacy


def load_current(path):
    with np.load(path, allow_pickle=False) as archive:
        contract = str(archive['contract'])
    if contract == 'proprio48_office_mlp_rnn_v2':
        from office_mlp_rnn_20261002 import OfficeMLPRNN
        return OfficeMLPRNN(path)
    return _load_legacy(path)
