from pathlib import Path
from datetime import datetime,timezone
import subprocess,hashlib,json,tarfile
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';E=R/'docs/evidence/rl_parameter26_serl17_prefix_20261026';H=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1')
stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S');commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();archive=B/'repository'/('RL_PARAMETER26_PHYSICAL_PREFIX_'+stamp);archive.mkdir()
files=[R/'AGENTS.md',R/'UPDATE_LOG.md',R/'docs/RL_PARAMETER26_SERL17_PHYSICAL_PREFIX_20261026.md']+[p for p in E.rglob('*') if p.is_file()]+[R/'code/mujoco_6d_vmc_benchmark/tools'/n for n in ['probe_serl_actor_floor_physical_prefix_20261026.py','serl_actor_floor_prefix_rollouts_20261026.py','review_serl_actor_floor_physical_prefix_20261026.py']]
manifest={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files};bundle=archive/'FULL_SMALL_EVIDENCE.tar.gz'
with tarfile.open(bundle,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
with tarfile.open(bundle,'r:gz') as tar:
 assert len(tar.getmembers())==len(manifest)
 for member in tar.getmembers():
  data=tar.extractfile(member).read();assert len(data)==manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[member.name]['sha256']
receipt=dict(scientific_commit=commit,bundle=str(bundle),sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),bytes=bundle.stat().st_size,members=len(manifest),all_members_verified=True,push_succeeded=False,remote_main='dbb1d76ed79177067c48ed49ff9f67f023c704aa',large_artifacts='SSD only; not a full HDD or arm1 backup')
(archive/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');(archive/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
handoff=H/('RL_PARAMETER26_PHYSICAL_PREFIX_STATUS_'+stamp)
try:
 handoff.mkdir();text=f'''# 最新RL交接：参数26 / Direct17 / 短物理前缀验证

Goal active，未健康收敛；科学提交{commit}仅本地，GitHub认证失败。
完整交接：{R}/docs/RL_PARAMETER26_SERL17_PHYSICAL_PREFIX_20261026.md
小证据：{E}
正式Direct17原4158035、归档4158038、review4158039继续；参数25完整结果和26启动信息以交接/LAUNCH/PROGRESS/REVIEW为准，先核原进程，勿重复启动。必须2m容量marker+历史23入口、pair learner及全部正式state保持，无自动18/27。
新短物理前缀使用完整16、两臂各200outer后3条件x8配对seedx2.56s，最多2457600子步；是独立登记的物理问题，不是延长旧15离线2000步预算。原400736/reviewer400737的结果与科学决定见交接，不重复、保存或推广辅助权重。
正式17/26纯GPU窗口454710须先查原PROFILE；不得拿混合辅助占用冒称纯正式。
完整小证据包：{bundle}
SHA256：{receipt['sha256']}；{len(manifest)}成员逐hash验证。
HDD只小交接/收据，checkpoint/replay/raw/完整包仍SSD，非HDD/arm1全备份。
'''
 (handoff/'HANDOFF.md').write_text(text);(handoff/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');assert (handoff/'HANDOFF.md').read_text()==text
 tmp=H/'LATEST_RL_HANDOFF.tmp';tmp.write_text(f'# 最新RL交接\n\n{handoff}/HANDOFF.md\n\n参数26/Direct17及短物理前缀审查，Goal active；科学提交{commit}仅本地，大产物SSD。\n');tmp.replace(H/'LATEST_RL_HANDOFF.md');receipt.update(hdd_handoff=str(handoff/'HANDOFF.md'),hdd_small_receipts_verified=True)
except OSError as e:receipt.update(hdd_error=str(e),hdd_small_receipts_verified=False)
(E/'FINAL_ARCHIVE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
