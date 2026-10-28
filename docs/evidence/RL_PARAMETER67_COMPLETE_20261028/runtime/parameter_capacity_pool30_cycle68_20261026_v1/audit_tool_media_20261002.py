"""Decode entire diagnostic videos; verify real-time duration and media hashes."""
import argparse
import json
from pathlib import Path
import imageio_ffmpeg
import numpy as np
from PIL import Image
from archive_tool_campaign_20261002 import sha, write_new


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directories', type=Path, nargs='+')
    p.add_argument('--allow-aborted',action='store_true',help='Verify original short aborted rollouts at their actual duration, never pad to 55s')
    a = p.parse_args()
    for path in a.directories:
        manifest = json.loads((path/'manifest.json').read_text())
        for suffix, digest in manifest['output_sha256'].items():
            assert sha(path/('replay_threeview'+suffix)) == digest
        reader = imageio_ffmpeg.read_frames(str(path/'replay_threeview.mp4'),
                    input_params=['-threads', '1'], output_params=['-threads', '1'])
        metadata = next(reader)
        selected = [49, 174, 374, 749, 1249, 1374]
        expected_count=1375;expected_duration=55.;abort_reason=None
        if a.allow_aborted:
            record=Path(manifest['record'])
            assert sha(record.with_suffix('.json'))==manifest['input_sha256']['.json']
            summary=json.loads(record.with_suffix('.json').read_text())
            if not summary['full_task_horizon_completed']:
                abort_reason=summary['abort_reason'];assert abort_reason and not summary['task_success'] and not summary['strict_success']
                assert manifest['stride']==1 and manifest['fps']==25
                assert sha(record)==manifest['input_sha256']['.npz']
                with np.load(record) as z:
                    expected_count=len(z['time']);expected_duration=expected_count/25
                    np.testing.assert_allclose(z['time'],np.arange(1,expected_count+1)/25,rtol=0,atol=1e-6)
                selected=np.linspace(0,expected_count-1,6).astype(int).tolist()
        montage = Image.new('RGB', (1920, 840))
        count = 0
        for index, frame in enumerate(reader):
            if index in selected:
                i = selected.index(index)
                picture = Image.frombytes('RGB', metadata['size'], frame).resize((960, 280))
                montage.paste(picture, ((i%2)*960, (i//2)*280))
            count += 1
        assert count == manifest['frame_count'] == expected_count
        assert abs(metadata['fps'] - 25) < 1e-9
        assert abs(metadata['duration'] - expected_duration) < .05
        montage.save(path/'review_montage.png')
        write_new(path/'MEDIA_AUDIT.json', dict(
            decoded_frames=count, fps=metadata['fps'], duration_s=metadata['duration'],
            expected_duration_s=expected_duration,abort_reason=abort_reason,short_abort_preserved=abort_reason is not None,
            selected_frame_indices=selected, source_sha256=sha(Path(__file__)),
            video_sha256=sha(path/'replay_threeview.mp4'),
            montage_sha256=sha(path/'review_montage.png'),
            limitation='Rendering of archived trajectories; task/safety conclusions come from independent physics audits, not video appearance'))
        print(str(path))


if __name__ == '__main__':
    main()
