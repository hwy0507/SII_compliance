from pathlib import Path
import json,hashlib,subprocess,sys
B=Path(__file__).resolve().parents[2];R=B/'repository/SII_compliance';TAG='RL_HISTORY87_PERSISTENT_CRITIC_INTERFACE_20261030';E=R/'docs/evidence'/TAG
revision=sys.argv[1];manifest=json.loads((E/'MANIFEST.json').read_text());checked=0
for item in manifest['files']:
 p=E/item['relative'];rel=str(p.relative_to(R));data=subprocess.check_output(['git','show',(':'+rel if revision=='index' else revision+':'+rel)],cwd=R)
 assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'] and data==p.read_bytes();checked+=1
paths=[str((E/'MANIFEST.json').relative_to(R)),'AGENTS.md','UPDATE_LOG.md','HANDOFF.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md','docs/'+TAG+'.md','docs/'+TAG+'_SAVE.json']
for rel in paths:
 data=subprocess.check_output(['git','show',(':'+rel if revision=='index' else revision+':'+rel)],cwd=R);assert data==(R/rel).read_bytes();checked+=1
print(json.dumps(dict(passed=True,revision=revision,manifest_entries=len(manifest['files']),git_blobs_verified=checked)))
