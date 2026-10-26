from pathlib import Path
from datetime import datetime,timezone
import subprocess,hashlib,json,tarfile
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';E=R/'docs/evidence/rl_reward_stability_frozen16_20261026';H=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1')
stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S');commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();archive=B/'repository'/('RL_REWARD_STABILITY_FROZEN16_'+stamp);archive.mkdir()
files=[R/'AGENTS.md',R/'UPDATE_LOG.md',R/'docs/RL_REWARD_STABILITY_AND_FROZEN16_20261026.md']+[p for p in E.rglob('*') if p.is_file() and p.name!='FINAL_ARCHIVE_RECEIPT.json']+[R/'code/mujoco_6d_vmc_benchmark/tools'/n for n in ['audit_serl_reward_stability_20261026.py','audit_serl_reward_terms_20261026.py','audit_parameter_reward_stability_20261026.py','review_serl_frozen_matrix_20261026.py']]
manifest={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files};bundle=archive/'FULL_SMALL_EVIDENCE.tar.gz'
with tarfile.open(bundle,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
with tarfile.open(bundle,'r:gz') as tar:
 assert len(tar.getmembers())==len(manifest)
 for member in tar.getmembers():
  data=tar.extractfile(member).read();assert len(data)==manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[member.name]['sha256']
receipt=dict(scientific_commit=commit,bundle=str(bundle),sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),bytes=bundle.stat().st_size,members=len(manifest),all_members_verified=True,push_succeeded=False,remote_main='dbb1d76ed79177067c48ed49ff9f67f023c704aa',large_artifacts='SSD only; not a full HDD or arm1 backup')
(archive/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');(archive/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
handoff=H/('RL_REWARD_STABILITY_FROZEN16_STATUS_'+stamp)
try:
 handoff.mkdir();text=f'''# 最新RL交接：回报稳定性审计、完整冻结16、参数27/Direct18继续运行

Goal active，未整体健康收敛；科学提交{commit}仅本地，GitHub认证失败。
完整交接：{R}/docs/RL_REWARD_STABILITY_AND_FROZEN16_20261026.md
小证据及实际最新进度：{E}
Direct13–16原审计1643450、奖励分项1910037已结束。末三均值变化均<5%，28条件改善但配对差+.134343区间跨零；改善主要减小穿透/峰矩惩罚，13和16全30停approach。回报趋稳不等于学会任务，不重跑审计。
冻结正式16完整30条件：{B}/runs/serl_cycle16_frozen_full30_20261026_v1；原evaluator1749189/1749193、review1749197，固定30x55s/seed2026102626/最多33000000子步，无优化/replay写入。先查原结果/进程，不重复，不把分片/部分完成写成完整。
原参数26和Direct17已完整结束，27等待准备1633945、18等待准备1660818已完成勿重跑。当前正式参数27 I2286139/A2286140/V2286141、Direct18 2732254。实际进度以完整交接与各LAUNCH/PROGRESS/REVIEW为准，禁止因旧PID退出重复训练。保留所有state、2m replay历史入口23，capacity+pair恢复。参数24–26审计原1811254先查结果勿重跑。没有自动下一轮授权标记替代科学审查。
完整小证据包：{bundle}
SHA256：{receipt['sha256']}；{len(manifest)}成员逐hash验证。
HDD只小交接/收据，checkpoint/replay/raw/完整包仍SSD，非HDD/arm1全备份。
'''
 (handoff/'HANDOFF.md').write_text(text);(handoff/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');assert (handoff/'HANDOFF.md').read_text()==text
 tmp=H/'LATEST_RL_HANDOFF.tmp';tmp.write_text(f'# 最新RL交接\n\n{handoff}/HANDOFF.md\n\n回报稳定性审计及完整冻结16，Goal active；科学提交{commit}仅本地，大产物SSD。\n');tmp.replace(H/'LATEST_RL_HANDOFF.md');receipt.update(hdd_handoff=str(handoff/'HANDOFF.md'),hdd_small_receipts_verified=True)
except OSError as e:receipt.update(hdd_error=str(e),hdd_small_receipts_verified=False)
(E/'FINAL_ARCHIVE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
