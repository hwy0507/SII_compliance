from pathlib import Path
import subprocess,json,hashlib,tarfile,sys,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';TAG='RL_HISTORY89_VIOLATION_PIPELINE_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
phase=sys.argv[1];assert phase in ('index','HEAD')
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((E/'MANIFEST.json').read_text());receipt=json.loads((A/'RECEIPT.json').read_text());archive=Path(receipt['archive']);assert sha(archive.read_bytes())==receipt['sha256']
for row in manifest['files']:
 data=(E/row['relative']).read_bytes();assert len(data)==row['bytes'] and sha(data)==row['sha256']
 rel=(E/row['relative']).relative_to(R).as_posix();actual=git('show',(':'+rel if phase=='index' else 'HEAD:'+rel));assert actual==data,rel
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==receipt['members']
 for m in tar.getmembers():assert tar.extractfile(m).read()==(E/m.name).read_bytes()
if phase=='index':names=git('diff','--cached','--name-only','-z').decode().split('\0')
else:names=git('diff-tree','--no-commit-id','--name-only','-r','HEAD','-z').decode().split('\0')
count=0
for n in names:
 if not n:continue
 data=(R/n).read_bytes();assert git('show',(':'+n if phase=='index' else 'HEAD:'+n))==data,n;count+=1
report=dict(time=time.time(),phase=phase,manifest_files=len(manifest['files']),git_blobs=count,archive_members=receipt['members'],all_bytes_exact=True,head=git('rev-parse','HEAD').decode().strip())
with (A/('VERIFY_'+phase+'.json')).open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(report))
