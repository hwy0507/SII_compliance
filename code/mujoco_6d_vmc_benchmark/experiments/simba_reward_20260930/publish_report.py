"""Publish small report artifacts to the existing Spark website and Git evidence."""
from pathlib import Path
import shutil,json,html,hashlib
ROOT=Path("/home/arm1/vmc_mujoco_runtime/reward_study_20260930")
REPO=Path("/home/arm1/SII_compliance_baseline")
REPORT=ROOT/"campaign_03/report"
DOC=REPO/"docs/SIMBAV2_REWARD_STUDY_20260930.md"
EVIDENCE=REPO/"docs/evidence/simba_reward_20260930"
WEB=Path("/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo")
ASSETS=WEB/"assets/simbav2_reward_20260930"
def main():
 assert DOC.exists()
 EVIDENCE.mkdir(parents=True,exist_ok=True);ASSETS.mkdir(parents=True,exist_ok=True)
 files=["REPORT.latest.md","RESULTS.latest.json","EVIDENCE_AUDIT.json","per_seed.csv","across_seed.csv","budgets.csv","training.csv","learning_curves.csv","episodes.csv","selected_metrics.png","validation_curves.png"]
 manifest={}
 for name in files:
  p=REPORT/name;assert p.is_file()
  for target in [EVIDENCE,ASSETS]:shutil.copy2(p,target/name)
  manifest[name]=dict(source=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
 portable=DOC.read_text().replace("(evidence/simba_reward_20260930/","(")
 (REPORT/"FINAL_REPORT.md").write_text(portable);(ASSETS/"FINAL_REPORT.md").write_text(portable)
 diagnostic_root=ROOT/"progress_dense_diagnostic_04"
 audit_file=diagnostic_root/"report/DIAGNOSTIC_AUDIT.json"
 diagnostic=None
 if (diagnostic_root/"COMPLETE.json").exists() and audit_file.exists():
  diagnostic=json.loads(audit_file.read_text())
  for name in ["DIAGNOSTIC_AUDIT.json","DIAGNOSTIC_AUDIT.md"]:
   p=diagnostic_root/"report"/name
   if p.exists():
    for target in [EVIDENCE,ASSETS]:shutil.copy2(p,target/name)
    manifest[name]=dict(source=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
 (EVIDENCE/"SOURCE_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
 r=json.loads((REPORT/"RESULTS.latest.json").read_text())
 body=[]
 for g in r["across_seed"]:
  if g["partition"]!="test":continue
  body.append("<tr><td>"+html.escape(g["group"])+"</td><td>"+str(g["independent_training_seeds"])+"</td>"+
   "".join("<td>%.4f ± %.4f</td>"%(g[k+"_mean"],g[k+"_seed_sd"] or 0) for k in ["rmse_cm","peak_torque_nm","peak_velocity_mps"])+"<td>0</td></tr>")
 page="""<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>SimbaV2 奖励对照 · 2026-09-30</title><style>body{max-width:1150px;margin:35px auto;padding:0 22px;font:16px/1.7 system-ui;color:#233047;background:#f6f8fb}table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px;border-bottom:1px solid #ddd;text-align:left}img{width:100%;background:white;margin:15px 0}aside{padding:16px;background:#fff3cf;border-left:4px solid #bc8300}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.8 system-ui;background:white;padding:22px}a{color:#1e5d9b}</style>
<h1>SimbaV2 Office 奖励对照</h1>
<p>主实验：8 × 100k transitions；40组验证；90条最终评测。以下为已看过的开发Office协议，不是真机或新布局盲测。</p>
<aside>两主组各18次测试均未完成任务。metric降低所选模型的RMSE，但峰值速度增加，不能说全面占优。训练几乎困在初始停稳阶段，尚不能排除训练设计导致的弱baseline。独立40k连续进度势函数诊断正在进行，结果将另列。</aside>
<h2>验证选择后 · 全55秒 · 均值 ± 训练seed标准差</h2><table><tr><th>奖励</th><th>seed数</th><th>RMSE cm</th><th>峰值力矩 Nm</th><th>峰值速度 m/s</th><th>任务成功</th></tr>"""
 page+="".join(body)+"</table>"
 if diagnostic is not None:
  page=page.replace("独立40k连续进度势函数诊断正在进行，结果将另列。","独立40k连续进度势函数诊断已经完成，结果另列如下；仍未学会完整任务。")
  page+='<h2>独立40k补充诊断 · 两训练seed · 非主实验重复验证</h2><p>每个seed固定40k、6个开发条件；24条均满55秒，表中保留全部失败（含1条物理无效回合）。均值±两个训练seed均值的样本标准差。</p><table><tr><th>奖励</th><th>RMSE cm</th><th>峰矩 Nm</th><th>峰速 m/s</th><th>完整55s</th><th>物理有效</th><th>任务成功</th></tr>'
  for g in diagnostic["across_seed"]:
   page+="<tr><td>"+html.escape(g["group"])+"</td>"
   for key in ["rmse_cm","peak_torque_nm","peak_velocity_mps"]:
    page+="<td>%.4f ± %.4f</td>"%(g[key+"_mean"],g[key+"_sd"])
   for key in ["full55_count","physical_count","task_count"]:
    page+="<td>%s/%s</td>"%(g[key],g["n_episodes"])
   page+="</tr>"
  page+='</table><p>117个已结束训练回合仍未进入抓取；不能声称探索瓶颈已解决，不能据此宣称SimbaV2本质弱于ESN。</p><p><a href="assets/simbav2_reward_20260930/DIAGNOSTIC_AUDIT.json">补充诊断逐回合审计JSON</a> · <a href="assets/simbav2_reward_20260930/DIAGNOSTIC_AUDIT.md">补充诊断审计说明</a></p>'
 for name in ["selected_metrics.png","validation_curves.png"]:page+='<img src="assets/simbav2_reward_20260930/'+name+'">'
 page+='<p>固定100k另有7条提前物理终止，详报告；不把变长失败指标当完整55秒排名。</p><p><a href="assets/simbav2_reward_20260930/FINAL_REPORT.md">完整Markdown</a> · <a href="assets/simbav2_reward_20260930/EVIDENCE_AUDIT.json">逐回合证据</a></p><details><summary>展开完整报告</summary><pre>'+html.escape(DOC.read_text())+'</pre></details></html>'
 (WEB/"simbav2_reward_20260930.html").write_text(page)
 print("http://192.168.31.70:8765/simbav2_reward_20260930.html")
if __name__=="__main__":main()
