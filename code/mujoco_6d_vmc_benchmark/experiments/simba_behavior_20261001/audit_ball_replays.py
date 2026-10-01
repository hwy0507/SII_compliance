"""Read-only evidence extraction for campaign_01 case_000 ball video audit.
Run on Spark using the reward_study_20260930/venv_gpu interpreter.
Existing MP4-derived frame sheets/clips are hashed; no physics is rerun.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import imageio_ffmpeg

ROOT = Path('/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001')
WEB = Path('/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo')
MEDIA = WEB / 'assets/ball_replay_audit_20261001'
METHODS = ['office_task_seed61001', 'metric_seed61001', 'esn', 'zero']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    evidence = {'scope': 'campaign_01, 100k checkpoint, seed61001 RL, case_000; development protocol',
                'physics_rerun': False, 'methods': {},
                'frame_sheet_original_indices_zero_based': list(range(8, 16)),
                'slow_clip_original_indices_zero_based': list(range(7, 21)),
                'slow_clip_speed_relative_to_original': 0.25,
                'limitations': ['No interpolated or new collision frames.',
                    'ball_detail covers t < 0.30 s, but launch is at 2 s.',
                    'Contact durations/peaks alone cannot establish physical realism.',
                    'Shared MJB does not imply shared contact exposure or body part.']}
    for method in METHODS:
        folder = ROOT / 'campaign_01/evaluation' / method / 'case_000'
        source = ROOT / 'campaign_01/media' / method
        summary = json.loads((folder / 'rollout.json').read_text())
        behavior = json.loads((folder / 'BEHAVIOR.json').read_text())
        manifest = json.loads((source / 'manifest.json').read_text())
        with np.load(folder / 'rollout.npz') as raw, np.load(folder / 'rollout_ball_detail.npz') as detail:
            frame_dt = float(np.median(np.diff(raw['time']))) * manifest['stride']
            reader = imageio_ffmpeg.read_frames(str(source / 'replay.mp4'))
            metadata = next(reader)
            reader.close()
            assert sha(source / 'replay.mp4') == manifest['output_sha256']['.mp4']
            assert sha(folder / 'rollout.mjb') == manifest['input_sha256']['.mjb']
            mask = (raw['time'] >= 1.95) & (raw['time'] <= 2.65)
            files = [folder / f for f in ['rollout.json', 'rollout.npz', 'rollout.mjb', 'rollout_ball_detail.npz', 'BEHAVIOR.json']]
            files += [source / 'replay.mp4', source / 'manifest.json', MEDIA / (method + '.jpg'), MEDIA / (method + '_slow.mp4')]
            evidence['methods'][method] = {
                'file_sha256': {str(f): sha(f) for f in files},
                'source_video_metadata': metadata,
                'frame_simulation_dt_s': frame_dt,
                'original_simulation_speed': frame_dt * metadata['fps'],
                'sheet_simulation_times_s': raw['time'][np.arange(8, 16)*manifest['stride']].tolist(),
                'ball_launch_time_s': summary['ball_launch_time_s'],
                'ball_event': summary['stats']['events'].get('ball'),
                'ball_behavior': next(x for x in behavior['event_results'] if x['obstacle_id'] == 'ball'),
                'detail_time_range_s': [float(detail['time'][0]), float(detail['time'][-1])],
                'detail_sample_count': len(detail['time']),
                'detail_contact_samples': int(np.count_nonzero(detail['contact'])),
                'trajectory': {'time': raw['time'][mask].tolist(), 'position': raw['ball'][mask].tolist(), 'velocity': raw['ball_velocity'][mask].tolist()}}
    validator = ROOT / 'frozen_main_01/code/mujoco_6d_vmc_benchmark/scripts/validate_office_apparatus_v5_20260917.py'
    evidence['validator'] = {'path': str(validator), 'sha256': sha(validator), 'high_rate_condition': 'if t<.30 and (t>=next_ball_sample or touch_ball):'}
    out = ROOT / 'campaign_01/report/BALL_REPLAY_AUDIT_20261001.json'
    out.write_text(json.dumps(evidence, indent=2) + '\n')
    print(out)
    for method, row in evidence['methods'].items():
        print(method, row['frame_simulation_dt_s'], row['source_video_metadata']['fps'], row['ball_event'], row['detail_time_range_s'])

if __name__ == '__main__':
    main()
