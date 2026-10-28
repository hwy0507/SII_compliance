"""Reuse full three-angle state replay and decode audit on the new candidate."""
import render_rod_tick_repair_20261013 as renderer


def main():
    # The renderer expects OUT/same_tick. Use a separate rendering adapter
    # below instead of changing historical source or its output paths.
    import json,os,subprocess,sys
    from pathlib import Path
    import imageio_ffmpeg
    root=Path(__file__).resolve().parents[1]
    out=root/'outputs/original_esn_rod_opposition_20261013'
    assert json.loads((out/'episode/execution.json').read_text())['status']=='complete'
    subprocess.run([sys.executable,'tools/render_office_threeview_20260929.py',
        '--rollout',str(out/'episode/rollout'),'--output',str(out/'media'),
        '--label','Frozen ESN | measured motor-friction candidate','--scene-label','Old cup-pillar office',
        '--stride','1','--fps','25','--gif-stride','5','--contact-closeup'],
        cwd=root,env=dict(os.environ,MUJOCO_GL='egl'),check=True)
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();video=out/'media/replay_threeview.mp4'
    manifest=json.loads((out/'media/manifest.json').read_text())
    assert manifest['frame_count']==1375 and renderer.sha(video)==manifest['output_sha256']['.mp4']
    decoded=subprocess.run([ffmpeg,'-nostdin','-v','error','-threads','1','-i',str(video),
        '-threads','1','-f','null','-','-progress','pipe:1'],capture_output=True,text=True,check=True)
    frames=[int(s.split('=')[1]) for s in decoded.stdout.splitlines() if s.startswith('frame=')]
    assert frames[-1]==1375 and not decoded.stderr.strip()
    images={}
    for second in (12,14,17,21):
        image=out/'media'/f'inspect_{second:02d}s.png'
        subprocess.run([ffmpeg,'-nostdin','-v','error','-threads','1','-ss',str(second),'-i',str(video),
            '-frames:v','1','-threads','1','-n',str(image)],check=True)
        images[image.name]=renderer.sha(image)
    clip=out/'media/rod_window_8_to_23s.mp4'
    subprocess.run([ffmpeg,'-nostdin','-v','error','-threads','1','-ss','8','-i',str(video),
        '-t','15','-an','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-threads','1',
        '-movflags','+faststart','-n',str(clip)],check=True)
    receipt=dict(frames=1375,duration_s=55.,fps=25,full_decode=True,
        source_sha256=renderer.sha(Path(__file__)),mp4_sha256=renderer.sha(video),
        clip_sha256=renderer.sha(clip),clip_start_video_s=8.,clip_duration_s=15.,clip_speed=1.,images=images)
    (out/'MEDIA_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
