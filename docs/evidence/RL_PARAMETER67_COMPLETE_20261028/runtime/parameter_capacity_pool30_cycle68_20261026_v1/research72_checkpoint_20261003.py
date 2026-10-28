"""Hash complete official RL checkpoints, including nested optimizer state."""
import hashlib
from pathlib import Path


def checkpoint_hashes(directory):
    directory = Path(directory).resolve()
    files = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlink in checkpoint: '+str(path))
        if path.is_file():
            digest = hashlib.sha256()
            with path.open('rb') as f:
                for block in iter(lambda: f.read(1024*1024), b''):
                    digest.update(block)
            files[str(path.relative_to(directory))] = digest.hexdigest()
    assert 'official_agent_state.json' in files
    for component in ('actor', 'critic', 'target_critic', 'temperature', 'obs_norm', 'rew_norm'):
        assert any(k.startswith(component+'/') for k in files), 'Missing checkpoint component: '+component
    return files
