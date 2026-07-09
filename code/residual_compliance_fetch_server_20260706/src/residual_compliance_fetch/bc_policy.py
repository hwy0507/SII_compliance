from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn


ARM_DOF = 7


class ResidualMLP(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int, hidden_sizes: tuple[int, ...]):
        super().__init__()
        layers: list[nn.Module] = []
        last_dim = int(obs_dim)
        for hidden in hidden_sizes:
            layers.append(nn.Linear(last_dim, int(hidden)))
            layers.append(nn.LayerNorm(int(hidden)))
            layers.append(nn.Tanh())
            last_dim = int(hidden)
        layers.append(nn.Linear(last_dim, int(action_dim)))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class BCResidualPolicy:
    """Offline BC policy for the contact-only residual action.

    The observation layout intentionally matches scripts/build_bc_dataset.py.
    It only consumes state/nominal command plus contact/force feedback signals
    that are available after contact has happened.
    """

    def __init__(self, checkpoint_path: str | Path, device: str = "auto"):
        path = Path(checkpoint_path)
        if not path.exists():
            raise FileNotFoundError(f"BC checkpoint not found: {path}")

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)

        self.obs_mean = np.asarray(checkpoint["obs_mean"], dtype=np.float32)
        self.obs_std = np.asarray(checkpoint["obs_std"], dtype=np.float32)
        self.link_vocab = [str(x) for x in checkpoint.get("link_vocab", ["none"])]
        if "none" not in self.link_vocab:
            self.link_vocab = ["none"] + self.link_vocab
        self.link_to_index = {name: idx for idx, name in enumerate(self.link_vocab)}

        hidden_sizes = tuple(int(x) for x in checkpoint["hidden_sizes"])
        self.model = ResidualMLP(
            obs_dim=int(checkpoint["obs_dim"]),
            action_dim=int(checkpoint["action_dim"]),
            hidden_sizes=hidden_sizes,
        ).to(self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

    def make_observation(
        self,
        *,
        q_arm: np.ndarray,
        q_target: np.ndarray,
        qdot_nominal: np.ndarray,
        prev_residual: np.ndarray,
        compliance_info: dict[str, Any],
        qvel_tracking_error: float,
    ) -> np.ndarray:
        q_arm = np.asarray(q_arm, dtype=np.float32).reshape(ARM_DOF)
        q_target = np.asarray(q_target, dtype=np.float32).reshape(ARM_DOF)
        qdot_nominal = np.asarray(qdot_nominal, dtype=np.float32).reshape(ARM_DOF)
        prev_residual = np.asarray(prev_residual, dtype=np.float32).reshape(ARM_DOF)

        contact_depth = float(compliance_info.get("contact_depth", 0.0))
        force_level = float(compliance_info.get("force_level", 0.0))
        contact_level = float(compliance_info.get("contact_level", 0.0))
        contact_flag = float(contact_depth > 1e-8 or force_level > 1e-8 or contact_level > 1e-8)

        link_name = compliance_info.get("active_link")
        link_name = "none" if link_name is None else str(link_name)
        one_hot = np.zeros(len(self.link_vocab), dtype=np.float32)
        one_hot[self.link_to_index.get(link_name, self.link_to_index.get("none", 0))] = 1.0

        obs = np.concatenate(
            [
                q_arm,
                q_target,
                q_target - q_arm,
                qdot_nominal,
                prev_residual,
                np.asarray(
                    [
                        contact_depth,
                        force_level,
                        float(qvel_tracking_error),
                        contact_level,
                        contact_flag,
                    ],
                    dtype=np.float32,
                ),
                one_hot,
            ]
        ).astype(np.float32)
        if obs.shape != self.obs_mean.shape:
            raise ValueError(f"BC observation shape {obs.shape} != checkpoint shape {self.obs_mean.shape}")
        return obs

    def predict(
        self,
        *,
        q_arm: np.ndarray,
        q_target: np.ndarray,
        qdot_nominal: np.ndarray,
        prev_residual: np.ndarray,
        compliance_info: dict[str, Any],
        qvel_tracking_error: float,
    ) -> np.ndarray:
        obs = self.make_observation(
            q_arm=q_arm,
            q_target=q_target,
            qdot_nominal=qdot_nominal,
            prev_residual=prev_residual,
            compliance_info=compliance_info,
            qvel_tracking_error=qvel_tracking_error,
        )
        obs = (obs - self.obs_mean) / np.maximum(self.obs_std, 1e-6)
        with torch.no_grad():
            x = torch.from_numpy(obs).to(self.device).unsqueeze(0)
            action = self.model(x).squeeze(0).detach().cpu().numpy()
        return np.asarray(action, dtype=np.float32)
