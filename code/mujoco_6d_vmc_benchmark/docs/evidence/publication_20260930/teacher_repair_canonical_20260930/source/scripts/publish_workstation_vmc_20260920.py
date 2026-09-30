"""Publish finalized contact-wise VMC teachers and a reproducible run index."""
from concurrent.futures import ThreadPoolExecutor
import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/workstation_teacher_release_20260920';WEB=ROOT/'web_demo'
LABELS={'rod':'持续棍推','rear':'后挡板单接触','front':'前挡板单接触','combined':'棍推＋后侧夹具组合'}


def main():
    summary=json.loads((OUT/'summary.json').read_text())
    if not summary['all_primary_contacts_covered'] or not all(summary['completed_campaigns'].values()):
        raise RuntimeError('Required contact searches are not complete')
    asset=WEB/'assets/workstation_vmc_20260920';asset.mkdir(parents=True,exist_ok=True)
    def render(group):
        selected=summary['selected'][group];source=Path(selected['row']['result']).parent
        focus=selected['row']['focus'] if group in ('front','rear') else 'push_rod_geom'
        # The final media use the correct force channel for the shown task.
        cmd=[sys.executable,str(ROOT/'scripts/render_panel_push_20260920.py'),str(source),'--contact-object',focus]
        subprocess.run(cmd,cwd=ROOT,env=dict(os.environ,MUJOCO_GL='egl',OPENBLAS_NUM_THREADS='1'),check=True)
        dest=asset/group;dest.mkdir(exist_ok=True)
        for name in ('rollout.mp4','rollout.gif','rollout.json','start.png','frame_050.png','frame_100.png'):
            shutil.copy2(source/name,dest/name)
        for name in ('controller.json','task_and_fixture.json','selected_metrics.json','reproduce.json'):
            shutil.copy2(OUT/'profiles'/group/name,dest/name)
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(render,LABELS))
    for name in ('summary.json','metrics.csv','teacher_candidate_manifest.json','teacher_pareto_manifest.json'):
        shutil.copy2(OUT/name,asset/name)
    total=sum(v['evaluated'] for v in summary['coverage'].values())
    invalid=summary['coverage']['front_superseded_target']['evaluated']
    candidates=json.loads((OUT/'teacher_candidate_manifest.json').read_text());elites=json.loads((OUT/'teacher_pareto_manifest.json').read_text())
    table=[];parameter_rows=[];videos=[];detail=[]
    for group,label in LABELS.items():
        selected=summary['selected'][group];r=selected['row'];coverage=summary['coverage'][group]
        def force(name):return r['contacts'].get(name,{}).get('peak_resultant_force_n',0.)
        def fmt(v):return f'{v:.1f}' if v>.05 else '—'
        table.append(f'<tr><td>{label}</td><td>{coverage["accepted"]}/{coverage["unique_conditions_and_parameters"]}</td><td>{fmt(force("push_rod_geom"))}</td><td>{fmt(force("push_back_guard"))}</td><td>{fmt(force("push_front_guard"))}</td><td>{r["endpoint_error_m"]*1000:.2f}</td><td>{r["speed_p95_mps"]:.3f}/{r["speed_peak_mps"]:.3f}</td><td>{r["torque_peak_nm"]:.2f}</td></tr>')
        cfg=selected['parameters']['controller'];env=selected['parameters']['environment']
        parameter_rows.append(f'<tr><td>{label}</td><td>{cfg["stiffness_6d"]}</td><td>{cfg["damping_6d"]}</td><td>{cfg["axis_rotation_rpy"]}</td></tr>')
        if group!='combined':
            videos.append(f'<details><summary>{label}：完整 24 秒</summary><p>{"推杆保持退出，标定固定挡板接触。" if group in ("front","rear") else "推杆持续推入；夹具始终参与物理仿真。"}</p><video controls playsinline preload="metadata" src="assets/workstation_vmc_20260920/{group}/rollout.mp4" poster="assets/workstation_vmc_20260920/{group}/start.png"></video><p><a href="assets/workstation_vmc_20260920/{group}/rollout.gif">GIF</a> · <a href="assets/workstation_vmc_20260920/{group}/controller.json">完整 VMC 参数</a> · <a href="assets/workstation_vmc_20260920/{group}/reproduce.json">复现命令</a></p></details>')
        contact_rows=[]
        for name,c in r['contacts'].items():
            if c['peak_point_force_n']<=.05:continue
            purpose='有意抓持（不当作需要消除的障碍接触）' if name=='target_object_geom' else ', '.join(c['bodies'])
            contact_rows.append(f'<tr><td>{html.escape(name)}</td><td>{c["peak_resultant_force_n"]:.2f}</td><td>{c["peak_point_force_n"]:.2f}</td><td>{c["resultant_impulse_ns"]:.3f}</td><td>{c["duration_s"]:.3f}</td><td>{html.escape(purpose)}</td></tr>')
        detail.append(f'<details><summary>{label}：所有实际接触、参数和任务定义</summary><table><tr><th>接触对象</th><th>合力峰值 N</th><th>单点峰值 N</th><th>合力冲量 Ns</th><th>正接触累计 s</th><th>机器人部位／用途</th></tr>{"".join(contact_rows)}</table><p>阶段目标位置误差 RMSE：{r["trajectory_rmse_after_contact_m"]*1000:.1f} mm；接触后统计，参考为当前阶段目标点，并非另跑无障碍时间轨迹的偏差。最大数值压入：{r["max_penetration_m"]*1000:.3f} mm。</p><pre>{html.escape(json.dumps(dict(controller=cfg,fixture=env),indent=2))}</pre></details>')
    page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>开放式取件工位 · VMC 接触标定</title>
<style>body{{max-width:1180px;margin:28px auto;padding:0 20px;background:#111923;color:#e5edf5;font:16px/1.7 system-ui}}h1{{font-size:28px}}h2{{font-size:22px}}video{{width:100%;border-radius:10px;background:#06090d}}a{{color:#8bd5ff}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:8px 10px;border-bottom:1px solid #354556;text-align:left}}.scroll{{overflow:auto}}.note{{padding:16px 20px;background:#20354a;border-radius:8px}}details{{margin:16px 0;padding:12px 16px;background:#182532;border-radius:8px}}summary{{cursor:pointer;font-size:18px;font-weight:600}}pre{{overflow:auto;font-size:13px}}</style>
<h1>开放式取件定位工位：VMC 接触参数标定</h1>
<p>2026-09-20 · 托盘定位边、带支座的前后夹具、地面安装的导向推杆。保留已认可的夹爪接触区域；新增实体均参与碰撞，移动推杆滑座增加真实质量。</p>
<div class="note">四类主要工况均已找到可用 teacher。每个回合使用一套固定 6D VMC 参数，不按碰撞对象或时钟临时切换。这里的“最优”指本轮有限搜索中，经可行性筛选和 Pareto 比较后选出的候选，不代表全局最优，也不代表已完成真实机器人验证。</div>
<h2>完整组合任务：棍推 → 夹具约束 → 持物滑移与抬升</h2>
<video controls playsinline preload="metadata" src="assets/workstation_vmc_20260920/combined/rollout.mp4" poster="assets/workstation_vmc_20260920/combined/start.png"></video>
<p>左侧实体工位；右侧仅将挡板透明显示，便于观察接触。两侧轨迹和物理碰撞完全相同。<a href="assets/workstation_vmc_20260920/combined/rollout.gif">完整 GIF</a> · <a href="assets/workstation_vmc_20260920/combined/controller.json">组合任务参数</a></p>
<h2>各接触工况分别标定</h2><p>表中力是每个命名障碍物对机器人的合力峰值；“—”表示该回合未发生对应的有效接触，不能解释为已证明其柔顺性。不同工况的推压与目标位置不同，不可直接用跨行数值比较算法优劣。</p>
<div class="scroll"><table><tr><th>工况</th><th>通过/去重候选</th><th>棍 N</th><th>后板 N</th><th>前板 N</th><th>最终误差 mm</th><th>速度 P95/峰值 m/s</th><th>力矩峰值 Nm</th></tr>{"".join(table)}</table></div>
{"".join(videos)}
<h2>每类工况选定的六维 VMC 参数</h2><p>数组前 3 项为平移，后 3 项为旋转。K 的单位分别为 N/m、Nm/rad；D 为 Ns/m、Nms/rad。完整质量、限幅、滤波和增益在各组 JSON 中。有些工况选中相同参数，这是搜索结果，没有为了区分而人为改动。</p>
<div class="scroll"><table><tr><th>工况</th><th>K</th><th>D</th><th>主轴 RPY（rad）</th></tr>{"".join(parameter_rows)}</table></div>
<h2>搜索范围与数据去向</h2><p>完成 {total} 条标定/搜索回合，其中 {invalid} 条旧前板任务因目标接近固定姿态的工作空间边界而被替代，不进入算法比较或 teacher 数据。另有早期结构 smoke 检查，不计入此表。搜索覆盖独立六维刚度、阻尼、虚拟质量、力/力矩限幅、主轴方向、滤波与位移反馈增益，并对前后板优胜参数各做四组局部复扫。</p>
<p>去重后保留 {len(candidates)} 条可行 teacher 候选，其中 {len(elites)} 条属于各自工况的 Pareto 集。重复物理条件/参数不会被当作新数据量。当前仍是开发标定集，尚未训练 MLP/ESN，也不是正式泛化测试集。</p>
<p><a href="assets/workstation_vmc_20260920/metrics.csv">全部指标 CSV</a> · <a href="assets/workstation_vmc_20260920/summary.json">选择与覆盖统计</a> · <a href="assets/workstation_vmc_20260920/teacher_candidate_manifest.json">可行 teacher 清单</a> · <a href="assets/workstation_vmc_20260920/teacher_pareto_manifest.json">Pareto teacher 清单</a></p>
<h2>所有实际接触均保留审计</h2><p>夹具正面、托架边缘、支座、导轨、桌面和有意抓持分别记录。夹爪与夹具边缘的接触进入力和冲量目标；上游连杆误撞夹具、撞桌面或驱动器外壳的回合被排除。有意夹持物块的力单独记录，不能通过松开夹爪来降低指标。接触累计时长不等于连续接触时长。</p>{"".join(detail)}
<p>四组 teacher 是按离线工况选出的固定参数配置；部署动作仍来自本体力觉估计，没有读取仿真接触对象标签或视觉几何。名义目标与推杆条件、控制参数均可从复现文件追溯。</p></html>'''
    (WEB/'workstation_vmc_20260920.html').write_text(page)
    old=WEB/'raised_hand_slide_20260920.html';archive=WEB/'raised_hand_before_workstation_20260920.html'
    if old.exists() and not archive.exists():shutil.copy2(old,archive)
    old.write_text(page)
    print('http://192.168.31.70:8765/workstation_vmc_20260920.html',flush=True)


if __name__=='__main__':main()
