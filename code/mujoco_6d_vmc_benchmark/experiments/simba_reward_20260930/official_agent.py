"""Pinned official SimbaV2, including its observation/reward normalizers.

Replay stores raw observations, raw rewards and tanh actions. Call sample_action
once per interaction (also during random warmup) so wrapper statistics advance.
A previous_transition is consumed once; do not also consume_transition on it.
This is an Office task adaptation, not an original-paper Office reward.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

UPSTREAM = Path("/home/arm1/vmc_mujoco_runtime/SimbaV2")
UPSTREAM_COMMIT = "86899c277cdc697b2b02d827243de1ea93f20a1d"
WARMUP_STEPS = 5000
BATCH_SIZE = 256
REPLAY_CAPACITY = 1_000_000

# Compatibility needed by the existing isolated server environment.
for name, value in (("long", np.int64), ("ulong", np.uint64)):
    if name not in np.__dict__:
        setattr(np, name, value)
if "issctype" not in np.__dict__:
    np.issctype = lambda x: isinstance(x, type) and issubclass(x, np.generic)
sys.path.insert(0, str(UPSTREAM))

import gymnasium as gym
import jax
# Upstream uses the pre-0.6 spelling; preserve identical tree-map semantics.
if not hasattr(jax, "tree_map"):
    jax.tree_map = jax.tree_util.tree_map
import jax.numpy as jnp
from omegaconf import OmegaConf
from scale_rl.agents import create_agent


def official_config(seed: int, total_steps: int, utd: int = 2,
                    gamma: float = .995, entropy_coef: float = -.5, initial_temperature: float = .01) -> dict:
    if total_steps <= 0 or utd < 1 or not 0 < gamma < 1:
        raise ValueError("invalid training budget, UTD or discount")
    return dict(
        agent_type="simbaV2", seed=seed,
        normalize_observation=True, normalize_reward=True, normalized_g_max=5.,
        load_only_param=False, load_param_key=None,
        load_observation_normalizer=True, load_reward_normalizer=True,
        learning_rate_init=1e-4, learning_rate_end=5e-5,
        learning_rate_decay_rate=1.,
        learning_rate_decay_step=max(1, total_steps * utd),
        actor_num_blocks=1, actor_hidden_dim=128, actor_c_shift=3.,
        actor_scaler_init=math.sqrt(2/128), actor_scaler_scale=math.sqrt(2/128),
        actor_alpha_init=.5, actor_alpha_scale=1/math.sqrt(128), actor_bc_alpha=0.,
        critic_use_cdq=True, critic_num_blocks=2, critic_hidden_dim=512,
        critic_c_shift=3., critic_num_bins=101, critic_min_v=-5., critic_max_v=5.,
        critic_scaler_init=math.sqrt(2/512), critic_scaler_scale=math.sqrt(2/512),
        critic_alpha_init=1/3, critic_alpha_scale=1/math.sqrt(512),
        target_tau=.005, temp_initial_value=initial_temperature, temp_target_entropy=None,
        temp_target_entropy_coef=entropy_coef, gamma=gamma, n_step=1,
    )


class OfficialOfficeAgent:
    def __init__(self, seed: int, total_steps: int, utd: int = 2,
                 gamma: float = .995, entropy_coef: float = -.5, initial_temperature: float = .01):
        actual = subprocess.check_output(
            ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
        if actual != UPSTREAM_COMMIT:
            raise RuntimeError(f"upstream pin mismatch: {actual}")
        self.config = official_config(seed, total_steps, utd, gamma, entropy_coef, initial_temperature)
        self.utd = utd
        self.agent = create_agent(
            gym.spaces.Box(-np.inf, np.inf, shape=(48,), dtype=np.float32),
            gym.spaces.Box(-1., 1., shape=(7,), dtype=np.float32),
            OmegaConf.create(self.config),
        )
        self.reward_normalizer = self.agent
        self.observation_normalizer = self.agent.agent
        self.raw_agent = self.agent.agent.agent
        self.interactions = 0
        self.updates = 0
        self.reward_samples = 0

    @staticmethod
    def _observation(raw_observation):
        obs = np.asarray(raw_observation, dtype=np.float32)
        if obs.shape != (48,) or not np.isfinite(obs).all():
            raise ValueError("expected finite raw48 observation")
        return obs[None, :].copy()

    def consume_transition(self, reward: float, terminated: bool,
                           truncated: bool = False):
        """Consume the final transition if there will be no next action.

        This reproduces RewardNormalizer.sample_actions' statistics update;
        it does not train, sample an action, or touch observation statistics.
        Never subsequently pass this same transition to sample_action.
        """
        norm = self.reward_normalizer
        done = np.asarray([bool(terminated or truncated)])
        rew = np.asarray([reward], dtype=np.float32)
        if not np.isfinite(rew).all():
            raise ValueError("reward must be finite")
        norm.G = norm.gamma * (1 - done) * norm.G + rew
        norm.G_rms.update(norm.G)
        norm.G_r_max = max(norm.G_r_max, float(np.max(np.abs(norm.G))))
        self.reward_samples += 1

    def sample_action(self, raw_observation, previous_transition=None,
                      training: bool = True) -> np.ndarray:
        obs = self._observation(raw_observation)
        timestep = {"next_observation": obs}
        if previous_transition is not None:
            if training:
                self.consume_transition(
                    previous_transition["reward"],
                    previous_transition["terminated"],
                    previous_transition.get("truncated", False),
                )
        # Reward statistics were explicitly consumed above. Call the inner
        # official observation wrapper to avoid consuming them twice.
        action = self.observation_normalizer.sample_actions(
            self.interactions, timestep, training=training)
        if training:
            self.interactions += 1
        return np.asarray(action[0], dtype=np.float32)

    def update(self, raw_batch: dict) -> dict:
        required = ("observation", "action", "reward", "terminated",
                    "truncated", "next_observation")
        batch = {key: np.asarray(raw_batch[key], dtype=np.float32).copy()
                 for key in required}
        # Both normalizers mutate their batch; copies protect replay contents.
        info = self.agent.update(self.updates, batch)
        self.updates += 1
        return info

    def diagnostics(self) -> dict:
        norm = self.reward_normalizer
        denom = max(float(np.sqrt(norm.G_rms.var[0] + norm.epsilon)),
                    float(norm.G_r_max / norm.g_max))
        return dict(reward_scale_denominator=denom,
                    reward_return_abs_max=float(norm.G_r_max),
                    reward_samples=self.reward_samples,
                    observation_samples=float(
                        self.observation_normalizer.obs_rms.count),
                    interactions=self.interactions, updates=self.updates)

    def save(self, path):
        path = Path(path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        self.agent.save(str(path))
        state = dict(config=self.config, upstream_commit=UPSTREAM_COMMIT,
                     utd=self.utd, interactions=self.interactions,
                     updates=self.updates, reward_samples=self.reward_samples,
                     jax_rng=np.asarray(self.raw_agent._rng).tolist(),
                     replay_saved=False,
                     note="Replay/environment state is caller responsibility.")
        (path / "official_agent_state.json").write_text(
            json.dumps(state, indent=2) + "\n")

    def load(self, path):
        path = Path(path).resolve()
        state = json.loads((path / "official_agent_state.json").read_text())
        if state["upstream_commit"] != UPSTREAM_COMMIT:
            raise ValueError("checkpoint upstream mismatch")
        if state["config"] != self.config:
            raise ValueError("resume config differs; reconstruct with saved config")
        self.agent.load(str(path))
        self.raw_agent._rng = jnp.asarray(state["jax_rng"], dtype=jnp.uint32)
        self.interactions = state["interactions"]
        self.updates = state["updates"]
        self.reward_samples = state["reward_samples"]
