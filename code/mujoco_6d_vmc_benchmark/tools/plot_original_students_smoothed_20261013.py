"""Display-only smoothing of the original three students; no simulation or fitting."""
import argparse
import csv
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sys

import numpy as np

METHODS = ('esn', 'ordinary_mlp', 'ordinary_rnn')
NAMES = dict(zip(METHODS, ('ESN', 'MLP', 'RNN')))
COLORS = dict(zip(METHODS, ('#117A70', '#DB7C29', '#6264BC')))
EVENTS = ('ball', 'human', 'rod', 'unknown_edge', 'pillar')
EVENT_NAMES = ('球撞击', '人手推', '棍推', '未知凸边／桌角', '柱子')
EVENT_COLORS = ('#D25B80', '#4E96BD', '#D2A02E', '#99837C', '#849A64')
SIGMA_S = .20
BIN_S = .02


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def smooth(values):
    """Symmetric nonnegative Gaussian, truncated at 3 sigma, edge-renormalized.

    No padding with zero-valued observations. Uses future samples for display
    only; contact times and raw metrics never pass through this operation.
    """
    y = np.asarray(values, dtype=float)
    radius = round(3*SIGMA_S/BIN_S)
    x = np.arange(-radius, radius+1)*BIN_S
    weights = np.exp(-.5*(x/SIGMA_S)**2)
    numerator = np.convolve(y, weights, 'full')[radius:radius+len(y)]
    denominator = np.convolve(np.ones(len(y)), weights, 'full')[radius:radius+len(y)]
    return numerator/denominator


def plot(rows, condition, out, pdf):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    fig, axes = plt.subplots(4, 1, figsize=(14, 11.8), sharex=True,
                             gridspec_kw={'height_ratios': [1, 1, 1, .86]})
    fig.subplots_adjust(left=.085, right=.985, bottom=.105, top=.865, hspace=.23)
    fig.suptitle('原版 ESN · MLP · RNN｜全过程平滑曲线', x=.085, ha='left', y=.975,
                 fontsize=20, fontweight='bold', color='#213245')
    fig.text(.085, .94, f'{condition}  ·  同一场景 / 同一仿真时钟 / 55 秒',
             fontsize=12, color='#546273')
    handles = [Line2D([], [], color=COLORS[r['method']], lw=2.5,
                      label=NAMES[r['method']]+'（原版）') for r in rows]
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(.08, .925),
               ncol=3, frameon=False, fontsize=12, handlelength=3, columnspacing=3)
    keys = ('rmse_mm', 'torque_nm', 'speed_mps')
    units = ('位置跟踪 RMSE\n(mm)', '最大关节力矩绝对值\n(N·m)', '末端平动速度\n(m/s)')
    for i, (ax, key, unit) in enumerate(zip(axes[:3], keys, units)):
        for r in rows:
            ax.plot(r['curves']['t'], r['smoothed'][key], color=COLORS[r['method']],
                    lw=2.0, label=NAMES[r['method']])
        for event, name, color in zip(EVENTS[:3], EVENT_NAMES[:3], EVENT_COLORS[:3]):
            contacts = [r['actual_contact'][event] for r in rows
                        if r['actual_contact'][event]['first_contact_s'] is not None]
            if not contacts:
                continue
            a = min(c['first_contact_s'] for c in contacts)
            b = max(c['last_contact_s'] for c in contacts)
            ax.axvspan(a, b, color=color, alpha=.075, zorder=0)
            if b-a < .3:
                ax.axvline(a, color=color, alpha=.5, lw=.9, ls=':')
            if i == 0:
                ax.text((a+b)/2, 1.025, f'{name} {a:.2f}–{b:.2f}s',
                        transform=ax.get_xaxis_transform(), ha='center',
                        color=color, fontsize=9.5)
        ax.set(ylabel=unit, ylim=(0, None), xlim=(0, 55))
        ax.grid(axis='y', alpha=.18)
        ax.grid(axis='x', alpha=.08)
        ax.tick_params(labelsize=10)
        ax.text(.985, .90, ('A', 'B', 'C')[i], transform=ax.transAxes,
                ha='right', fontsize=12, color='#9CA7B2')
    ax = axes[3]
    for rowno, r in enumerate(rows):
        y = 2-rowno
        for eventno, (event, color) in enumerate(zip(EVENTS, EVENT_COLORS)):
            c = r['actual_contact'][event]
            if c['first_contact_s'] is None:
                continue
            a, b = c['first_contact_s'], c['last_contact_s']
            offset = .26-eventno*.13
            ax.broken_barh([(a, max(b-a, 0.001))], (y+offset-.06, .12),
                           facecolors=color, edgecolors=color, linewidth=.7)
        ax.axhline(y-.44, color='#CCD3DC', lw=.6, alpha=.6)
    ax.set(yticks=[2, 1, 0], yticklabels=['ESN', 'MLP', 'RNN'], ylim=(-.5, 2.6),
           xlabel='仿真时间 (s)｜实际接触首末跨度（内部可能有间断）')
    ax.set_xticks(np.arange(0, 56, 5))
    ax.grid(axis='x', alpha=.15)
    ax.legend(handles=[Patch(facecolor=c, label=n) for c, n in zip(EVENT_COLORS, EVENT_NAMES)],
              loc='lower left', bbox_to_anchor=(0, 1.01), ncol=5,
              fontsize=9, frameon=False, borderaxespad=0)
    fig.text(.085, .058, '统一高斯平滑：σ = 0.20 s，约 95% 权重在 ±0.40 s 内；仅用于展示趋势，短时峰值会被压低。',
             fontsize=9.5, color='#546273')
    fig.text(.085, .036, '上方浅色带 = 三方法接触首末时刻的包络；下方逐方法分开。接触时间未经平滑；原始峰值另存，不以平滑峰值替代。',
             fontsize=9.5, color='#546273')
    fig.savefig(out/(condition+'.png'), dpi=175)
    pdf.savefig(fig)
    if condition.endswith('000'):
        fig.savefig(out/(condition+'.pdf'))
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    write(out/'execution.json', dict(status='running', command=sys.argv, started_utc=started))
    np.testing.assert_allclose(smooth(np.ones(8)*3), 3, atol=1e-14)
    impulse = np.zeros(101); impulse[50] = 1
    np.testing.assert_allclose(smooth(impulse), smooth(impulse)[::-1], atol=1e-14)
    raw = read(args.input)
    rows = [r for r in raw['rows'] if r['cohort'] == 'original' and r['method'] in METHODS]
    del raw
    gc.collect()
    conditions = sorted({r['condition'] for r in rows})
    assert len(rows) == 24 and len(conditions) == 8
    assert len({(r['condition'], r['method']) for r in rows}) == 24
    write(out/'source_curves.json', dict(rows=rows))
    audit_rows = []
    for r in rows:
        run = Path(r['source']['run'])
        assert sha(r['source']['raw']) == r['source']['raw_sha256']
        assert sha(run/'AUDIT.json') == r['source']['audit_sha256']
        audit = read(run/'AUDIT.json')
        execution = read(run/'execution.json')
        checkpoint = run/'checkpoint.npz'
        assert sha(checkpoint) == execution['checkpoint_sha256']
        for key, val in r['checks'].items():
            np.testing.assert_allclose(audit[key], val, rtol=1e-9)
        t = np.asarray(r['curves']['t'])
        np.testing.assert_allclose(np.diff(t), BIN_S, rtol=0, atol=1e-7)
        assert len(t) == 2750 and r['full_horizon']
        r['smoothed'] = dict(
            rmse_mm=np.sqrt(smooth(np.square(r['curves']['interval_rms_mm']))).tolist(),
            torque_nm=smooth(r['curves']['torque_peak_nm']).tolist(),
            speed_mps=smooth(r['curves']['speed_peak_mps']).tolist())
        assert all(np.isfinite(v).all() for v in r['smoothed'].values())
        for c in r['actual_contact'].values():
            if c['first_contact_s'] is not None:
                assert 0 <= c['first_contact_s'] <= c['last_contact_s'] <= t[-1]+1e-7
        audit_rows.append(dict(method=r['method'], condition=r['condition'],
            checkpoint_sha256=execution['checkpoint_sha256'], source=r['source'],
            raw_metrics=r['checks'], task=r['task'], strict=r['strict']))
    write(out/'smoothed_curves.json', dict(sigma_s=SIGMA_S, truncated_support_s=.6, rows=rows))
    with (out/'contact_intervals.csv').open('w') as f:
        writer = csv.writer(f)
        writer.writerow(['condition', 'method', 'event', 'first_contact_s', 'last_contact_s', 'cumulative_contact_s'])
        for r in rows:
            for event, c in r['actual_contact'].items():
                writer.writerow([r['condition'], r['method'], event, c['first_contact_s'],
                                 c['last_contact_s'], c['contact_duration_s']])
    with (out/'raw_metrics.csv').open('w') as f:
        writer = csv.writer(f)
        writer.writerow(['condition','method','task','strict','rmse_mm','peak_torque_nm','peak_speed_mps'])
        for r in rows:
            writer.writerow([r['condition'],r['method'],r['task'],r['strict'],
                             *[r['checks'][k] for k in ('rmse_mm','peak_torque_nm','peak_speed_mps')]])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.spines.left': False, 'axes.spines.bottom': False,
                         'axes.unicode_minus': False, 'pdf.fonttype': 42})
    with PdfPages(out/'original_three_all_8_conditions.pdf') as pdf:
        for condition in conditions:
            subset = sorted([r for r in rows if r['condition'] == condition],
                            key=lambda r: METHODS.index(r['method']))
            plot(subset, condition, out, pdf)
    links = ''.join(f'<h2>{c}</h2><a href="{c}.png"><img src="{c}.png" width="1100"></a>' for c in conditions)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>原版三模型平滑曲线</title>'
        '<style>body{font-family:system-ui;margin:30px;background:#f5f7fa}img{max-width:100%;background:white}</style>'
        '<h1>原版 ESN / MLP / RNN：8 个条件</h1><p>相同平滑强度；接触首末跨度含间断，不等于持续接触。</p>'
        '<p><a href="original_three_all_8_conditions.pdf">下载完整 PDF</a> · '
        '<a href="contact_intervals.csv">接触时刻表</a> · <a href="raw_metrics.csv">未经平滑的指标</a></p>'+links)
    shutil.copy2(__file__, out/Path(__file__).name)
    write(out/'AUDIT.json', dict(status='passed', rows=24, conditions=conditions,
        input_sha256=sha(args.input), input_path=str(args.input.resolve()),
        source_sha256=sha(__file__), checks=['original_only', 'three_methods_only',
        'raw_substep_hash', 'episode_audit_hash', 'checkpoint_hash', 'raw_metrics_unchanged',
        'finite_smoothed_curves', 'constant_preservation_at_edges', 'symmetric_kernel',
        'contact_spans_within_recording', 'no_new_simulation'], records=audit_rows))
    write(out/'execution.json', dict(status='complete', command=sys.argv, started_utc=started,
        ended_utc=datetime.now(timezone.utc).isoformat(), host=platform.node(),
        interpreter=sys.executable, python=platform.python_version(), numpy=np.__version__,
        matplotlib=matplotlib.__version__, source_sha256=sha(__file__), simulation=False,
        server_compute=False, sigma_s=SIGMA_S, support_s=.6,
        rmse_definition='sqrt(Gaussian-weighted mean of 20ms squared position-error RMS)',
        torque_speed_definition='Gaussian mean of audited 20ms physical peak envelopes',
        edge_behavior='renormalize to available data; no zero padding',
        event_definition='unsmoothed first-to-last contact span; may include gaps', rows=24))
    print(json.dumps(dict(status='complete', out=str(out), rows=24, pages=8)))


if __name__ == '__main__':
    main()
