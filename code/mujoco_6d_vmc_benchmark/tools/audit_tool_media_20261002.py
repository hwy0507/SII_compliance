"""Decode entire diagnostic videos; verify real-time duration and media hashes."""
import argparse
import json
from pathlib import Path
import imageio_ffmpeg
from PIL import Image
from archive_tool_campaign_20261002 import sha, write_new


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directories', type=Path, nargs='+')
    a = p.parse_args()
    for path in a.directories:
        manifest = json.loads((path/'manifest.json').read_text())
        for suffix, digest in manifest['output_sha256'].items():
            assert sha(path/('replay_threeview'+suffix)) == digest
        reader = imageio_ffmpeg.read_frames(str(path/'replay_threeview.mp4'),
                    input_params=['-threads', '1'], output_params=['-threads', '1'])
        metadata = next(reader)
        selected = [49, 174, 374, 749, 1249, 1374]
        montage = Image.new('RGB', (1920, 840))
        count = 0
        for index, frame in enumerate(reader):
            if index in selected:
                i = selected.index(index)
                picture = Image.frombytes('RGB', metadata['size'], frame).resize((960, 280))
                montage.paste(picture, ((i%2)*960, (i//2)*280))
            count += 1
        assert count == manifest['frame_count'] == 1375
        assert abs(metadata['fps'] - 25) < 1e-9
        assert abs(metadata['duration'] - 55) < .05
        montage.save(path/'review_montage.png')
        write_new(path/'MEDIA_AUDIT.json', dict(
            decoded_frames=count, fps=metadata['fps'], duration_s=metadata['duration'],
            selected_frame_indices=selected, source_sha256=sha(Path(__file__)),
            video_sha256=sha(path/'replay_threeview.mp4'),
            montage_sha256=sha(path/'review_montage.png'),
            limitation='Rendering of archived failure trajectories; no new simulation or task-success claim'))
        print(str(path))


if __name__ == '__main__':
    main()
