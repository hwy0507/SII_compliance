#!/usr/bin/env python3
"""Render a readable paired GIF for the rod-perturbation VMC experiment.

Left: no-rod reference. Right: physical rod perturbation. The magenta actual
marker, blue nominal marker and cyan virtual-carriage marker make the
departure/rejoin relation visible; a small inset plots end-effector deviation
from the paired no-rod trajectory over simulation time.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def _frame_indices(
    frame_count: int,
    time: np.ndarray,
    start_time: float | None,
    end_time: float | None,
) -> np.ndarray:
    """Map GIF frames to a full simulation trace, including cropped GIFs."""

    eligible = np.flatnonzero(
        (True if start_time is None else time >= start_time)
        & (True if end_time is None else time <= end_time)
    )
    if len(eligible) == 0:
        raise ValueError("the declared GIF time window does not intersect the trace")
    sampled = np.rint(np.linspace(0, len(eligible) - 1, frame_count)).astype(int)
    return eligible[np.clip(sampled, 0, len(eligible) - 1)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--perturbed-gif", type=Path, required=True)
    parser.add_argument("--perturbed-trace", type=Path, required=True)
    parser.add_argument("--reference-gif", type=Path, required=True)
    parser.add_argument("--reference-trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--playback-speed", type=float, default=0.5)
    parser.add_argument(
        "--time-start", type=float, default=None,
        help="Inclusive simulation-time start represented by the input GIFs (required when they were pre-cropped).",
    )
    parser.add_argument(
        "--time-end", type=float, default=None,
        help="Inclusive simulation-time end represented by the input GIFs (required when they were pre-cropped).",
    )
    args = parser.parse_args()

    perturbed_frames = list(iio.imiter(args.perturbed_gif))
    reference_frames = list(iio.imiter(args.reference_gif))
    perturbed = np.load(args.perturbed_trace)
    reference = np.load(args.reference_trace)
    count = min(len(perturbed_frames), len(reference_frames))
    times = perturbed["time"]
    if args.time_start is not None and args.time_end is not None and args.time_end <= args.time_start:
        raise ValueError("--time-end must be later than --time-start")
    perturbed_indices = _frame_indices(count, times, args.time_start, args.time_end)
    reference_indices = _frame_indices(count, reference["time"], args.time_start, args.time_end)
    delta = np.linalg.norm(perturbed["ee_position"] - reference["ee_position"], axis=1) * 1000.0
    font = _font(20)
    small = _font(15)
    output_frames: list[np.ndarray] = []

    for frame_no in range(count):
        left = Image.fromarray(reference_frames[frame_no]).convert("RGB")
        right = Image.fromarray(perturbed_frames[frame_no]).convert("RGB")
        width, height = left.size
        canvas = Image.new("RGB", (2 * width, height + 86), (12, 15, 22))
        canvas.paste(left, (0, 0))
        canvas.paste(right, (width, 0))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, width, 34), fill=(30, 51, 104))
        draw.rectangle((width, 0, 2 * width, 34), fill=(105, 35, 66))
        draw.text((12, 7), "Reference: no rod", fill="white", font=font)
        draw.text((width + 12, 7), "Physical rod perturbation", fill="white", font=font)
        index = perturbed_indices[frame_no]
        time_s = float(times[index])
        draw.text((12, height + 8), "blue: nominal  |  magenta: actual EE  |  cyan: virtual carriage", fill=(220, 230, 245), font=small)
        draw.text((12, height + 31), f"simulation time: {time_s:.2f} s   paired EE deviation: {delta[index]:.1f} mm", fill=(255, 226, 120), font=font)
        # Compact data strip: all historical paired deviations with current
        # time cursor. This makes a millimetre-scale physical deviation legible.
        x0, x1, y0, y1 = 510, 2 * width - 16, height + 10, height + 68
        draw.rectangle((x0, y0, x1, y1), outline=(92, 108, 134), width=1)
        plot_slice = delta[: index + 1]
        if len(plot_slice) > 1:
            max_value = max(5.0, float(np.max(delta)) * 1.1)
            points = [
                (x0 + (x1 - x0) * j / (len(plot_slice) - 1), y1 - (y1 - y0) * value / max_value)
                for j, value in enumerate(plot_slice)
            ]
            draw.line(points, fill=(255, 62, 173), width=2)
        draw.text((x0 + 4, y0 + 3), "paired EE deviation (mm)", fill=(194, 207, 227), font=small)
        output_frames.append(np.asarray(canvas))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(args.output, np.stack(output_frames), duration=1.0 / (25.0 * args.playback_speed), loop=0)


if __name__ == "__main__":
    main()
