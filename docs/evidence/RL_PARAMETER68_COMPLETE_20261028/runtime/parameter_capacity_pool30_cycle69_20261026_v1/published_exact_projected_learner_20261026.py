"""Compose the tested execution optimization with persistent objective markers."""
from published_exact_pipeline_20261026 import install_foreach


def exact_class(base):
    """Retain both learning-objective markers; only change equivalent execution."""
    from published_projected_terminal_learner_20261026 import projected_class
    class ExactLearner(projected_class(base)):
        def load_state_dict(self, state):
            super().load_state_dict(state)
            self.pipeline_receipt = install_foreach(self)
    return ExactLearner
