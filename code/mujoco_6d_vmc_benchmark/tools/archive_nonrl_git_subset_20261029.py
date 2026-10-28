"""Package a committed source/evidence subset, verifying every Git blob.

Does not include raw physics, environments or models. Refuses existing output
and records the exact commit; no extraction and no remote computation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile


def main(commit, output):
    repo=Path(__file__).resolve().parents[3]
    commit=subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=repo,text=True).strip()
    assert not output.exists()
    paths=['code/mujoco_6d_vmc_benchmark/scripts',
           'code/mujoco_6d_vmc_benchmark/tools',
           'docs/NONRL_TEACHER_VELOCITY_UNITS_20261029.md',
           'docs/NONRL_INTENT_RECOVERY_20261029.md',
           'docs/NONRL_SPECIAL_REGRESSION_REPAIR_20261028.md',
           'docs/EVALUATION_STANDARD_SPT_20261025.md',
           'docs/evidence/NONRL_INTENT_RECOVERY_20261029']
    tree=subprocess.check_output(['git','ls-tree','-r','-z',commit,'--',*paths],cwd=repo)
    expected={}
    for entry in tree.split(b'\0'):
        if not entry:continue
        metadata,name=entry.split(b'\t',1)
        mode,kind,oid=metadata.decode().split()
        assert kind=='blob' and mode in ('100644','100755')
        expected[name.decode()]=(mode,oid)
    output.mkdir(parents=True)
    archive=output/'SOURCE_AND_EVIDENCE.tar.gz'
    subprocess.run(['git','archive','--format=tar.gz','--output='+str(archive),commit,'--',*paths],cwd=repo,check=True)
    verified={}
    with tarfile.open(archive,'r:gz') as stream:
        for member in stream:
            if member.isdir():continue
            assert member.isfile() and member.name in expected and member.name not in verified
            data=stream.extractfile(member).read()
            mode,oid=expected[member.name]
            actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            assert actual==oid and len(data)==member.size
            assert bool(member.mode & 0o111)==(mode=='100755')
            verified[member.name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),git_blob=oid)
    assert set(verified)==set(expected)
    result=dict(status='locally_verified_pending_share',commit=commit,archive=str(archive),
        bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        files=len(verified),scope='Committed benchmark scripts/tools and selected nonRL reports/small evidence only. Not complete repository, raw physics, model weights, environment, or in-flight results.',
        members=verified)
    (output/'LOCAL_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v for k,v in result.items() if k!='members'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();main(args.commit,args.output.resolve())
