"""Build a separate contact-math candidate; no edits to the parent runtime.

Only named float64 three-vector norms and geom_bodyid reads inside contact
bookkeeping are changed. All other expressions, gate thresholds and physics
calls remain. Full action-tape validation is required before deployment.
"""
import argparse
import ast
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import time

HELPER = '''\n\ndef _contact_norm3(value):
    """Internal contiguous real float64 three-vector; contact buffers only."""
    return float(np.sqrt(value.dot(value)))
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace_count(text, old, new, count=1):
    if text.count(old) != count:
        raise ValueError(f'Expected {count} source seams: {old}')
    return text.replace(old, new)


def helper(source):
    if 'def _contact_norm3(' in source:
        raise ValueError('Candidate already patched')
    return replace_count(source, 'import numpy as np\n', 'import numpy as np\n'+HELPER)


def patch_environment(source):
    start = source.index('            contact_records = data.contact\n')
    end = source.index('            if push_contact:\n', start)
    block = source[start:end]
    # Values come from np.zeros(6), np.zeros(3), or a 3x3 @ 3-vector product.
    for expression, count in [('wrench[:3]', 3), ('world_force', 1),
                              ('push_resultant', 1), ('push_all_resultant', 1)]:
        block = replace_count(block, f'float(np.linalg.norm({expression}))',
                              f'_contact_norm3({expression})', count)
    block = replace_count(block, 'model.geom_bodyid[', 'contact_body_ids[', 4)
    block = '            contact_body_ids = model.geom_bodyid\n'+block
    return helper(source[:start]+block+source[end:])


def patch_evaluator(source):
    start = source.index('        contact_records=d.contact\n')
    end = source.index('        for key,force in pair_forces.items():\n', start)
    block = source[start:end]
    for expression in ('wf[:3]', 'edge_wrench[:3]', 'corner_wrench[:3]', 'force'):
        block = replace_count(block, f'float(np.linalg.norm({expression}))',
                              f'_contact_norm3({expression})')
    block = replace_count(block, 'np.linalg.norm(world)', '_contact_norm3(world)')
    block = replace_count(block, 'm.geom_bodyid[', 'contact_body_ids[', 4)
    block = '        contact_body_ids=m.geom_bodyid\n'+block
    return helper(source[:start]+block+source[end:])


def patch_adapter(source):
    # This expression is inserted into evaluator.run, whose globals include
    # the helper. Preserve every matching seam and all injected audit logic.
    return replace_count(source, 'float(np.linalg.norm(f[:3]))', '_contact_norm3(f[:3])')


def prepare(parent, output):
    parent, output = Path(parent).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest = json.loads((parent/'SOURCE_HASHES.json').read_text())
    for relative, digest in manifest.items():
        if sha(parent/'source'/relative) != digest:
            raise ValueError('Parent source drift: '+relative)
    changes = {}
    for relative, patch in [
        ('scripts/audited_velocity_env.py', patch_environment),
        ('scripts/validate_office_apparatus_v5_20260917.py', patch_evaluator),
        ('tools/published_compliance_episode_20261025.py', patch_adapter),
    ]:
        old = (parent/'source'/relative).read_text()
        new = patch(old)
        ast.parse(new)
        changes[relative] = (old, new)
    shutil.copytree(parent, output)
    diffs = []
    for relative, (old, new) in changes.items():
        (output/'source'/relative).write_text(new)
        manifest[relative] = sha(output/'source'/relative)
        diffs.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                     fromfile='parent/'+relative, tofile='candidate/'+relative))
    (output/'CONTACT_MATH_DIFF.patch').write_text(''.join(diffs))
    (output/'SOURCE_HASHES.json').write_text(json.dumps(manifest, indent=2)+'\n')
    metadata = json.loads((parent/'RUNTIME.json').read_text())
    metadata.update(created_unix=time.time(), status='validation_only_not_deployed',
        scope='Contact math candidate, restricted vectors; no training or equivalence claim',
        parent_runtime=str(parent), parent_runtime_manifest_sha256=sha(parent/'RUNTIME.json'),
        source_snapshot_manifest_sha256=sha(output/'SOURCE_HASHES.json'),
        contact_math_builder_sha256=sha(__file__), contact_math_changed_files=list(changes),
        contact_math_diff_sha256=sha(output/'CONTACT_MATH_DIFF.patch'))
    (output/'RUNTIME.json').write_text(json.dumps(metadata, indent=2)+'\n')
    protected = [p.name for p in parent.glob('*HASHES.json') if p.name != 'SOURCE_HASHES.json']
    for name in protected:
        if sha(parent/name) != sha(output/name):
            raise AssertionError('Protected manifest changed: '+name)
    return dict(candidate=str(output), runtime_sha256=sha(output/'RUNTIME.json'),
                changed_files=list(changes), protected_manifests=protected, deployed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.parent_runtime, args.output)))
