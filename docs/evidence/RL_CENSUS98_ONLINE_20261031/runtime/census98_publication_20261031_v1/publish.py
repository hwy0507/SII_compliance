from pathlib import Path
import subprocess,json,time,hashlib,tarfile,argparse
P=Path(__file__).resolve().parent;B=P.parents[1];R=B/'repository/SII_compliance';TAG='RL_CENSUS98_ONLINE_20261031';A=B/'repository'/TAG;E=R/'docs/evidence'/TAG
rd=lambda p:json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def digest(x):return hashlib.sha256(x).hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
parser=argparse.ArgumentParser();parser.add_argument('--stage',action='store_true');parser.add_argument('--verify-published',action='store_true');args=parser.parse_args()
paths=rd(A/'TASK_PATHS.json')['paths'];manifest=rd(E/'MANIFEST.json')['files'];receipt=rd(A/'RECEIPT.json');archive=Path(receipt['archive'])
assert digest(archive.read_bytes())==receipt['sha256']
with tarfile.open(archive) as t:
 assert len(t.getmembers())==receipt['members']
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
for x in manifest:
 data=(E/x['relative']).read_bytes();assert len(data)==x['bytes'] and digest(data)==x['sha256']
if args.stage:
 assert not git('diff','--cached','--name-only').strip()
 subprocess.run(['git','add','-f','--',*paths],cwd=R,check=True)
 assert set(git('diff','--cached','--name-only').decode().splitlines())==set(paths)
 subprocess.run(['git','diff','--cached','--check','--',*[p for p in paths if not p.endswith('.diff')]],cwd=R,check=True)
 for name in paths:assert (R/name).read_bytes()==git('show',':'+name)
 print('Staged and verified',len(paths));raise SystemExit
assert args.verify_published
commit=git('rev-parse','HEAD').decode().strip();remote=git('ls-remote','--heads','origin','refs/heads/main').decode().split()[0];assert remote==commit
assert set(git('diff-tree','--no-commit-id','--name-only','-r','HEAD').decode().splitlines())==set(paths)
checked=[]
for name in paths:
 data=(R/name).read_bytes();assert data==git('show','HEAD:'+name)==git('show',':'+name);checked.append(dict(path=name,bytes=len(data),sha256=digest(data)))
put(A/'PUBLICATION.json',dict(passed=True,time=time.time(),commit=commit,remote_main=remote,files=checked,archive_sha256=receipt['sha256'],archive_members=receipt['members'],all_task_git_and_archive_bytes_verified=True));print(commit,len(paths))
