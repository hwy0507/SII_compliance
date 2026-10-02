"""Stack two complete three-view replays at unchanged playback speed."""
import argparse
import json
from pathlib import Path
import subprocess
import imageio_ffmpeg
from archive_tool_campaign_20261002 import sha,write_new


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--top',type=Path,required=True);p.add_argument('--bottom',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True)
    inputs=[]
    for path in (a.top,a.bottom):
        meta=json.loads((path/'manifest.json').read_text());audit=json.loads((path/'MEDIA_AUDIT.json').read_text())
        video=path/'replay_threeview.mp4';digest=sha(video)
        assert meta['output_sha256']['.mp4']==audit['video_sha256']==digest
        assert meta['stride']==1 and meta['fps']==25 and meta['frame_count']==1375
        inputs.append(dict(directory=str(path.resolve()),manifest=meta,video_sha256=digest))
    assert inputs[0]['manifest']['input_sha256']['.mjb']==inputs[1]['manifest']['input_sha256']['.mjb']
    exe=imageio_ffmpeg.get_ffmpeg_exe();target=a.output/'comparison.mp4'
    command=[exe,'-nostdin','-n','-threads','1','-i',str(a.top/'replay_threeview.mp4'),
             '-threads','1','-i',str(a.bottom/'replay_threeview.mp4'),'-filter_complex_threads','1',
             '-filter_complex','[0:v][1:v]vstack=inputs=2[v]','-map','[v]','-an','-c:v','libx264',
             '-threads','1','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
    with (a.output/'encode.log').open('x') as f:subprocess.run(command,check=True,stdout=f,stderr=subprocess.STDOUT)
    decoder=imageio_ffmpeg.read_frames(str(target),input_params=['-threads','1'],output_params=['-threads','1'])
    meta=next(decoder);count=sum(1 for _ in decoder)
    assert count==1375 and meta['fps']==25 and abs(meta['duration']-55)<.05
    write_new(a.output/'MANIFEST.json',dict(source_sha256=sha(Path(__file__)),inputs=inputs,command=command,
        encoder_sha256=sha(Path(exe)),video_sha256=sha(target),decoded_frames=count,fps=meta['fps'],duration_s=meta['duration'],
        semantics='Top and bottom keep their original scene/task labels. Same saved MJB, real-time 55s, no dropped time or frames, no physics rerun. Rendering alone does not establish generalization or superiority.'))
    print(json.dumps(dict(frames=count,video_sha256=sha(target))))


if __name__=='__main__':main()
