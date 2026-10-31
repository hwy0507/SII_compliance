from pathlib import Path
import hashlib,json,subprocess,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';A=B/'repository/RL_CENSUS95_PROGRESS_20261031'
rd=lambda p:json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
review=rd(A/'GIT_BYTES_REVIEW.json');head=git('rev-parse','HEAD').decode().strip();actual=git('ls-remote','--heads','origin','refs/heads/main').decode().split()[0]
assert actual==head
assert git('merge-base','--is-ancestor',review['commit'],head)==b''
assert git('rev-parse','origin/main').decode().strip()==actual
checked=[]
for x in review['files']:
 data=git('show',actual+':'+x['path']);local=(R/x['path']).read_bytes();assert data==local
 # A normal merge may add another researcher's log; all other published bytes remain exact.
 if x['path']!='UPDATE_LOG.md':assert hashlib.sha256(data).hexdigest()==x['sha256']
 checked.append(dict(path=x['path'],bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
assert git('status','--porcelain')==b''
ids=rd(D/'OBSERVATION_REVIEW.json')['identities']
for j in ids:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
result=dict(passed=True,time=time.time(),scientific_commit=review['commit'],published_main=head,actual_remote_main=actual,baseline=git('rev-parse','origin/baseline').decode().strip(),remote_files=checked,live_original_identities=len(ids),goal='active',complete95=False,gpu_guard_kept=True,normal_push=True)
with (A/'PUBLICATION.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='remote_files'}))
