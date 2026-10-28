"""Prepare an isolated contact-access candidate; never edit a frozen parent.

Only replace per-contact Python wrappers with per-substep array views. Contact
order, force calls, arithmetic, dt and all audits remain. Validation is required
before this candidate can be considered for any training runtime.
"""
import argparse
import ast
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('Expected one source seam: '+old)
    return source.replace(old, new)


def patch_environment(source):
    start = source.index('            for contact_index in range(data.ncon):')
    end = source.index('            if push_all_contact and self.push_rod_hold_end_s', start)
    block = source[start:end]
    block = once(block, '                contact = data.contact[contact_index]\n', '')
    for field in ('geom1', 'geom2', 'frame'):
        block = block.replace('contact.'+field, 'contact_'+field+'[contact_index]')
    if block.count('contact.dist') != block.count('float(contact.dist)'):
        raise ValueError('Environment contact distance conversion changed')
    block = block.replace('float(contact.dist)', 'float(contact_dist[contact_index])')
    for field in ('includemargin', 'solref', 'solimp'):
        block = block.replace('contact.'+field, 'contact_records[contact_index].'+field)
    if 'contact.' in block:
        raise ValueError('Unmapped contact field')
    prefix = ('            contact_records = data.contact\n'
              '            contact_geom1, contact_geom2 = contact_records.geom1, contact_records.geom2\n'
              '            contact_dist, contact_frame = contact_records.dist, contact_records.frame\n')
    return source[:start]+prefix+block+source[end:]


def patch_evaluator(source):
    start = source.index('        for i in range(d.ncon):')
    end = source.index('        for key,force in resultant.items():', start)
    block = source[start:end]
    block = once(block, '            ct=d.contact[i];g1,g2=int(ct.geom1),int(ct.geom2)',
                 '            g1,g2=int(contact_geom1[i]),int(contact_geom2[i])')
    block = block.replace('float(ct.dist)', 'float(contact_dist[i])')
    block = block.replace('ct.dist', 'float(contact_dist[i])')
    block = block.replace('ct.frame', 'contact_frame[i]')
    if 'ct.' in block:
        raise ValueError('Unmapped evaluator contact field')
    prefix = ('        contact_records=d.contact\n'
              '        contact_geom1,contact_geom2=contact_records.geom1,contact_records.geom2\n'
              '        contact_dist,contact_frame=contact_records.dist,contact_records.frame\n')
    return source[:start]+prefix+block+source[end:]


def main(args):
    parent, output = args.parent_runtime.resolve(), args.output.resolve()
    hashes = json.loads((parent/'SOURCE_HASHES.json').read_text())
    for relative, digest in hashes.items():
        if sha(parent/'source'/relative) != digest:
            raise ValueError('Parent source drift: '+relative)
    if output.exists():
        raise FileExistsError(output)
    changes = {}
    for relative, patch in [
        ('scripts/audited_velocity_env.py', patch_environment),
        ('scripts/validate_office_apparatus_v5_20260917.py', patch_evaluator),
    ]:
        old = (parent/'source'/relative).read_text()
        new = patch(old)
        ast.parse(new)
        changes[relative] = (old, new)
    relative = 'tools/published_compliance_episode_20261025.py'
    old = (parent/'source'/relative).read_text()
    if old.count('world=ct.frame.reshape(3,3).T@f[:3]*(1 if g2 in robot else -1)') != 2:
        raise ValueError('Episode adapter seam changed')
    new = old.replace('world=ct.frame.reshape(3,3).T@f[:3]*(1 if g2 in robot else -1)',
                      'world=contact_frame[i].reshape(3,3).T@f[:3]*(1 if g2 in robot else -1)')
    ast.parse(new)
    changes[relative] = (old, new)
    shutil.copytree(parent, output)
    diffs = []
    for relative, (old, new) in changes.items():
        (output/'source'/relative).write_text(new)
        hashes[relative] = sha(output/'source'/relative)
        diffs.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                     fromfile='parent/'+relative, tofile='candidate/'+relative))
    (output/'CONTACT_ACCESS_DIFF.patch').write_text(''.join(diffs))
    (output/'SOURCE_HASHES.json').write_text(json.dumps(hashes, indent=2)+'\n')
    metadata = json.loads((parent/'RUNTIME.json').read_text())
    metadata.update(created_unix=time.time(), status='validation_only_not_deployed',
        scope='Contact-access candidate; no training dispatch or physical-equivalence claim',
        parent_runtime=str(parent), parent_runtime_manifest_sha256=sha(parent/'RUNTIME.json'),
        source_snapshot_manifest_sha256=sha(output/'SOURCE_HASHES.json'),
        contact_candidate_builder_sha256=sha(__file__),
        contact_candidate_changed_files=list(changes),
        contact_candidate_diff_sha256=sha(output/'CONTACT_ACCESS_DIFF.patch'))
    (output/'RUNTIME.json').write_text(json.dumps(metadata, indent=2)+'\n')
    for name in ('PARAMETER_HASHES.json', 'ROBOT_ASSET_HASHES.json', 'PUBLISHED_HASHES.json'):
        if (parent/name).exists() and sha(parent/name) != sha(output/name):
            raise AssertionError('Protected manifest changed: '+name)
    print(json.dumps(dict(candidate=str(output), runtime_sha256=sha(output/'RUNTIME.json'),
        changed_files=list(changes), deployed=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args())
