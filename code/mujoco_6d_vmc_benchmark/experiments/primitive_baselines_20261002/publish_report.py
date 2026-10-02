"""Publish audited development summaries on the existing LAN result page."""
import argparse,datetime,html,json
from pathlib import Path
ROOT=Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002")
WEB=Path("/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/primitive_baselines_20261002")
def esc(x):return html.escape(str(x))
def main():
    p=argparse.ArgumentParser();p.add_argument("--primitive",type=Path,default=ROOT/"final_report01");p.add_argument("--office",type=Path,default=ROOT/"office_bridge/transfer_report01");a=p.parse_args()
    WEB.mkdir(parents=True,exist_ok=True)
    for name,target in [("test_report",a.primitive),("office_report",a.office),("training_report",ROOT/"training_report01")]:
        link=WEB/name
        if not link.exists():link.symlink_to(target,target_is_directory=True)
        elif link.resolve()!=target.resolve():raise ValueError("Report link target changed")
    chunks=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Baseline 开发实验结果</title><style>body{font:16px/1.6 system-ui,sans-serif;max-width:1500px;margin:auto;padding:28px;color:#18313c;background:#f4f7f8}h1{margin-bottom:4px}h2{margin-top:32px}table{border-collapse:collapse;width:100%;background:white;font-size:14px}th,td{text-align:left;padding:10px;border:1px solid #d4dfe3}th{background:#e8f0f3}.scroll{overflow:auto}p{max-width:1100px}.muted{color:#627682}a{color:#1b657c}.ok{color:#28713d}.warn{color:#9a523b}details{margin:16px 0}summary{cursor:pointer}img{max-width:100%;height:auto}</style><h1>Baseline 开发实验结果</h1>']
    chunks+=['<p class="muted">更新时间 '+datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")+'；未完成项明确保留，不将缺失计为成功或失败。</p>',
    '<p><a href="./">四个原始场景视频</a> · <a href="office/">新综合场景视频</a> · <a href="test_report/SUMMARY.json">测试原始汇总 JSON</a> · <a href="test_report/EPISODES.csv">逐回合 CSV</a></p>',
    '<h2>四场景保留测试</h2><p>每个方法预注册 12 个条件（四场景各 3 个），保持相同物理条件。Task、Strict、实际接触与完整时长分别列出。RMSE 为完整时长回合的中位数；力矩与速度为这些回合的最大值。所有失败保留。</p>',
    '<p class="muted">本轮保留各原场景步长：球/侧面桌角 1e-4 s，棍推 5e-5 s，旧桌角 2.5e-4 s；不是统一正式步长结果。原四场景 Strict 还要求指定接触，新综合场景的 Strict 则不要求触碰所有障碍。</p>']
    primitive=a.primitive/"SUMMARY.json"
    if primitive.exists():
        data=json.loads(primitive.read_text())
        chunks+=['<p>所有列出方法的共同已完成条件：<b>'+str(len(data["common_fixture_ids"]))+'</b>。条件未齐时，请结合 JSON 中的 common_paired，勿直接比较不同覆盖范围。</p>']
        def table(summaries,scene=None):
            lines=['<div class="scroll"><table><thead><tr><th>方法</th><th>完成</th><th>Task</th><th>Strict</th><th>实际接触</th><th>完整时长</th><th>RMSE / mm</th><th>峰矩 / Nm</th><th>峰速 / m/s</th></tr></thead><tbody>']
            for identity,s in summaries.items():
                v=s["all_completed"] if scene is None else s["by_scene"][scene];n=v["total"];m=v["full_horizon_metrics"]
                metrics=["—"]*3 if not m else [f'{m["rmse_m"]["median"]*1000:.2f}',f'{m["peak_torque_nm"]["maximum"]:.2f}',f'{m["peak_speed_mps"]["maximum"]:.3f}']
                vals=[s["label"],str(n)+("/12" if scene is None else "/3"),*[str(v[k])+"/"+str(n) for k in ["task_success","strict_success","contact_exposed","full_horizon"]],*metrics]
                lines.append("<tr>"+"".join("<td>"+esc(x)+"</td>" for x in vals)+"</tr>")
            return "".join(lines)+"</tbody></table></div>"
        chunks.append(table(data["models"]))
        for scene,label in [("ball","球撞"),("push","棍推"),("corner","侧面桌角"),("table_corner","桌角")]:
            chunks+=["<details><summary>"+label+"：分场景成绩</summary>",table(data["models"],scene),"</details>"]
    else:chunks.append("<p>最终测试尚未汇总。</p>")
    chunks+=['<h2>固定新综合场景迁移</h2><p>main 7cd5f4b 的同一归档模型，55 s、dt=1e-4 s。本组只有一个综合条件，不能据此估计泛化成功率。固定参数使用统一旧 BO 先验，学习方法从四场景迁移；原 ESN 为不同训练经历的历史参考。</p>']
    office=a.office/"SUMMARY.json"
    if office.exists():
        data=json.loads(office.read_text());chunks.append('<div class="scroll"><table><tr><th>方法</th><th>Task</th><th>Strict</th><th>完整时长</th><th>最终阶段</th><th>RMSE / mm</th><th>峰矩 / Nm</th><th>峰速 / m/s</th><th>外穿透 / mm</th></tr>')
        for r in data["rows"]:
            vals=[r["id"],r["task"],r["strict"],r["full_horizon"],r["stage"],*[f"{r[k]:.3f}" for k in ["rmse_mm","peak_torque_nm","peak_speed_mps","external_penetration_mm"]]]
            chunks.append("<tr>"+"".join("<td>"+esc(x)+"</td>" for x in vals)+"</tr>")
        chunks+=['</table></div><p class="muted">未完成：'+esc(", ".join(r["id"] for r in data["missing"]) or "无")+'</p><p><a href="office_report/SUMMARY.json">综合场景逐项接触与结果 JSON</a> · <a href="office_report/EPISODES.csv">综合场景 CSV</a></p>']
        for name in ["historical_reference","direct_rl","admittance","impedance","vmc"]:
            if (a.office/(name+".png")).exists():chunks+=['<details><summary>'+esc(name.replace("_"," "))+'：物块轨迹与任务进度</summary><img src="office_report/'+name+'.png"></details>']
    chunks+=['<h2>训练和解释边界</h2><p>直接 RL 两种 reward 使用固定 60,000 步 checkpoint，各两颗 seed；在线调参使用三类控制器共同达到的周期 checkpoint，按预注册规则锁定，不根据测试分数挑选。参数先验每种控制器仅一组，四场景共用。</p><p>学习预算有限，不宣称收敛。第一颗 direct seed 的两种 reward 均在 21,525 步遇到相同命令解析故障，从 20,000 步恢复；每条恢复训练额外发生的 1,525 次物理交互保留并计账。局部储能限制不构成机器人整体无源性证明。</p><p>没有碰撞的回合仍留在任务分母中，但不能当作成功的碰撞恢复。低 RMSE 也可能来自停滞；应结合任务进度、真实接触和最终放置。</p><p><a href="training_report/TRAINING_STATUS.json">训练记录</a> · <a href="training_report/training_diagnostics.png">训练曲线（不是测试成绩）</a></p></html>']
    (WEB/"results.html").write_text("".join(chunks))
    print("http://192.168.31.70:8765/primitive_baselines_20261002/results.html")
if __name__=="__main__":main()
