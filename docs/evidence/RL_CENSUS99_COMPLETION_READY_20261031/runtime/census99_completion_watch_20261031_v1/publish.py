from pathlib import Path
import subprocess,json,hashlib,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';TAG='RL_CENSUS99_COMPLETION_READY_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
run=lambda args:subprocess.check_output(args,cwd=R)
sha=lambda data:hashlib.sha256(data).hexdigest()
head=run(['git','rev-parse','HEAD']).decode().strip();remote=run(['git','ls-remote','--heads','origin','refs/heads/main','refs/heads/baseline']).decode();branches={line.split()[1]:line.split()[0] for line in remote.splitlines()};assert branches['refs/heads/main']==head;assert branches['refs/heads/baseline']=='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d'
subprocess.run(['git','fetch','origin','refs/heads/main:refs/remotes/origin/main'],cwd=R,check=True);assert run(['git','rev-parse','origin/main']).decode().strip()==head
paths=[p for p in E.rglob('*') if p.is_file()]+[R/n for n in ['AGENTS.md','UPDATE_LOG.md','HANDOFF.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md',f'docs/{TAG}.md',f'docs/{TAG}_SAVE.json']]
checked=[]
for p in sorted(paths):
 rel=str(p.relative_to(R));data=p.read_bytes();blob=run(['git','show',f'origin/main:{rel}']);assert blob==data;checked.append(dict(path=rel,bytes=len(data),sha256=sha(data)))
receipt=json.loads((A/'RECEIPT.json').read_text());assert sha(Path(receipt['archive']).read_bytes())==receipt['sha256']
r=dict(passed=True,time=time.time(),commit=head,remote_main=branches['refs/heads/main'],baseline=branches['refs/heads/baseline'],files_verified=len(checked),files=checked,archive_receipt=receipt,normal_push=True)
with (A/'PUBLICATION.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(dict(passed=True,commit=head,files_verified=len(checked),archive_sha256=receipt['sha256'])))
