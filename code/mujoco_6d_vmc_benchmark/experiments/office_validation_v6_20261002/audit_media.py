"""Verify complete native-speed media, decoded frames and archived inputs."""
import hashlib,json
from pathlib import Path
import imageio_ffmpeg
from PIL import Image
ROOT=Path('/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rows=[]
    for ident in ['zero','esn_original_v2','parameter_impedance','direct_metric_74001']:
        p=ROOT/ident/'media';m=json.loads((p/'manifest.json').read_text())
        for ext,h in m['input_sha256'].items():assert sha(ROOT/ident/('rollout'+ext))==h
        for ext,h in m['output_sha256'].items():assert sha(p/('replay_threeview'+ext))==h
        count,seconds=imageio_ffmpeg.count_frames_and_secs(str(p/'replay_threeview.mp4'))
        assert count==1375 and abs(seconds-55)<.001 and m['fps']==25
        with Image.open(p/'replay_threeview.gif') as gif:
            duration=0
            for i in range(gif.n_frames):gif.seek(i);duration+=gif.info['duration']
            assert gif.n_frames==275 and duration==55000
        rows.append(dict(id=ident,decoded_mp4_frames=count,mp4_seconds=seconds,gif_seconds=duration/1000,hashes_verified=True))
    (ROOT/'MEDIA_AUDIT.json').write_text(json.dumps(dict(status='passed',rows=rows),indent=2))
    print(json.dumps(rows))
if __name__=='__main__':main()

