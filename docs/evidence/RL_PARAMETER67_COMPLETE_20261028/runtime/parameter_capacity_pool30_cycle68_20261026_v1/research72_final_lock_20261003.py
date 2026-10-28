"""Freeze declared finalists without opening sealed condition contents.

Final selection is supplied from completed development evidence, with every
seed and every failure retained. This tool does not choose policies by success.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def amendment_hashes(root):
    """Freeze all explicit protocol changes together with the original protocol."""
    amendments={}
    protocol_sha=sha(root/'PROTOCOL.json')
    for path in sorted(root.glob('AMENDMENT_*.json')):
        assert not path.is_symlink()
        assert read(path)['protocol_sha256']==protocol_sha
        amendments[path.name]=sha(path)
    return amendments


def runtime_hashes(source):
    """Exact runnable source/asset set, excluding interpreter-generated caches."""
    result={}
    for folder in ('scripts','tools','assets'):
        for f in (source/folder).rglob('*'):
            if any(x in ('__pycache__','outputs') for x in f.relative_to(source).parts) or f.suffix=='.pyc':continue
            assert not f.is_symlink(), 'Runtime symlinks are not frozen: '+str(f)
            if f.is_file():result[str(f.relative_to(source))]=sha(f)
    assert result
    return result


def authorize_final_read(root,lock_path,expected,source,output):
    """Every entry point, including a direct queue invocation, checks before read."""
    lock,protocol=verify_lock(root,lock_path,expected)
    assert runtime_hashes(source)==lock['runtime_source_sha256'], 'Runtime file set/content changed'
    receipt=read(root/'FINAL_UNSEAL_RECEIPT.json')
    assert receipt['model_lock_sha256']==expected
    assert receipt['sealed_condition_sha256']==protocol['sealed_condition_sha256']
    assert receipt['protocol_sha256']==sha(root/'PROTOCOL.json')
    assert Path(receipt['output']).resolve()==output.resolve()
    assert sha(root/'sealed/HELDOUT.json')==protocol['sealed_condition_sha256']
    return lock,protocol


def verify_candidates(candidates):
    assert 1<=len(candidates)<=64
    assert len({c['name'] for c in candidates})==len(candidates)
    for c in candidates:
        assert re.fullmatch('[a-zA-Z0-9_.-]+',c['name']) and c['name'] not in ('.','..')
        selectors=sum(bool(c.get(k)) for k in ('checkpoint','controller','adapted_rl','nominal'))
        assert selectors<=1 and 'rl_case' not in c
        assert selectors or c['category']=='enhanced_teacher'
        assert isinstance(c.get('config',{}),dict)
        if c.get('checkpoint'):
            assert sha(c['checkpoint'])==c['checkpoint_sha256']
            if c.get('training_metadata_sha256'):
                assert sha(Path(c['checkpoint']).parent/'TRAINING_COMPLETE.json')==c['training_metadata_sha256']
        if c.get('adapted_rl'):
            from research72_checkpoint_20261003 import checkpoint_hashes
            rl=c['adapted_rl'];manifest=read(rl['manifest'])
            assert sha(rl['manifest'])==rl['manifest_sha256']
            assert manifest['checkpoint']==rl['checkpoint']
            assert checkpoint_hashes(rl['checkpoint'])==manifest['hashes']
            assert sha(manifest['training_protocol'])==manifest['training_protocol_sha256']
            training=read(manifest['training_protocol'])
            assert sha(Path(rl['parameter_source'])/'PRIORS.json')==training['prior_file_sha256']


def verify_lock(root,path,expected):
    assert sha(path)==expected, 'Final model lock changed'
    lock=read(path);protocol=read(root/'PROTOCOL.json')
    assert lock['schema']=='sii-research72-final-lock-v1'
    assert lock['training_closed'] is True and lock['all_registered_finalists_included'] is True
    assert lock['protocol_sha256']==sha(root/'PROTOCOL.json')
    assert lock['amendment_sha256']==amendment_hashes(root), 'Protocol amendments changed'
    assert lock['sealed_condition_sha256']==protocol['sealed_condition_sha256']
    assert datetime.fromisoformat(lock['frozen_utc'])<=datetime.now(timezone.utc)
    verify_candidates(lock['candidates'])
    return lock,protocol


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--finalists',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve()
    protocol=read(root/'PROTOCOL.json');selection=read(a.finalists)
    assert selection['protocol_sha256']==sha(root/'PROTOCOL.json')
    assert selection['selection_uses_only_train_validation_development'] is True
    assert selection['all_registered_finalists_included'] is True
    assert selection['incomplete_or_failed_training_disclosed'] is True
    assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists(), 'Final conditions already opened; no re-freezing'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(protocol['dispatch_deadline_utc'])
    candidates=selection['candidates'];verify_candidates(candidates)
    seeds=set(protocol['budget_caps']['training_seeds'])
    learned={'esn','memoryless','ordinary_mlp','ordinary_rnn','matched_mlp','matched_rnn'}
    rl=set(protocol['budget_caps']['rl_families'])
    required=learned|rl|{'enhanced_teacher','classical_admittance','classical_impedance','classical_vmc','nominal_zero'}
    assert required<={c['category'] for c in candidates}, 'Missing registered family in final matrix'
    for family in learned|rl:
        assert {c['seed'] for c in candidates if c['category']==family}==seeds, 'Missing seed: '+family
    grouped=[]
    for group in selection['paired_seed_groups']:
        members=[c for c in candidates if c['name'] in group['names']]
        assert len(members)==len(seeds) and {c['seed'] for c in members}==seeds
        assert len({c['category'] for c in members})==1, 'Seed group mixes methods'
        assert len({c.get('variant') for c in members})==1, 'Seed group mixes selected losses'
        grouped.extend(group['names'])
    assert len(grouped)==len(set(grouped))
    assert set(grouped)=={c['name'] for c in candidates if c['category'] in learned|rl}
    for evidence in selection['development_evidence']:
        assert sha(evidence['path'])==evidence['sha256']
    assert selection['completion_receipts']
    for evidence in selection['completion_receipts']:
        assert sha(evidence['path'])==evidence['sha256']
        assert read(evidence['path'])['status']=='complete'
    source=Path(__file__).resolve().parents[1]
    source_hashes=runtime_hashes(source)
    lock=dict(schema='sii-research72-final-lock-v1',frozen_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=sha(root/'PROTOCOL.json'),sealed_condition_sha256=protocol['sealed_condition_sha256'],
        amendment_sha256=amendment_hashes(root),
        candidates=candidates,paired_seed_groups=selection['paired_seed_groups'],
        selection_sha256=sha(a.finalists),development_evidence=selection['development_evidence'],
        completion_receipts=selection['completion_receipts'],
        training_closed=True,all_registered_finalists_included=True,
        incomplete_or_failed_training_disclosed=True,runtime_source_sha256=source_hashes,
        rules='All frozen finalists run all24 sealed conditions. No strict-success eligibility filter, final-condition fitting, environment or gate change. Missing/aborted executions remain in the denominator ledger.')
    with a.output.open('x') as f:
        json.dump(lock,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(models=len(candidates),lock_sha256=sha(a.output),sealed_contents_read=False)))


if __name__=='__main__':main()
