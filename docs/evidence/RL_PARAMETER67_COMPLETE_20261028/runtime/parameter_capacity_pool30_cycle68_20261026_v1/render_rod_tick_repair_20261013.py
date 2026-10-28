"""Full repaired rollout plus an explicitly labelled rod-window close view."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/original_esn_rod_tick_20261013'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    run=OUT/'same_tick';execution=json.loads((run/'episode/execution.json').read_text())
    assert execution['status']=='complete'
    for folder,extra in [('media',[]),('rod_closeup',['--contact-closeup'])]:
        subprocess.run([sys.executable,'tools/render_office_threeview_20260929.py',
            '--rollout',str(run/'episode/rollout'),'--output',str(run/folder),
            '--label','Frozen ESN | synchronized feedback and residual',
            '--scene-label','Old cup-pillar office','--stride','1','--fps','25','--gif-stride','5',*extra],
            cwd=ROOT,env=dict(os.environ,MUJOCO_GL='egl'),check=True)
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();checks={}
    for folder in ('media','rod_closeup'):
        media=run/folder;video=media/'replay_threeview.mp4';m=json.loads((media/'manifest.json').read_text())
        assert m['frame_count']==1375 and sha(video)==m['output_sha256']['.mp4']
        output=subprocess.run([ffmpeg,'-nostdin','-v','error','-threads','1','-i',str(video),
            '-threads','1','-f','null','-','-progress','pipe:1'],capture_output=True,text=True,check=True)
        frames=[int(s.split('=')[1]) for s in output.stdout.splitlines() if s.startswith('frame=')]
        assert frames[-1]==1375 and not output.stderr.strip()
        samples={}
        for second in (12,14,17,21):
            image=media/f'inspect_{second:02d}s.png'
            subprocess.run([ffmpeg,'-nostdin','-v','error','-threads','1','-ss',str(second),
                '-i',str(video),'-frames:v','1','-threads','1','-n',str(image)],check=True)
            samples[image.name]=sha(image)
        checks[folder]=dict(frames=1375,duration_s=55.,full_decode=True,mp4_sha256=sha(video),images=samples)
    source=run/'rod_closeup/replay_threeview.mp4';clip=run/'rod_closeup/rod_window_8_to_23s.mp4'
    subprocess.run([ffmpeg,'-nostdin','-v','error','-threads','1','-ss','8','-i',str(source),
        '-t','15','-an','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-threads','1',
        '-movflags','+faststart','-n',str(clip)],check=True)
    checks['rod_clip']=dict(source_start_video_s=8.,duration_s=15.,speed=1.,
        derived_from_full_record=True,mp4_sha256=sha(clip))
    (OUT/'MEDIA_VERIFICATION.json').write_text(json.dumps(dict(videos=checks,source_sha256=sha(Path(__file__))),indent=2)+'\n')
    print(json.dumps(checks,indent=2))

if __name__=='__main__':main()
