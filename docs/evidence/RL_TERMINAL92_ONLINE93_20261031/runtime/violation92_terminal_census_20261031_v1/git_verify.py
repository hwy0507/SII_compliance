from pathlib import Path
import subprocess,json,hashlib,tarfile,time,argparse
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';TAG='RL_TERMINAL92_ONLINE93_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def digest(b):return hashlib.sha256(b).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--committed',action='store_true');args=parser.parse_args()
manifest=read(E/'MANIFEST.json')['files'];receipt=read(A/'RECEIPT.json');archive=Path(receipt['archive'])
assert digest(archive.read_bytes())==receipt['sha256']
with tarfile.open(archive) as t:
 assert len(t.getmembers())==receipt['members']
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
for x in manifest:
 data=(E/x['relative']).read_bytes();assert len(data)==x['bytes'] and digest(data)==x['sha256']
paths=git('diff-tree','--no-commit-id','--name-only','-r','HEAD').decode().splitlines() if args.committed else git('diff','--cached','--name-only').decode().splitlines()
assert len(paths)==len(manifest)+7,(len(paths),len(manifest))
checked=[]
for name in paths:
 data=(R/name).read_bytes();assert data==git('show',':'+name)
 if args.committed:assert data==git('show','HEAD:'+name)
 checked.append(dict(path=name,bytes=len(data),sha256=digest(data)))
result=dict(passed=True,time=time.time(),commit=git('rev-parse','HEAD').decode().strip(),committed=args.committed,files=checked,manifest_entries=len(manifest),tar_members=receipt['members'],archive_sha256=receipt['sha256'])
if args.committed:
 with (A/'GIT_BYTES_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(passed=True,committed=args.committed,files=len(paths),manifest_entries=len(manifest),tar_members=receipt['members'])))
