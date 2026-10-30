"""Persist the explicit finite-target projection objective across future resumes."""
from published_terminal_loss_weight_20261026 import weighted_class
from published_finite_target_projection_20261026 import install

MARKER = dict(version=1, terminal_cap=30., gamma=.9995, maximum_actions=1375,
              position='target critic Q before stochastic entropy term', upper_only=True)


def projected_class(base):
    class ProjectedLearner(weighted_class(base, 128)):
        def load_state_dict(self, state):
            if state.get('finite_target_projection', MARKER) != MARKER:
                raise ValueError('Cannot silently change projection contract')
            if state.get('terminal_loss_weight') != 128:
                raise ValueError('Expected terminal-weighted formal parent')
            super().load_state_dict(state)
            self.projection_receipt = install(self, True)

        def state_dict(self):
            state = super().state_dict()
            state['finite_target_projection'] = dict(MARKER)
            return state
    return ProjectedLearner
