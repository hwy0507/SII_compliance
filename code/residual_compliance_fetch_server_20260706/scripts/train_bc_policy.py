#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from residual_compliance_fetch.utils import ensure_dir


class ResidualMLP(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int, hidden_sizes: tuple[int, ...]):
        super().__init__()
        layers: list[nn.Module] = []
        last_dim = obs_dim
        for hidden in hidden_sizes:
            layers.append(nn.Linear(last_dim, hidden))
            layers.append(nn.LayerNorm(hidden))
            layers.append(nn.Tanh())
            last_dim = hidden
        layers.append(nn.Linear(last_dim, action_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _load_dataset(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    data = np.load(path, allow_pickle=True)
    observations = data["observations"].astype(np.float32)
    actions = data["actions"].astype(np.float32)
    weights = data["sample_weights"].astype(np.float32)
    meta = {
        "feature_names": [str(x) for x in data["feature_names"].tolist()],
        "link_vocab": [str(x) for x in data["link_vocab"].tolist()],
    }
    return observations, actions, weights, meta


def _weighted_mse(pred: torch.Tensor, target: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    per_sample = torch.mean((pred - target) ** 2, dim=1)
    return torch.mean(per_sample * weight)


def train(args: argparse.Namespace) -> dict:
    _set_seed(int(args.seed))

    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = PROJECT_ROOT / data_path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    ensure_dir(output_path.parent)

    observations, actions, weights, meta = _load_dataset(data_path)
    n = observations.shape[0]
    if n < 10:
        raise RuntimeError(f"Need at least 10 samples, got {n}")

    indices = np.arange(n)
    rng = np.random.default_rng(int(args.seed))
    rng.shuffle(indices)
    val_count = max(1, int(n * float(args.val_fraction)))
    val_indices = indices[:val_count]
    train_indices = indices[val_count:]

    obs_mean = observations[train_indices].mean(axis=0).astype(np.float32)
    obs_std = observations[train_indices].std(axis=0).astype(np.float32)
    obs_std = np.maximum(obs_std, 1e-6)

    x_train = (observations[train_indices] - obs_mean) / obs_std
    y_train = actions[train_indices]
    w_train = weights[train_indices]
    x_val = (observations[val_indices] - obs_mean) / obs_std
    y_val = actions[val_indices]
    w_val = weights[val_indices]

    train_ds = TensorDataset(
        torch.from_numpy(x_train),
        torch.from_numpy(y_train),
        torch.from_numpy(w_train),
    )
    val_x = torch.from_numpy(x_val)
    val_y = torch.from_numpy(y_val)
    val_w = torch.from_numpy(w_val)

    device_name = args.device
    if device_name == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_name)

    hidden_sizes = tuple(int(x) for x in str(args.hidden_sizes).split(",") if x.strip())
    model = ResidualMLP(
        obs_dim=observations.shape[1],
        action_dim=actions.shape[1],
        hidden_sizes=hidden_sizes,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(args.lr), weight_decay=float(args.weight_decay))
    loader = DataLoader(
        train_ds,
        batch_size=int(args.batch_size),
        shuffle=True,
        drop_last=False,
    )

    history: list[dict] = []
    best_val = float("inf")
    best_state = None

    val_x = val_x.to(device)
    val_y = val_y.to(device)
    val_w = val_w.to(device)

    for epoch in range(1, int(args.epochs) + 1):
        model.train()
        train_losses = []
        for batch_x, batch_y, batch_w in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            batch_w = batch_w.to(device)
            pred = model(batch_x)
            loss = _weighted_mse(pred, batch_y, batch_w)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=float(args.grad_clip))
            optimizer.step()
            train_losses.append(float(loss.detach().cpu()))

        model.eval()
        with torch.no_grad():
            val_pred = model(val_x)
            val_loss = float(_weighted_mse(val_pred, val_y, val_w).detach().cpu())
            val_mae = float(torch.mean(torch.abs(val_pred - val_y)).detach().cpu())

        train_loss = float(np.mean(train_losses)) if train_losses else 0.0
        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "val_mae": val_mae,
        }
        history.append(row)
        if val_loss < best_val:
            best_val = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

        if epoch == 1 or epoch % int(args.log_every) == 0 or epoch == int(args.epochs):
            print(
                f"epoch={epoch:04d} train_loss={train_loss:.6f} "
                f"val_loss={val_loss:.6f} val_mae={val_mae:.6f}"
            )

    if best_state is not None:
        model.load_state_dict(best_state)

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "obs_mean": obs_mean,
        "obs_std": obs_std,
        "hidden_sizes": hidden_sizes,
        "obs_dim": int(observations.shape[1]),
        "action_dim": int(actions.shape[1]),
        "feature_names": meta["feature_names"],
        "link_vocab": meta["link_vocab"],
        "data_path": str(data_path),
        "best_val_loss": float(best_val),
    }
    torch.save(checkpoint, output_path)

    history_path = output_path.with_suffix(".history.json")
    with history_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "data_path": str(data_path),
                "output_path": str(output_path),
                "device": str(device),
                "num_samples": int(n),
                "train_samples": int(len(train_indices)),
                "val_samples": int(len(val_indices)),
                "history": history,
                "best_val_loss": float(best_val),
            },
            f,
            indent=2,
        )

    return {
        "checkpoint": str(output_path),
        "history": str(history_path),
        "device": str(device),
        "best_val_loss": float(best_val),
        "num_samples": int(n),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a BC warm-start residual policy.")
    parser.add_argument("--data", default="data/contact_heavy_strict_500_bc.npz")
    parser.add_argument("--output", default="runs/bc_contact_policy.pt")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--hidden-sizes", default="256,256")
    parser.add_argument("--val-fraction", type=float, default=0.15)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--log-every", type=int, default=5)
    args = parser.parse_args()

    result = train(args)
    print(json.dumps(result, indent=2))
    print(f"Saved BC checkpoint to {result['checkpoint']}")


if __name__ == "__main__":
    main()
