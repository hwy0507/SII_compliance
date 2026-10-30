"""Persist the explicitly registered target-pair estimator across resumes."""
from published_exact_projected_learner_20261026 import exact_class
from published_target_pair_mean_20261026 import install


def marker(reduction):
    if reduction not in ('minimum', 'mean'):
        raise ValueError('Unsupported target-pair reduction')
    return dict(version=1, target=reduction, actor='minimum', sampled_targets=2)


def pair_class(base, reduction):
    expected = marker(reduction)
    class PairLearner(exact_class(base)):
        def load_state_dict(self, state):
            if state.get('target_pair_reduction', expected) != expected:
                raise ValueError('Cannot silently change persisted pair estimator')
            super().load_state_dict(state)
            self.pair_reduction_receipt = install(self, reduction == 'mean')

        def state_dict(self):
            state = super().state_dict()
            state['target_pair_reduction'] = dict(expected)
            return state
    return PairLearner
