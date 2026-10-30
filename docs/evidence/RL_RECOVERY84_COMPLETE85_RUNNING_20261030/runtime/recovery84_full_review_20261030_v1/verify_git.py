from pathlib import Path
import hashlib,json,subprocess,time,sys
B=Path(__file__).resolve().parents[2];R=B/'repository/SII_compliance';TAG='RL_RECOVERY84_COMPLETE85_RUNNING_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
mode=sys.argv[1];assert mode in ['index','commit'];base=':' if mode=='index' else 'HEAD:'
def cmd(args):return subprocess.check_output(['git']+args,cwd=R)
manifest=json.loads((E/'MANIFEST.json').read_text());count=0
for r in manifest['files']:
 p=E/r['relative'];rel=str(p.relative_to(R));data=cmd(['show',base+rel]);assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],rel;count+=1
extra=[E/'MANIFEST.json',R/'docs'/(TAG+'.md'),R/'docs'/(TAG+'_SAVE.json'),R/'AGENTS.md',R/'UPDATE_LOG.md',R/'HANDOFF.md',R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']
for p in extra:assert cmd(['show',base+str(p.relative_to(R))])==p.read_bytes();count+=1
changed=cmd(['diff','--cached','--name-only','-z'] if mode=='index' else ['diff-tree','--no-commit-id','--name-only','-r','-z','HEAD']).split(b'\0');changed=[p.decode() for p in changed if p]
assert len(changed)==count,(len(changed),count)
for rel in changed:
 data=cmd(['show',base+rel]);assert len(data)<10_000_000,rel
r=dict(passed=True,time=time.time(),manifest_entries=len(manifest['files']),all_target_blobs_verified=count,changed_files=len(changed),mode=mode,head=cmd(['rev-parse','HEAD']).decode().strip(),large_git_blobs=False)
with (A/(mode.upper()+'_REVIEW.json')).open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r))
