from pathlib import Path
from datetime import datetime,timezone
import subprocess,hashlib,json,tarfile,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';E=R/'docs/evidence/rl_parameter23_serl16_temperature_20261026'
H=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1')
stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S');commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
archive=B/'repository'/('RL_PARAMETER23_TEMPERATURE_PROBE_'+stamp);archive.mkdir()
files=[R/'AGENTS.md',R/'UPDATE_LOG.md',R/'docs/RL_PARAMETER23_SERL16_TEMPERATURE_PROBE_20261026.md']
files += [p for p in E.rglob('*') if p.is_file()]
files += [R/'code/mujoco_6d_vmc_benchmark/tools'/n for n in ['serl_temperature_state_candidate_20261026.py','validate_serl_temperature_state_20261026.py','probe_serl_temperature_successor_20261026.py','review_serl_temperature_successor_probe_20261026.py']]
manifest={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files}
bundle=archive/'FULL_SMALL_EVIDENCE.tar.gz'
with tarfile.open(bundle,'w:gz') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(R)),recursive=False)
with tarfile.open(bundle,'r:gz') as tar:
 assert len(tar.getmembers())==len(manifest)
 for member in tar.getmembers():
  data=tar.extractfile(member).read();assert len(data)==manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[member.name]['sha256']
receipt=dict(scientific_commit=commit,bundle=str(bundle),sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),bytes=bundle.stat().st_size,members=len(manifest),all_members_verified=True,push_succeeded=False,remote_main='dbb1d76ed79177067c48ed49ff9f67f023c704aa',large_artifacts='SSD only; no newly verified arm1 or complete HDD backup')
(archive/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');(archive/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
handoff=H/('RL_PARAMETER23_TEMPERATURE_PROBE_STATUS_'+stamp)
try:
 handoff.mkdir()
 text=f'''# 最新RL交接：参数23 / Direct16 / 温度后继有限对照

科学提交{commit}；GitHub认证仍失败，远端最后核验dbb1d76，未发布。Goal active，未健康收敛。
完整交接：{R}/docs/RL_PARAMETER23_SERL16_TEMPERATURE_PROBE_20261026.md
参数23：{B}/runs/parameter_pool30_cycle23_20261026_v1，learner1064168/1064173/1064175，归档1064231，完整审查1064233。
Direct16：{B}/runs/serl_multistep_batch65536_cycle16_20261026_v1，learner1387783，归档1387835，完整审查1387837。
先核对原PID与最新完整review后继续；保持所有正式state，勿重复/回退/导入辅助权重。没有自动17/24。
最新完整Direct15 648282/5146264，Task/Strict0/30，仍未收敛；参数22 I18/18 A15/14 V17/17。导纳22末loss升高，23早期回落但仍须观察。
温度候选v1逐位gate失败保留、v2数值界/隔离通过，有限probe：{B}/runs/serl_cycle14_temperature_successor_probe_20261026_v1。原1094552/1162204已完，勿重跑；正式未部署。完整结果/审查决定见主交接，不导入辅助权重。
纯四正式GPU固定180样本：{B}/runs/batch16_parameter23_gpu_profile_20261026_v1/PROFILE.json；非永久瞬时保证。
完整小证据包：{bundle}
SHA256：{receipt['sha256']}，{len(manifest)}成员逐hash核验。
HDD仅本交接/收据；完整包、checkpoint/replay/raw仍SSD，不称HDD或arm1全备份。
'''
 (handoff/'HANDOFF.md').write_text(text);(handoff/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');assert (handoff/'HANDOFF.md').read_text()==text
 latest=H/'LATEST_RL_HANDOFF.md';tmp=H/'LATEST_RL_HANDOFF.tmp'
 tmp.write_text(f'# 最新RL交接\n\n{handoff}/HANDOFF.md\n\n科学提交{commit}仅本地。参数23/Direct16继续，Goal active；大产物与完整证据SSD，HDD仅小交接/收据。\n');tmp.replace(latest)
 receipt['hdd_handoff']=str(handoff/'HANDOFF.md');receipt['hdd_small_receipts_verified']=True
except OSError as e:
 receipt['hdd_error']=str(e);receipt['hdd_small_receipts_verified']=False
(E/'FINAL_ARCHIVE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
