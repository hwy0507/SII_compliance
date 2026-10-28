"""Verify git-archive file contents before publishing a new shared checkout.

Git archives encode root ownership; the shared checkout intentionally belongs to
the receiving account. Validate content, paths and modes, not uid/gid equality.
This program never extracts or overwrites an existing source directory.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def digest(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        result.update(block)
    return result.hexdigest()


def verify(archive, extracted, expected_archive_sha):
    with archive.open('rb') as stream:
        if digest(stream) != expected_archive_sha:
            raise ValueError('Archive SHA256 mismatch')
    entries = {}
    with tarfile.open(archive, 'r:') as source:
        for member in source:
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts:
                raise ValueError('Unsafe archive path')
            path = extracted / str(name)
            if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != extracted.parent):
                raise ValueError('Symlink in extracted path')
            if member.isdir():
                if not path.is_dir():
                    raise ValueError('Missing directory: ' + str(name))
                continue
            if not member.isfile() or str(name) in entries:
                raise ValueError('Nonregular or duplicate archive entry')
            with source.extractfile(member) as stream:
                expected = digest(stream)
            with path.open('rb') as stream:
                actual = digest(stream)
            if expected != actual or path.stat().st_size != member.size:
                raise ValueError('File content mismatch: ' + str(name))
            if path.stat().st_mode & 0o777 != member.mode & 0o777:
                raise ValueError('File permissions mismatch: ' + str(name))
            entries[str(name)] = actual
    actual_paths = {str(p.relative_to(extracted)) for p in extracted.rglob('*') if p.is_file() or p.is_symlink()}
    if actual_paths != set(entries):
        raise ValueError('Extracted file set differs from archive')
    return entries


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--extracted', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--publish', type=Path, required=True)
    args = parser.parse_args()
    if args.publish.exists():
        raise FileExistsError('Refusing to overwrite published source')
    entries = verify(args.archive, args.extracted, args.sha256)
    args.extracted.rename(args.publish)
    receipt = dict(archive_sha256=args.sha256, published_path=str(args.publish),
                   files_verified=len(entries), files_sha256=entries,
                   note='Content/size/mode verified; uid/gid intentionally belong to receiving account')
    with args.archive.with_suffix('.verification.json').open('x') as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps({key: value for key, value in receipt.items() if key != 'files_sha256'}))
