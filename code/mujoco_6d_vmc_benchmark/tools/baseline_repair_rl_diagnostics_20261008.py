"""Finite scalar summaries of official optimizer's nested diagnostic tree."""
from collections.abc import Mapping
import numpy as np


def flatten_metrics(info):
    result = {}
    def visit(value, prefix):
        if isinstance(value, Mapping):
            for key, child in value.items():
                visit(child, prefix+'/'+str(key) if prefix else str(key))
            return
        array = np.asarray(value)
        if array.dtype.kind not in 'biuf' or not array.size or not np.isfinite(array).all():
            raise ValueError('Nonfinite/nonnumeric optimizer diagnostic: '+prefix)
        if array.size == 1:
            result[prefix] = float(array.reshape(-1)[0])
        else:
            result[prefix+'/mean'] = float(array.mean())
            result[prefix+'/min'] = float(array.min())
            result[prefix+'/max'] = float(array.max())
            result[prefix+'/size'] = int(array.size)
    visit(info, '')
    if not result:
        raise ValueError('Optimizer returned no diagnostics')
    return result
