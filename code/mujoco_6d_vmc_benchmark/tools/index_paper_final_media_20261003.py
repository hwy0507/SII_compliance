"""Verify downloaded full videos and index all preselected final galleries."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    report = json.loads(a.report.read_text())
    by_run = {r['run']: r for r in report['rows']}
    assert len(by_run) == len(report['rows'])
    server = Path('/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_rl_20261002_141136')
    entries = []
    for folder, expected in [('media_final_h1', 26), ('media_formal', 7), ('media_remaining_designed_conditions', 14)]:
        manifests = sorted((a.cache/folder).glob('*/manifest.json'))
        assert len(manifests) == expected
        for path in manifests:
            meta = json.loads(path.read_text())
            audit = json.loads((path.parent/'MEDIA_AUDIT.json').read_text())
            run = str(Path(meta['record']).parent)
            result = by_run[run]
            assert meta['input_sha256']['.npz'] == result['trace_sha256']
            assert meta['input_sha256']['.mjb'] == result['model_sha256']
            assert meta['scene_label'] == 'office-validation-v6'
            assert meta['stride'] == 1 and meta['fps'] == 25 and meta['frame_count'] == 1375
            assert audit['decoded_frames'] == 1375 and audit['duration_s'] == 55 and result['full_horizon']
            for ext, digest in meta['output_sha256'].items():
                assert sha(path.parent/('replay_threeview'+ext)) == digest
            assert audit['video_sha256'] == meta['output_sha256']['.mp4']
            assert sha(path.parent/'review_montage.png') == audit['montage_sha256']
            relative = path.parent.relative_to(a.cache)
            entries.append(dict(name=result['name'], tier=result['tier'], condition=result['condition'],
                                task_success=result['task_success'], strict_success=result['strict_success'],
                                run=run, server_video=str(server/relative/'replay_threeview.mp4'),
                                local_video=str((path.parent/'replay_threeview.mp4').resolve()),
                                trace_sha256=result['trace_sha256'], video_sha256=audit['video_sha256'],
                                gif_sha256=meta['output_sha256']['.gif'], manifest_sha256=sha(path),
                                media_audit_sha256=sha(path.parent/'MEDIA_AUDIT.json')))
    comparisons = []
    for seed in (1, 2):
        relative = Path('comparison_final_h1_seed'+str(seed))
        path = a.cache/relative
        meta = json.loads((path/'MANIFEST.json').read_text())
        assert sha(path/'comparison.mp4') == meta['video_sha256']
        assert meta['decoded_frames'] == 1375 and meta['fps'] == 25 and meta['duration_s'] == 55
        comparisons.append(dict(seed=seed, server_video=str(server/relative/'comparison.mp4'),
                                video_sha256=meta['video_sha256'], manifest_sha256=sha(path/'MANIFEST.json')))
    index = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=sha(Path(__file__)),
                 verification_host=platform.node(), python=sys.executable, argv=sys.argv,
                 report_sha256=sha(a.report), full_videos=entries, stacked_comparisons=comparisons,
                 note='All 26 h1 and seven formal models; h2-h4 both ESN/matched-RNN seeds, plus h3 teacher and memoryless explanatory controls. No outcome filtering. Native decode audits and downloaded content hashes both verified. Videos are saved-state replays, not new simulation.')
    with (a.output/'MEDIA_INDEX.json').open('x') as f:
        json.dump(index, f, indent=2, allow_nan=False); f.write('\n')
    lines = ['# Complete three-view final media', '',
             'Server: `arm1@192.168.31.70:' + str(server) + '/`.', '',
             'All videos are 55 s, 25 fps, 1375 frames, with unchanged playback speed. Paths below are relative to that server root.', '',
             '| Condition / dt | Model | Task | Strict | MP4 |', '|---|---|---|---|---|']
    for row in entries:
        tier = '5e-5' if row['tier'] == 'formal_resolution' else '1e-4'
        relative = Path(row['server_video']).relative_to(server)
        lines.append(f'| {row["condition"]} / {tier} | {row["name"]} | {row["task_success"]} | {row["strict_success"]} | `{relative}` |')
    lines += ['', 'Two h1 stacked ESN (top) / matched RNN (bottom) comparisons:', '']
    lines += ['- `' + str(Path(row['server_video']).relative_to(server)) + '`' for row in comparisons]
    lines += ['', 'Per-file hashes and local playback cache paths: `MEDIA_INDEX.json`. Failures are retained.']
    (a.output/'MEDIA_INDEX.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(full_videos=len(entries), stacked_comparisons=len(comparisons))))


if __name__ == '__main__':
    main()
