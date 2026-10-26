from pathlib import Path
import collections
import hashlib
import json
import statistics
import subprocess
import time

B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R = B / 'repository/SII_compliance'
OUT = R / 'docs/evidence/rl_parameter17_batch13_20261026'
OUT.mkdir(parents=True, exist_ok=True)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

sources = []
def copy(path, target):
    data = path.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    assert sha(path) == digest == sha(target)
    sources.append(dict(source=str(path), destination=str(target.relative_to(R)), sha256=digest, bytes=len(data)))

# Completed reviews and immutable registrations; exclude trajectories and weights.
names = [
    'parameter_batch65536_cycle16_review_20261026_v1',
    'serl_multistep_transfer_cycle12_review_20261026_v1',
    'parameter_batch65536_cycle17_20261026_v1',
    'serl_multistep_batch65536_cycle13_20261026_v1',
    'parameter_batch65536_cycle17_review_20261026_v1',
    'serl_multistep_batch65536_cycle13_review_20261026_v1',
    'parameter_pair15_fixed_20261026_v1',
    'batch13_parameter17_gpu_profile_20261026_v1',
    'cycle16_parameter_and_direct12_behavior_audit_20261026_v1',
    'serl_cycle12_stochastic_representatives_20261026_v1',
]
for name in names:
    root = B / 'runs' / name
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if len(rel.parts) > 3 or any(v in rel.parts for v in ('train', 'direct', '__pycache__')):
            continue
        if (path.suffix in ('.json', '.py', '.png') or (len(rel.parts) == 1 and path.name.endswith('_value_return.npz'))) and path.stat().st_size < 12_000_000:
            # Evaluation trajectories/partial results remain at the run path.
            if 'evaluation' in rel.parts and path.name not in ('EVALUATION.json', 'EXTERNAL_ACTION_RNG_GATE.json', 'POLICY_UNCHANGED.json', 'RESULTS.json'):
                continue
            copy(path, OUT / name / rel)
        elif path.name == 'check_only.log':
            copy(path, OUT / name / rel.with_suffix('.txt'))

required_sources = {
    'resume_cheq_batch65536_reviewed_continuation_20261026.py',
    'resume_serl_multistep_batch65536_stage_20261026.py',
    'evaluate_serl_seeded_multistep_20261026.py',
    'archive_published_cycle_checkpoints_20261025.py',
    'audit_published_episode_20261025.py',
    'summarize_published_episode_audit_20261025.py',
    'replay_published_filter_audit_20261025.py',
    'replay_published_torque_audit_20261025.py',
    'validate_published_finite_check_20261025.py',
}
def find_source_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith('.py') and '/' not in key:
                required_sources.add(key)
            find_source_keys(child)
    elif isinstance(value, list):
        for child in value:
            find_source_keys(child)
for ref in ('parameter_batch65536_cycle17_20261026_v1/impedance/REGISTRATION.json', 'serl_multistep_batch65536_cycle13_20261026_v1/REGISTRATION.json', 'serl_cycle12_stochastic_representatives_20261026_v1/REGISTRATION.json'):
    find_source_keys(read(B / 'runs' / ref))
for name in ('parameter_batch65536_cycle17_20261026_v1', 'serl_multistep_batch65536_cycle13_20261026_v1', 'serl_cycle12_stochastic_representatives_20261026_v1'):
    for path in sorted((B / 'runtime' / name).glob('*.py')):
        if path.name in required_sources:
            copy(path, OUT / 'runtime_sources' / name / path.name)
for name in ('prepare_parameter17_20261026.py', 'prepare_serl_batch13_20261026.py', 'setup_cycle17_batch13_monitors_20261026.py', 'prepare_serl12_stochastic_20261026.py', Path(__file__).name):
    copy(B / 'runtime' / name, OUT / 'preparation_sources' / name)

losses = {}
for run, methods in [('parameter_batch65536_cycle16_20261026_v1', ['impedance', 'admittance', 'vmc']), ('serl_multistep_transfer_cycle12_20261026_v1', ['direct'])]:
    for method in methods:
        path = B / 'runs' / run / method
        if method != 'direct':
            path /= 'train'
        path /= 'optimizer.jsonl'
        with path.open() as stream:
            rows = [json.loads(line) for line in collections.deque(stream, maxlen=1000)]
        losses[method] = dict(source=str(path), sha256=sha(path), count=len(rows), first_step=rows[0]['step'], last_step=rows[-1]['step'], means={k: statistics.mean(row[k] for row in rows) for k in rows[0] if 'loss' in k and isinstance(rows[0][k], (int, float))})
write(OUT / 'LAST1000_LOSSES.json', dict(new_physics=0, optimizer_updates=0, methods=losses))

frozen = {}
for method in ('impedance', 'admittance', 'vmc'):
    path = B / 'runs/parameter_pair15_fixed_20261026_v1' / method / 'REVIEW.json'
    report = read(path)
    assert report['passed'] and report['full_learner_state_unchanged']
    frozen[method] = dict(source=str(path), sha256=sha(path), rows=[row['physical']['row'] for row in report['episodes']], task=report['task'], strict=report['strict'])
write(OUT / 'FROZEN15_SUMMARY.json', dict(methods=frozen, scope='Three originally preselected representatives each, not full30 or final ranking; no-contact compliance remains null.', new_physics=0, optimizer_updates=0))

profile = read(B / 'runs/batch13_parameter17_gpu_profile_20261026_v1/PROFILE.json')
assert len(profile['samples']) == 180
write(OUT / 'GPU_PROFILE_SUMMARY.json', {k: v for k, v in profile.items() if k != 'samples'})
status = dict(time=time.time(), processes={}, progress={}, gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=index,utilization.gpu,memory.used', '--format=csv'], text=True))
for pid in (1280294, 1280295, 1280296, 1280297, 1328339, 1328342, 1328360, 1328362, 1521445, 1535401):
    proc = Path('/proc') / str(pid)
    status['processes'][str(pid)] = dict(alive=proc.exists(), command=(proc/'cmdline').read_bytes().replace(b'\0', b' ').decode() if proc.exists() else None)
for method in ('impedance', 'admittance', 'vmc'):
    status['progress'][method] = read(B/'runs/parameter_batch65536_cycle17_20261026_v1'/method/'train/PROGRESS.json')
status['progress']['direct'] = read(B/'runs/serl_multistep_batch65536_cycle13_20261026_v1/direct/PROGRESS.json')
status['stochastic_evaluation'] = {path.parent.name: read(path) for path in (B/'runs/serl_cycle12_stochastic_representatives_20261026_v1/evaluation').rglob('rollout.progress.json')}
write(OUT / 'LIVE_STATUS.json', status)
write(OUT / 'SOURCES.json', dict(time=time.time(), copied_files=len(sources), files=sources, large_artifacts='SSD only; HDD quota prevents full backup; arm1 copy not verified'))
print(json.dumps(dict(copied_files=len(sources), bytes=sum(v['bytes'] for v in sources), output=str(OUT))))
