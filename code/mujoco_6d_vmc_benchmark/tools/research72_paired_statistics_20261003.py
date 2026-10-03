"""Predeclared crossed-seed/condition statistics, independent of simulation.

Rows are training seeds, columns are shared conditions. Deterministic methods
have one row, never three duplicated observations. Missing data remain NaN.
This module neither selects checkpoints nor accesses condition manifests.
"""
import numpy as np

ANALYSIS_SEED = 2026100373
BOOTSTRAP_REPLICATES = 10000


def rectangular(values):
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or not array.size or np.isinf(array).any():
        raise ValueError("Expected a nonempty seed-by-condition array; infinity is invalid")
    return array


def success_summary(values):
    """Missing trials bound the rate; they are neither observed failures nor wins."""
    x = rectangular(values)
    observed = np.isfinite(x)
    if not np.isin(x[observed], [0., 1.]).all():
        raise ValueError("Success must be binary or missing")
    wins = int(np.nansum(x)); count = int(observed.sum()); total = x.size
    per_seed = []
    for row in x:
        n = int(np.isfinite(row).sum()); w = int(np.nansum(row))
        per_seed.append(dict(successes=w, observed=n, planned=len(row),
                             rate=w / n if n else None))
    return dict(successes=wins, observed=count, planned=total, missing=total-count,
                rate=wins / total if count == total else None,
                observed_only_rate=wins / count if count else None,
                planned_rate_bounds=[wins / total, (wins+total-count) / total],
                seeds=x.shape[0], conditions=x.shape[1], per_seed=per_seed,
                per_condition_successes=np.nansum(x, axis=0).astype(int).tolist(),
                per_condition_observed=observed.sum(axis=0).tolist())


def crossed_difference(left, right, *, eligible=None,
                       replicates=BOOTSTRAP_REPLICATES, seed=ANALYSIS_SEED):
    """Mean paired left-minus-right with crossed rather than flattened resampling.

Both learned methods must align seed identities before calling. One-row
deterministic controls are broadcast only for pairing, not sample-size claims.
The eligibility mask is outcome-conditioned when used for jointly successful
contacts; that restriction must remain explicit in the report.
"""
    a, b = rectangular(left), rectangular(right)
    if a.shape[1] != b.shape[1]:
        raise ValueError("Condition axes differ")
    nseed = max(a.shape[0], b.shape[0])
    if a.shape[0] not in (1, nseed) or b.shape[0] not in (1, nseed):
        raise ValueError("Seed axes must match or be deterministic")
    if replicates < 1:
        raise ValueError("Positive bootstrap count required")
    shape = (nseed, a.shape[1])
    a, b = np.broadcast_to(a, shape), np.broadcast_to(b, shape)
    valid = np.isfinite(a) & np.isfinite(b)
    if eligible is not None:
        mask = np.asarray(eligible, dtype=bool)
        if mask.shape != shape:
            raise ValueError("Explicit eligibility must match paired seed/condition axes")
        valid &= mask
    delta = np.where(valid, a-b, np.nan)
    count = int(valid.sum())
    result = dict(difference=float(np.nansum(delta)/count) if count else None,
                  paired_cells=count, paired_conditions=int(valid.any(axis=0).sum()),
                  planned_paired_cells=delta.size, training_seed_axis=nseed,
                  left_seed_count=rectangular(left).shape[0],
                  right_seed_count=rectangular(right).shape[0],
                  bootstrap_seed=seed, bootstrap_replicates=replicates,
                  outcome_conditioned=eligible is not None,
                  ci95=None, valid_bootstrap_replicates=0,
                  interval_semantics="Exploratory percentile interval; no multiplicity adjustment")
    if not count:
        return result
    rng = np.random.default_rng(seed)
    seeds = rng.integers(nseed, size=(replicates, nseed))
    conditions = rng.integers(shape[1], size=(replicates, shape[1]))
    draws = delta[seeds[:, :, None], conditions[:, None, :]]
    counts = np.isfinite(draws).sum(axis=(1, 2))
    estimates = np.nansum(draws, axis=(1, 2))[counts > 0]/counts[counts > 0]
    result.update(ci95=np.percentile(estimates, [2.5, 97.5]).tolist(),
                  valid_bootstrap_replicates=len(estimates))
    return result


def contact_pair_arrays(left, right, event, metric):
    """Prepare only full, jointly strict, jointly exposed pairs for a diagnostic."""
    a, b = np.asarray(left, dtype=object), np.asarray(right, dtype=object)
    if a.ndim != 2 or b.ndim != 2 or a.shape[1] != b.shape[1]:
        raise ValueError("Metrics require matching condition axes")
    nseed = max(a.shape[0], b.shape[0])
    if a.shape[0] not in (1, nseed) or b.shape[0] not in (1, nseed):
        raise ValueError("Metrics require matching seed axes")
    a, b = np.broadcast_to(a, (nseed, a.shape[1])), np.broadcast_to(b, (nseed, b.shape[1]))
    av = np.full(a.shape, np.nan); bv = av.copy(); valid = np.zeros(a.shape, bool)
    for index in np.ndindex(a.shape):
        x, y = a[index], b[index]
        # Keep each method's values independent of the other method's outcome.
        # Otherwise slicing back to a deterministic single row can erase a
        # valid comparison against seed2 merely because seed1 failed.
        for record, target in ((x, av), (y, bv)):
            if record is not None:
                value = record['contact'][event].get(metric)
                if value is not None:
                    target[index] = value
        if x is None or y is None:
            continue
        if not all(r['full_horizon'] and r['strict_success'] and r['contact'][event]['exposure'] for r in (x, y)):
            continue
        vx, vy = x['contact'][event].get(metric), y['contact'][event].get(metric)
        if vx is None or vy is None:
            continue
        valid[index] = np.isfinite(vx) and np.isfinite(vy)
    # Preserve deterministic row count for correct reporting and resampling.
    return av[:np.asarray(left).shape[0]], bv[:np.asarray(right).shape[0]], valid


def recovery_summary(records, event):
    """Report observation and censoring, never replace absent recovery by zero."""
    exposed = [r['recovery'][event] for r in records if r is not None and r['recovery'][event]['exposed']]
    recovered = [r for r in exposed if r['settled_rejoin_time_s'] is not None]
    censored = [r for r in exposed if r['right_censored']]
    if len(recovered)+len(censored) != len(exposed):
        raise ValueError("Recovery record is neither recovered nor censored")
    return dict(exposed=len(exposed), recovered=len(recovered), right_censored=len(censored),
                observed_recovery_times_s=[r['settled_rejoin_time_s'] for r in recovered],
                observation_windows_s=[r['observation_window_s'] for r in exposed],
                unconditional_mean_recovery_s=None,
                note="Recovery times conditional on observed recovery only; no naive average with censored or unexposed trials.")
