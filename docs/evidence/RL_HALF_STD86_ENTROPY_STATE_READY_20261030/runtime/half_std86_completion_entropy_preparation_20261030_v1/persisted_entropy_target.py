"""Preparation only: exact-parent migration and persistent SAC entropy target.

This adapter does not choose a scientific target or launch training. A future
protocol must bind the target, action dimension and exact parent learner digest,
and require this loader in trainers, evaluators and health diagnostics.
"""
import copy
import math

KEY = 'registered_entropy_target'

def entropy_class(base, *, target, dimension, parent_digest, allow_parent=False):
    if type(dimension) is not int or dimension not in (5, 7):
        raise ValueError('Parameter action dimension must be5 or7')
    if type(target) not in (int, float) or not math.isfinite(target):
        raise ValueError('Finite explicit target entropy required')
    if not isinstance(parent_digest,str) or len(parent_digest)!=64 or any(c not in '0123456789abcdef' for c in parent_digest):
        raise ValueError('Exact parent learner SHA256 digest required')
    expected = dict(version=1, target_entropy=float(target), action_dimension=dimension,
                    migration_parent_learner_digest=parent_digest,
                    applies_to='native SAC autotune alpha objective; no actor forward override')
    class EntropyLearner(base):
        def __init__(self,*args,**kwargs):
            if kwargs.get('dimension')!=dimension or kwargs.get('direct') is not False or kwargs.get('algorithm')!='cheq':
                raise ValueError('Registered parameter CHEQ interface required')
            super().__init__(*args,**kwargs)
            self._entropy_restored=False
        def _entropy_guard(self):
            if not self._entropy_restored or self.learner.target_entropy!=float(target):
                raise ValueError('Unrestored or drifted entropy target')
        def load_state_dict(self,state):
            from validate_published_finite_check_20261025 import digest
            if KEY in state:
                if state[KEY]!=expected:
                    raise ValueError('Cannot change persisted entropy protocol')
            elif not allow_parent or digest(state)!=parent_digest:
                raise ValueError('Only the exact explicitly registered parent may migrate')
            stripped=dict(state);stripped.pop(KEY,None)
            super().load_state_dict(stripped)
            # Preserve native integer metadata for the unchanged -dimension case.
            self.learner.target_entropy=-dimension if float(target)==-dimension else float(target)
            self._entropy_restored=True
        def state_dict(self):
            self._entropy_guard()
            out=super().state_dict();out[KEY]=copy.deepcopy(expected)
            return out
        def update(self,arrays):
            self._entropy_guard()
            result=super().update(arrays)
            # Cached metrics may describe the preceding policy update on odd
            # steps; the applied target is explicit even before its next update.
            result['registered_entropy_target/applied']=float(target)
            return result
    return EntropyLearner
