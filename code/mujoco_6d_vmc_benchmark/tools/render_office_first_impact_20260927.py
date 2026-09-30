"""Reportable saved-state first-impact replay; no dynamics integration."""
import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('MUJOCO_GL', 'egl')
os.environ.setdefault('MPLBACKEND', 'Agg')
import imageio_ffmpeg
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--preview-only', action='store_true')
    a = p.parse_args()
    case = ROOT / 'outputs/esn_office_r34_stress_20260927/results/r34_hard'
    report = json.loads((case / 'rollout.json').read_text())
    assert digest(case / 'rollout.mjb') == report['model_sha256']
    model = mujoco.MjModel.from_binary_path(str(case / 'rollout.mjb'))
    data = mujoco.MjData(model)
    with np.load(case / 'rollout.npz') as z:
        trace = {key: z[key].copy() for key in ('mocap_pos', 'mocap_quat', 'neuron_time', 'observation', 'applied_action')}
    with np.load(case / 'rollout_ball_detail.npz') as z:
        detail = {key: z[key].copy() for key in z.files}
    data.mocap_pos[:] = trace['mocap_pos'][0]
    data.mocap_quat[:] = trace['mocap_quat'][0]
    ball = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'office_v5_ball_geom')
    hand = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'hand_collision')
    depths = []
    for q in detail['qpos']:
        data.qpos[:] = q
        mujoco.mj_fwdPosition(model, data)
        depths.append(max([0.] + [-float(c.dist) * 1000 for c in data.contact[:data.ncon]
                                  if {int(c.geom1), int(c.geom2)} == {ball, hand}]))
    depths = np.array(depths)
    peak = int(np.argmax(depths))
    logged_peak = report['stats']['max_external_penetration_m'] * 1000
    assert abs(depths[peak] - logged_peak) < 1e-6
    a.output.mkdir(parents=True, exist_ok=False)
    model.vis.global_.offwidth = 768
    model.vis.global_.offheight = 576
    model.vis.headlight.ambient[:] = .65
    model.vis.headlight.diffuse[:] = .8
    renderer = mujoco.Renderer(model, height=576, width=768)
    cameras = []
    for lookat, distance, azimuth, elevation in [([.64, -.02, .45], 2.5, 135, -20),
                                                  ([.54, -.26, .625], .45, 5, -5)]:
        cam = mujoco.MjvCamera()
        cam.lookat[:] = lookat
        cam.distance, cam.azimuth, cam.elevation = distance, azimuth, elevation
        cameras.append(cam)
    font = {size: ImageFont.truetype(FONT, size) for size in (17, 19, 22, 28)}
    prop = FontProperties(fname=FONT, size=9)
    plt.rcParams.update({'font.size': 9, 'axes.unicode_minus': False})
    fig, ax = plt.subplots(figsize=(5.12, 1.92), dpi=100, facecolor='#101a27')
    ax.set_facecolor('#101a27')
    # The logger becomes sparse after force contact ends. Do not bridge
    # missing states with a visually fabricated continuous curve.
    segments = np.split(np.arange(len(depths)), np.flatnonzero(np.diff(detail['time']) > 2 * .0000015625) + 1)
    for segment in segments:
        ax.plot(detail['time'][segment] * 1000, depths[segment], color='#61d4ed', lw=1.7,
                marker='.' if len(segment) == 1 else None, markersize=3)
    ax.axhline(.2, color='#ff7777', ls='--', lw=1)
    ax.set(xlim=(54.95, 55.65), ylim=(0, .24))
    ax.set_xlabel('存档位姿时间 / ms', fontproperties=prop, color='white', labelpad=1)
    ax.set_ylabel('穿透 / mm', fontproperties=prop, color='white', labelpad=1)
    ax.text(55.63, .202, '0.2 mm门槛', fontproperties=prop, color='#ff9999', ha='right', va='bottom')
    ax.tick_params(colors='white', labelsize=8)
    for spine in ax.spines.values():
        spine.set_color('#587086')
    fig.subplots_adjust(left=.13, right=.98, bottom=.25, top=.95)
    fig.canvas.draw()
    chart = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert('RGB')
    chart.save(a.output / 'penetration_curve.png')
    transform = ax.transData
    times = detail['time']
    pre = np.flatnonzero(times < .05495)[::2]
    event = np.flatnonzero((times >= .05495) & (times <= .05565))[::4]
    post = np.flatnonzero((times > .05565) & (times <= .1001))[::2]
    selected = sorted(set(np.r_[pre, event, post, peak].tolist()))
    if a.preview_only:
        selected = [peak]
    else:
        selected = [selected[0]] * 10 + selected + [selected[-1]] * 30
    writer = None
    if not a.preview_only:
        writer = imageio_ffmpeg.write_frames(str(a.output / 'first_impact.mp4'), (1280, 864), fps=20,
            codec='libx264', pix_fmt_out='yuv420p', output_params=['-threads', '1', '-movflags', '+faststart'])
        writer.send(None)
    gif_frames, frame_records = [], []
    first_contact = report['stats']['events']['ball']['first_s']
    last_contact = report['stats']['events']['ball']['last_s']
    first_nonzero_index = np.flatnonzero(np.any(trace['observation'][:, 39:45] != 0, axis=1))[0]
    first_nonzero_time = float(trace['neuron_time'][first_nonzero_index])
    try:
        for i in selected:
            t = float(times[i])
            data.qpos[:] = detail['qpos'][i]
            data.time = t
            mujoco.mj_fwdPosition(model, data)
            im = Image.new('RGB', (1280, 864), '#101a27')
            draw = ImageDraw.Draw(im)
            draw.text((20, 8), 'R34 · 强球撞 · 存档回放（未重跑物理）', font=font[28], fill='white')
            draw.text((20, 49), f'完整55秒任务：成功   |   严格门：失败（{logged_peak:.6f} > 0.200000 mm）',
                      font=font[22], fill='#ffca82')
            for panel, camera in enumerate(cameras):
                renderer.update_scene(data, camera=camera)
                view = Image.fromarray(renderer.render())
                if panel == 0:
                    im.paste(view.resize((512, 384)), (0, 88))
                else:
                    im.paste(view, (512, 88))
            draw.text((15, 98), '办公室全景', font=font[19], fill='white', stroke_width=1, stroke_fill='black')
            draw.text((528, 98), '手—球接触近景（几何未夸大变形）', font=font[19], fill='white', stroke_width=1, stroke_fill='black')
            current_chart = chart.copy()
            chart_draw = ImageDraw.Draw(current_chart)
            if 54.95 <= t * 1000 <= 55.65:
                x, y = transform.transform((t * 1000, depths[i]))
                y = 192 - y
                chart_draw.line((x, 12, x, 147), fill='#ccd6e2', width=1)
                chart_draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill='#ff7777' if depths[i] > .2 else '#ffca82')
            im.paste(current_chart, (0, 472))
            draw = ImageDraw.Draw(im)
            tick = max(0, int(np.searchsorted(trace['neuron_time'], t + 1e-10, side='right') - 1))
            observation = trace['observation'][tick]
            action = trace['applied_action'][tick]
            draw.text((20, 674), f'当前存档时间 {t*1000:.5f} ms    重建穿透 {depths[i]:.6f} mm', font=font[22], fill='white')
            draw.text((20, 710), f'最近策略采样 {trace["neuron_time"][tick]*1000:.0f} ms：'
                      f'估计力 {np.linalg.norm(observation[39:42]):.3f} N · '
                      f'估计力矩 {np.linalg.norm(observation[42:45]):.3f} Nm · 最大动作幅值 {np.max(np.abs(action)):.4f}',
                      font=font[19], fill='#9ae7f1')
            xcoord = lambda value: 20 + 1240 * value / .1
            draw.line((20, 790, 1260, 790), fill='#536c85', width=4)
            draw.rectangle((xcoord(first_contact), 781, xcoord(last_contact), 799), fill='#ffae66')
            draw.text((xcoord(first_contact) - 145, 750), '球撞 55.06–55.51 ms', font=font[19], fill='#ffca82')
            for sample in (0., .04, .08):
                x = xcoord(sample)
                draw.line((x, 780, x, 803), fill='#61d4ed', width=2)
                draw.text((min(1190, max(20, x - 18)), 804), f'{sample*1000:.0f} ms', font=font[17], fill='white')
            draw.text((xcoord(.08) - 90, 750), '首个非零观测 80 ms', font=font[19], fill='#9ae7f1')
            x = xcoord(t)
            draw.ellipse((x - 5, 785, x + 5, 795), fill='white')
            draw.text((20, 837), '非匀速慢放 · 曲线断处无密集存档，不插值 · 接触真值只用于诊断，未输入ESN', font=font[17], fill='#c3cedb')
            if i == peak:
                im.save(a.output / 'peak_frame.png')
            if writer:
                writer.send(np.asarray(im))
                gif_frames.append(im.resize((960, 648)).convert('P', palette=Image.Palette.ADAPTIVE, colors=128))
            frame_records.append(dict(source_index=int(i), time_s=t, reconstructed_depth_mm=float(depths[i]),
                                      last_actor_sample_s=float(trace['neuron_time'][tick]), actor_action=action.tolist()))
    finally:
        if writer:
            writer.close()
        renderer.close()
        plt.close(fig)
    if gif_frames:
        gif_frames[0].save(a.output / 'first_impact.gif', save_all=True, append_images=gif_frames[1:], duration=50, loop=0, optimize=False)
    np.savez_compressed(a.output / 'reconstructed_geometry.npz', configuration_time_s=times, depth_mm=depths)
    manifest = dict(render_only=True, physics_rerun=False, preview_only=a.preview_only,
                    source_sha256=digest(Path(__file__)), first_nonzero_wrench_observation_s=first_nonzero_time,
                    reconstructed_peak_mm=float(depths[peak]), recorded_episode_peak_mm=logged_peak,
                    absolute_peak_difference_mm=float(abs(depths[peak] - logged_peak)), frames=frame_records,
                    input_sha256={p.name: digest(p) for p in (case / 'rollout.json', case / 'rollout.npz', case / 'rollout.mjb', case / 'rollout_ball_detail.npz')},
                    output_sha256={p.name: digest(p) for p in a.output.iterdir() if p.is_file()},
                    caveats=['Nonuniform replay speed; video frame number is not simulation time.',
                             'Curve segments do not bridge stored-state gaps larger than two fine physics steps; no dense motion is fabricated after force contact ends.',
                             'Position-only forward calculation reconstructs contact geometry, not dynamic forces.',
                             'Saved qpos is post-integration; original contact stats use cached pre-integration geometry. Their timestamps can differ by one1.5625us step.',
                             'This replay covers only the first100ms; full55s task outcome is from the archived complete rollout.',
                             'No calibration or material/gate modification is implied.'])
    (a.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: v for k, v in manifest.items() if k not in ('frames', 'input_sha256', 'output_sha256')}, indent=2))


if __name__ == '__main__':
    main()
