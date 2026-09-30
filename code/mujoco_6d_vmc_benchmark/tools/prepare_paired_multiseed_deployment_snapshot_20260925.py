"""Copy existing165-source training bytes and add reviewed deployment helpers."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]
import prepare_paired_multiseed_deployment_20260925 as prep
from audit_paired_transitions_20260924 import read,require
from canonical48_paired_deployment_20260924 import sha


def build(source, manifest_path, output):
    require(not output.exists(),'Fresh snapshot required; never modify old snapshot')
    manifest=read(manifest_path);frozen=manifest['source_hashes']
    require(len(frozen)==165 and manifest['training']['seed'] in prep.SEEDS,'Need existing additional-seed165-source manifest')
    for name,value in frozen.items():
        require((source/name).resolve().is_relative_to(source) and sha(source/name)==value,'Original training bytes changed: '+name)
    additions=(*prep.ADDITIONS,prep.PROTOCOL,'tools/prepare_paired_multiseed_deployment_snapshot_20260925.py')
    files={str(p.relative_to(source)):p for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    require(not any(p.is_symlink() for p in files.values()),'No source symlinks')
    original_hashes={name:sha(path) for name,path in files.items()}
    added={}
    for name in additions:
        digest=sha(ROOT/name)
        if name in files: require(original_hashes[name]==digest,'Would overwrite original frozen source: '+name)
        else: files[name]=ROOT/name;added[name]=digest
    output.mkdir(parents=True,exist_ok=False);destination=output/'source'
    for name,path in sorted(files.items()):
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    hashes={name:sha(destination/name) for name in files}
    require(all(hashes[k]==v for k,v in original_hashes.items()),'Original copy changed')
    require(all(hashes[k]==v for k,v in frozen.items()),'Copied training165 changed')
    require(all(hashes[k]==v for k,v in added.items()),'Added helper copy changed')
    # Compile bytes directly without writing .pyc or importing simulator modules.
    for name in files:
        if name.endswith('.py'):compile((destination/name).read_bytes(),str(destination/name),'exec')
    record=dict(simulations_started=0,builder_sha256=sha(__file__),source=str(source),
        training_manifest_sha256=sha(manifest_path),original_training_source_files=165,
        original_file_count=len(original_hashes),files=hashes,added=added,source_bytes_unchanged=True)
    with (output/'BUILD.json').open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
    for path in sorted(destination.rglob('*'),reverse=True):path.chmod(0o555 if path.is_dir() else 0o444)
    destination.chmod(0o555)
    print(json.dumps(dict(source=str(destination),files=len(files),added=len(added),build_sha256=sha(output/'BUILD.json'),simulations_started=0)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('training-source','training-manifest','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();build(args.training_source.resolve(),args.training_manifest.resolve(),args.output.resolve())


if __name__=='__main__':main()
