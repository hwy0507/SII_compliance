"""One registered inference intervention: halve pre-tanh Gaussian std.

This changes the sampling distribution intentionally. Serialized weights,
optimizer, replay and RNG stay unchanged; that is not a claim of unchanged
policy behavior. No original runtime files are edited.
"""
import math,types

def install_probe(learner, observations, digest):
    import torch
    actor=learner.learner.agent.actor
    assert not hasattr(actor,'_sii_probe_original_forward')
    before=digest(learner.state_dict())
    original=actor.forward
    # Use the native normalization/context/clock bridge; its registered actor
    # wrapper still strips privileged clock before actor inference.
    obs=torch.as_tensor(learner.observation(observations[0]),device=learner.device).unsqueeze(0)
    assert obs.shape==(1,50)
    # The probe checks the sampling map at a fixed input; this is not a new
    # physics rollout, and does not replace native stream replay after each case.
    with torch.no_grad():
        mean0,std0log=original(obs)
    actor._sii_probe_original_forward=original
    def forward(self, observation):
        mean, log_std=self._sii_probe_original_forward(observation)
        return mean,log_std-math.log(2.)
    actor.forward=types.MethodType(forward,actor)
    with torch.no_grad():
        mean1,std1log=actor(obs)
        assert torch.equal(mean0,mean1)
        assert torch.equal(std1log,std0log-math.log(2.))
        assert torch.allclose(std1log.exp(),.5*std0log.exp(),rtol=1e-6,atol=0.)
    assert digest(learner.state_dict())==before
    return dict(passed=True,pre_tanh_std_factor=.5,pre_tanh_mean_exact=True,
        serialized_learner_optimizer_rng_unchanged=True,sampling_distribution_intentionally_changed=True,
        affects='Native stochastic actor forward distribution; tanh/action bounds and original CHEQ mixing remain',
        no_claim_of_training_entropy_equivalence=True,new_physics=0,new_optimizer_updates=0)
