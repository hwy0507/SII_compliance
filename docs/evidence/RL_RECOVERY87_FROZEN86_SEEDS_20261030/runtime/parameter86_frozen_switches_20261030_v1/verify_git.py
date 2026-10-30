"""Check the frozen evidence snapshot against every staged or committed blob."""
from pathlib import Path
import json,hashlib,subprocess,sys,ast
B=Path(__file__).resolve().parents[2];R=B/'repository/SII_compliance';TAG='RL_RECOVERY87_FROZEN86_SEEDS_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
revision=sys.argv[1] if len(sys.argv)>1 else ':'
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def shab(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((E/'MANIFEST.json').read_text())
for row in manifest['files']:
 p=E/row['relative'];data=p.read_bytes();assert len(data)==row['bytes'] and shab(data)==row['sha256'],str(p)
files=[str(p.relative_to(R)) for p in E.rglob('*') if p.is_file()]+['AGENTS.md','UPDATE_LOG.md','HANDOFF.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md','docs/'+TAG+'.md','docs/'+TAG+'_SAVE.json']
if revision==':':
 staged=git('diff','--cached','--name-only','-z').decode().rstrip('\0').split('\0');assert set(staged)==set(files),(set(staged)-set(files),set(files)-set(staged))
for name in files:
 prefix=':' if revision==':' else revision+':'
 assert git('show',prefix+name)==(R/name).read_bytes(),name
 if name.endswith('.py'):ast.parse((R/name).read_text())
receipt=dict(passed=True,revision=revision,manifest_files=len(manifest['files']),verified_git_blobs=len(files),all_bytes_exact=True)
out=A/('GIT_INDEX_REVIEW.json' if revision==':' else 'GIT_COMMIT_REVIEW.json');out.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
