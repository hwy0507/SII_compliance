from pathlib import Path
from datetime import datetime,timezone
import subprocess,hashlib,json,tarfile
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';E=R/'docs/evidence/rl_actor_floor_parameter25_20261026';H=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1')
stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S');commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();archive=B/'repository'/('RL_ACTOR_FLOOR_PARAMETER25_'+stamp);archive.mkdir()
files=[R/'AGENTS.md',R/'UPDATE_LOG.md',R/'docs/RL_PARAMETER25_SERL16_ACTOR_FLOOR_20261026.md']+[p for p in E.rglob('*') if p.is_file()]+[R/'code/mujoco_6d_vmc_benchmark/tools'/n for n in ['serl_actor_entropy_floor_candidate_20261026.py','validate_serl_actor_entropy_floor_20261026.py','probe_serl_actor_entropy_floor_20261026.py','review_serl_actor_entropy_floor_probe_20261026.py','review_parameter_cycles19_24_20261026.py']]
manifest={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files};bundle=archive/'FULL_SMALL_EVIDENCE.tar.gz'
with tarfile.open(bundle,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
with tarfile.open(bundle,'r:gz') as tar:
 assert len(tar.getmembers())==len(manifest)
 for member in tar.getmembers():
  data=tar.extractfile(member).read();assert len(data)==manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[member.name]['sha256']
receipt=dict(scientific_commit=commit,bundle=str(bundle),sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),bytes=bundle.stat().st_size,members=len(manifest),all_members_verified=True,push_succeeded=False,remote_main='dbb1d76ed79177067c48ed49ff9f67f023c704aa',large_artifacts='SSD only; not a full HDD or arm1 backup')
(archive/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');(archive/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
launch=json.loads((B/'runs/parameter_capacity_pool30_cycle24_20261026_v1/LAUNCH.json').read_text());mon=json.loads((B/'runs/parameter_capacity_pool30_cycle24_20261026_v1/MONITORS.json').read_text())
handoff=H/('RL_ACTOR_FLOOR_PARAMETER25_STATUS_'+stamp)
try:
 handoff.mkdir();text=f'''# 最新RL交接：参数25 / Direct17 / actor熵下限对照

Goal active，未健康收敛；科学提交{commit}仅本地，GitHub认证失败。
完整交接：{R}/docs/RL_PARAMETER25_SERL16_ACTOR_FLOOR_20261026.md
小证据：{E}
实际参数24跨1m审查通过，全旧row/marker/history保留，新reward误差0；后续必须capacity driver和严格marker，不用默认1m Replay恢复。新2m上限拒绝覆盖。原24和新25当前状态必须读完整交接及各自LAUNCH/PROGRESS/REVIEW后判断，勿据历史PID重复启动。
Direct16已完整审查，最新完整父16；正式17原4158035从准确16全state接续，归档4158038/review4158039；不导入辅助权重。原官方10critic/random2 bootstrap/actor all10mean/noentropy/8:1/32步保持。
actor floor0.1候选gate/probe已有限完成；只改变有效actor系数，原温度及优化器保留。结果和科学决定见完整交接，不重复两臂、不保存或推广辅助权重。
六周期汇总只读既有审查，不重跑神经推理/物理。准备和监视原进程先核验，避免重复。
完整小证据包：{bundle}
SHA256：{receipt['sha256']}；{len(manifest)}成员逐hash验证。
HDD仅小交接/收据，checkpoint/replay/raw/完整包仍SSD，非HDD/arm1全备份。
'''
 (handoff/'HANDOFF.md').write_text(text);(handoff/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');assert (handoff/'HANDOFF.md').read_text()==text
 tmp=H/'LATEST_RL_HANDOFF.tmp';tmp.write_text(f'# 最新RL交接\n\n{handoff}/HANDOFF.md\n\n参数25/Direct17及actor熵对照，Goal active；科学提交{commit}仅本地，大产物SSD。\n');tmp.replace(H/'LATEST_RL_HANDOFF.md');receipt.update(hdd_handoff=str(handoff/'HANDOFF.md'),hdd_small_receipts_verified=True)
except OSError as e:receipt.update(hdd_error=str(e),hdd_small_receipts_verified=False)
(E/'FINAL_ARCHIVE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
