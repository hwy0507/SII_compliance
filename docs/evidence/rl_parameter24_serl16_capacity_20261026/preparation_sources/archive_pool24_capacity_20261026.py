from pathlib import Path
from datetime import datetime,timezone
import subprocess,hashlib,json,tarfile
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';E=R/'docs/evidence/rl_parameter24_serl16_capacity_20261026';H=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1')
stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S');commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();archive=B/'repository'/('RL_PARAMETER24_REPLAY_CAPACITY_'+stamp);archive.mkdir()
files=[R/'AGENTS.md',R/'UPDATE_LOG.md',R/'docs/RL_PARAMETER24_SERL16_REPLAY_CAPACITY_20261026.md']+[p for p in E.rglob('*') if p.is_file()]+[R/'code/mujoco_6d_vmc_benchmark/tools'/n for n in ['parameter_replay_capacity_20261026.py','validate_parameter_replay_capacity_20261026.py','resume_cheq_capacity_pool30_20261026.py']]
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
handoff=H/('RL_PARAMETER24_REPLAY_CAPACITY_STATUS_'+stamp)
try:
 handoff.mkdir();text=f'''# 最新RL交接：参数24容量扩展 / Direct16

Goal active，未健康收敛；科学提交{commit}仅本地，GitHub认证失败。
完整交接：{R}/docs/RL_PARAMETER24_SERL16_REPLAY_CAPACITY_20261026.md
正式参数24：{B}/runs/parameter_capacity_pool30_cycle24_20261026_v1；learner {[(j['controller'],j['pid']) for j in launch['jobs']]}。
监视：{ {k:v['pid'] for k,v in mon.items()} }；必须先查原startup/capacity_boundary/完整review，不凭旧PID重启。
回放从准确最新23全state扩容1m→2m，保留旧row/RNG/优化器，持久replay_capacity_extension marker；过1m后仍保留旧数据，采样分布与环形覆盖不同。新2m上限拒绝覆盖。后续必须新capacity driver与严格marker，不能旧Replay默认加载；无自动25。
Direct16原1387783、归档1387835、review1387837，{B}/runs/serl_multistep_batch65536_cycle16_20261026_v1；保持全部state/官方8:1/32步/batch65536，不重启。无自动17。
容量准备v1维度构造错误失败保留，v2原1919323已完，三父恢复/CPU缓存/6负守卫/合成跨1m通过；正式跨界检查是否完成以原capacity_boundary/REVIEW.json为准。0辅助优化/physics，无辅助权重。
旧温度候选已完成且不支持部署，不重复；前交接保留全部失败/结果。
完整小证据包：{bundle}
SHA256：{receipt['sha256']}；{len(manifest)}成员逐hash验证。
HDD只本交接/收据，checkpoint/replay/raw/完整包仍SSD，非HDD/arm1全备份。
'''
 (handoff/'HANDOFF.md').write_text(text);(handoff/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');assert (handoff/'HANDOFF.md').read_text()==text
 tmp=H/'LATEST_RL_HANDOFF.tmp';tmp.write_text(f'# 最新RL交接\n\n{handoff}/HANDOFF.md\n\n参数24容量扩展/Direct16继续，Goal active；科学提交{commit}仅本地，大产物SSD。\n');tmp.replace(H/'LATEST_RL_HANDOFF.md');receipt.update(hdd_handoff=str(handoff/'HANDOFF.md'),hdd_small_receipts_verified=True)
except OSError as e:receipt.update(hdd_error=str(e),hdd_small_receipts_verified=False)
(E/'FINAL_ARCHIVE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
