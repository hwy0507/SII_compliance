from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,tarfile,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';E=R/'docs/evidence/rl_parameter28_terminal_concentration_20261026';H=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1')
stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S');commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();archive=B/'repository'/('RL_PARAMETER28_TERMINAL_'+stamp);archive.mkdir()
files=[R/'AGENTS.md',R/'UPDATE_LOG.md',R/'docs/RL_PARAMETER28_TERMINAL_CONCENTRATION_20261026.md']+[p for p in E.rglob('*') if p.is_file() and p.name!='FINAL_ARCHIVE_RECEIPT.json']+[R/'code/mujoco_6d_vmc_benchmark/tools'/n for n in ['audit_admittance_terminal_concentration_20261026.py','review_admittance_terminal_concentration_20261026.py','track_admittance27_terminal_anchors_20261026.py']]
manifest={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files};bundle=archive/'FULL_SMALL_EVIDENCE.tar.gz'
with tarfile.open(bundle,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
with tarfile.open(bundle,'r:gz') as tar:
 assert len(tar.getmembers())==len(manifest)
 for member in tar.getmembers():
  data=tar.extractfile(member).read();assert len(data)==manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[member.name]['sha256']
receipt=dict(scientific_commit=commit,bundle=str(bundle),sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),bytes=bundle.stat().st_size,members=len(manifest),all_members_verified=True,push_succeeded=False,remote_main='dbb1d76ed79177067c48ed49ff9f67f023c704aa',large_artifacts='SSD only; not full HDD or arm1 backup')
(archive/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');(archive/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
handoff=H/('RL_PARAMETER28_TERMINAL_STATUS_'+stamp)
try:
 handoff.mkdir();launch=B/'runs/parameter_capacity_pool30_cycle28_20261026_v1/LAUNCH.json';pids={v['controller']:v['pid'] for v in json.loads(launch.read_text())['jobs']} if launch.exists() else {}
 text=f'''# 最新RL交接：参数28、Direct18与终端误差集中度

Goal active，未整体健康收敛；科学提交{commit}仅本地，GitHub认证失败。
完整交接：{R}/docs/RL_PARAMETER28_TERMINAL_CONCENTRATION_20261026.md
小证据及最新实际进度：{E}
正式Direct18原2732254、归档2732257/review2732258；参数28原PID {pids}。先查原LAUNCH/PROGRESS/REVIEW，勿重复启动。必须capacity replay+pair learner、2m历史入口23/全部正式state保持，无自动29或19训练。
新导纳25/26终端贡献v2原3292216完成：.0879478→.7292925，short0600新失败占26终端部分41.6861%；不是全部在线loss。未找到相反标签完全同critic输入，不能据此改权重/特征/LR。v1浮点减法顺序导致守卫失败原件保留；v2按原float32减法复现health，1e-9守卫不变。原27固定804终端跟踪3440440已完成：同804 masked SSE5527.899475→683.216563（下降87.64%），重点旧失败2303.516289→115.118200；旧分母下亦恢复，不仅稀释。只恢复agent权重CPU前向，0优化/物理，保存算术另核，不重跑26前向。
冻结正式16全30矩阵原1749189/1749193、review1749197仍以原结果/进程为准，固定30x55s/seed2026102626/最多33000000子步，不把部分完成写成完整，禁止重复。
Direct19等待准备3088320只等完整18后check-only，不自动训练；review调度3269262只在原18退出后复用CPU0。参数28等待3057098及27调度3269264应查原完成状态勿重跑。
完整小证据包：{bundle}
SHA256：{receipt['sha256']}；{len(manifest)}成员逐hash验证。
HDD只小交接/收据，checkpoint/replay/raw/完整包仍SSD，非HDD/arm1全备份。
'''
 (handoff/'HANDOFF.md').write_text(text);(handoff/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');assert (handoff/'HANDOFF.md').read_text()==text
 temp=H/'LATEST_RL_HANDOFF.tmp';temp.write_text(f'# 最新RL交接\n\n{handoff}/HANDOFF.md\n\n参数28/Direct18及终端误差分析，Goal active；科学提交{commit}仅本地，大产物SSD。\n');temp.replace(H/'LATEST_RL_HANDOFF.md');receipt.update(hdd_handoff=str(handoff/'HANDOFF.md'),hdd_small_receipts_verified=True)
except OSError as error:receipt.update(hdd_error=str(error),hdd_small_receipts_verified=False)
(E/'FINAL_ARCHIVE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
