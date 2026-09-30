"""Copy original immutable paired source; add only declared multiseed files."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
ADDITIONS=('tools/run_canonical48_paired_multiseed_20260924.py',
           'tools/run_paired_multiseed_queue_20260924.py',
           'docs/RL_PAIRED_MULTISEED_PROTOCOL_20260924.md')
ENTRY_SHA='56fd587fd95d3cbd9333c2e965bcf91a4649cd994bcc85f56081eb14640ec156'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def build(original,proof,output):
    if output.exists(): raise ValueError('Fresh output required; no overwrite')
    manifests=[json.loads((proof/m/'manifest.json').read_text()) for m in ('parameter6','direct7')]
    if manifests[0]['source_hashes']!=manifests[1]['source_hashes']: raise ValueError('Paired original sources differ')
    frozen=manifests[0]['source_hashes']
    if len(frozen)!=163: raise ValueError('Require original163 source manifest')
    for name,digest in frozen.items():
        if sha(original/name)!=digest: raise ValueError('Original source drift: '+name)
    if sha(ROOT/ADDITIONS[0])!=ENTRY_SHA: raise ValueError('Reviewed multiseed entry drift')
    for name in ADDITIONS:
        if (original/name).exists(): raise ValueError('New addition would overwrite original: '+name)
    files=[p for p in original.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    if any(p.is_symlink() for p in files): raise ValueError('Source symlinks need explicit review')
    output.mkdir(parents=True,exist_ok=False)
    dest=output/'source'
    for src in files:
        target=dest/src.relative_to(original);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
    for name in ADDITIONS:
        target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    hashes={str(p.relative_to(dest)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file()}
    for name,digest in frozen.items():
        if hashes[name]!=digest: raise ValueError('Copied original execution drift')
    for src in files:
        if hashes[str(src.relative_to(original))]!=sha(src): raise ValueError('Copied original file drift')
    record=dict(builder_sha256=sha(__file__),original_source=str(original.resolve()),original_files=len(files),original_execution_files=len(frozen),
        added={name:hashes[name] for name in ADDITIONS},files=hashes,
        proof_manifests={m:sha(proof/m/'manifest.json') for m in ('parameter6','direct7')},
        source_bytes_unchanged=True,simulations_started=0)
    (output/'BUILD.json').write_text(json.dumps(record,indent=2)+'\n')
    for path in sorted(dest.rglob('*'),reverse=True): path.chmod(0o555 if path.is_dir() else 0o444)
    dest.chmod(0o555)
    print(json.dumps(dict(source=str(dest.resolve()),files=len(hashes),original_execution_files=len(frozen),
        build_sha256=sha(output/'BUILD.json'),simulations_started=0)))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('original-source','proof-root','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.original_source.resolve(),a.proof_root.resolve(),a.output.resolve())

if __name__=='__main__':main()
