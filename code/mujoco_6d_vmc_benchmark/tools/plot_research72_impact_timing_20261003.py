"""Plot all 34 models on each of five public conditions; no winner selection."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); data = json.loads(a.input.read_text()); rows = data['rows']
    assert data['episodes'] == data['exposed'] == 170
    conditions = sorted({r['condition'] for r in rows})
    assert len(conditions) == 5
    a.output.mkdir(parents=True, exist_ok=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    summaries = []
    for index, condition in enumerate(conditions):
        subset = [r for r in rows if r['condition'] == condition]
        assert len(subset) == 34
        contact = [r['first_bout_duration_ms'] for r in subset]
        update = [r['time_until_next_actor_update_ms'] for r in subset]
        ax.hlines(index, 0, max(contact), color='#bb5544', lw=7,
                  label='First contact episode (maximum duration)' if index == 0 else None)
        ax.hlines(index, min(update), max(update), color='#2367a5', lw=2,
                  label='Next actor evaluation (min–max across 34 models)' if index == 0 else None)
        ax.scatter([float(np.median(update))], [index], s=38, color='#2367a5', zorder=3,
                   label='Median actor evaluation' if index == 0 else None)
        summaries.append(dict(condition=condition, models=len(subset),
            maximum_first_contact_duration_ms=max(contact), next_actor_evaluation_min_ms=min(update),
            next_actor_evaluation_median_ms=float(np.median(update)), next_actor_evaluation_max_ms=max(update)))
    ax.set_yticks(range(5), [f'Public condition {i:03d}' for i in range(5)])
    ax.invert_yaxis(); ax.set_ylim(4.6, -.6); ax.set_xlim(-.8, 35)
    ax.set_xlabel('Time after first detected ball contact (ms)')
    ax.set_title('The first impact pulse ends before the next policy evaluation\n170/170 public traces: first peak occurs before that evaluation', fontsize=12)
    ax.grid(axis='x', alpha=.2); ax.spines[['top', 'right']].set_visible(False)
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.18), frameon=False, fontsize=9)
    fig.text(.5, .025, '33 initial learned candidates + original teacher per condition; failures retained.\n'
        '50 μs physics resolution; 40 ms actor period. The 4 ms WBC and passive dynamics still respond.',
        ha='center', fontsize=8.5)
    fig.subplots_adjust(left=.18, right=.97, top=.83, bottom=.32)
    for suffix in ('png', 'pdf'):
        fig.savefig(a.output/('impact_timing.'+suffix), dpi=180)
    plt.close(fig)
    cgroup = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    record = dict(status='complete', completed_utc=datetime.now(timezone.utc).isoformat(),
        host=platform.node(), python=sys.executable, argv=sys.argv, numpy=np.__version__,
        memory_max=(cgroup/'memory.max').read_text().strip(), source_sha256=sha(Path(__file__)),
        input_sha256=sha(a.input), summaries=summaries,
        outputs={p.name: sha(p) for p in a.output.iterdir()},
        interpretation='Diagnostic timing only, not a causal compliance ranking or hardware force safety test.')
    (a.output/'MANIFEST.json').write_text(json.dumps(record, indent=2, allow_nan=False)+'\n')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
