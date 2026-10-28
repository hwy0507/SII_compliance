"""Decode complete videos and extract fixed-time visual inspection frames."""
import hashlib,json,subprocess
from pathlib import Path
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]/'outputs/original_esn_payload_bridge_20261013'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    receipt=ROOT/'MEDIA_VERIFICATION.json'
    if receipt.exists():raise FileExistsError(receipt)
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();rows={}
    for arm in ('path_only','path_bridge_v2','path_bridge_friction_probe'):
        media=ROOT/arm/'media';video=media/'replay_threeview.mp4'
        manifest=json.loads((media/'manifest.json').read_text())
        assert manifest['frame_count']==1375 and manifest['video_duration_s']==55.
        assert sha(video)==manifest['output_sha256']['.mp4']
        result=subprocess.run([ffmpeg,'-nostdin','-v','error','-threads','1','-i',str(video),
            '-map','0:v:0','-threads','1','-f','null','-','-progress','pipe:1'],
            text=True,capture_output=True,check=True)
        frames=[int(line.split('=')[1]) for line in result.stdout.splitlines() if line.startswith('frame=')]
        assert frames[-1]==1375
        assert not result.stderr.strip(),result.stderr
        samples={}
        for second in (13,24,35):
            image=media/f'inspect_{second:02d}s.png'
            subprocess.run([ffmpeg,'-nostdin','-v','error','-threads','1','-ss',str(second),
                '-i',str(video),'-frames:v','1','-threads','1','-n',str(image)],check=True)
            samples[image.name]=sha(image)
        rows[arm]=dict(full_decode=True,frames=frames[-1],duration_s=55.,
            mp4_sha256=sha(video),manifest_sha256=sha(media/'manifest.json'),inspection_samples=samples)
    receipt.write_text(json.dumps(dict(videos=rows,verifier_sha256=sha(Path(__file__))),indent=2)+'\n')
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
