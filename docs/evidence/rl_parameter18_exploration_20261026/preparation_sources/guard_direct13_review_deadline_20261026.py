from pathlib import Path
import hashlib,json,os,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=B/'runs/serl_multistep_batch65536_cycle13_review_deadline_guard_20261026_v1'
REG=json.loads((OUT/'REGISTRATION.json').read_text())
os.sched_setaffinity(0,{54})
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def identity(pid):
    try:
        path=Path('/proc')/str(pid)
        fields=(path/'stat').read_text().rsplit(')',1)[1].split()
        if fields[0]=='Z':return None
        return dict(start=fields[19],command=(path/'cmdline').read_bytes().replace(b'\0',b' ').decode())
    except FileNotFoundError:return None
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n')
assert sha(__file__)==REG['source_sha256']
old=Path(REG['original_review']);cp=Path(REG['checkpoint']);run=Path(REG['training_run'])
deadline=time.monotonic()+7200
while True:
    if (old/'FINISHED.json').exists():
        assert json.loads((old/'REVIEW.json').read_text())['passed']
        write('FINISHED.json',dict(time=time.time(),used_original_review=True,replacement_started=False));break
    active=identity(REG['coordinator_pid'])==REG['coordinator_identity'] or identity(REG['reviewer_pid'])==REG['reviewer_identity']
    if not active and cp.exists():
        log=(old/'driver.log').read_text()
        if 'RuntimeError: Cycle11 archive unavailable: direct' not in log or (run/'FAILURE.json').exists():
            raise RuntimeError('Original review ended for a different reason; inspect evidence, no automatic retry')
        for name,expected in REG['review_sources'].items():assert sha(old/name)==expected
        replacement=Path(REG['replacement_review']);replacement.mkdir()
        for name in REG['review_sources']:(replacement/name).write_bytes((old/name).read_bytes())
        # The original observer is terminal and the exact complete checkpoint
        # exists. Re-run only its read-only audit, never a training process.
        with (replacement/'driver.log').open('x') as stream:
            proc=subprocess.Popen([str(B/'env/bin/python'),str(replacement/'coordinator.py')],stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
            write('REPLACEMENT_LAUNCH.json',dict(time=time.time(),pid=proc.pid,source_hashes=REG['review_sources'],original_log_sha256=sha(old/'driver.log')))
            code=proc.wait()
        if code:raise RuntimeError('Read-only replacement failed; retain evidence')
        assert json.loads((replacement/'REVIEW.json').read_text())['passed']
        write('FINISHED.json',dict(time=time.time(),used_original_review=False,replacement_started=True,replacement_review=str(replacement)));break
    if (run/'FAILURE.json').exists():raise RuntimeError('Formal training failure; no restart')
    if not cp.exists() and identity(REG['learner_pid'])!=REG['learner_identity']:
        # Allow its already-running archiver to publish the final checkpoint.
        if not (run/'FINISHED.json').exists():raise RuntimeError('Learner ended without complete-cycle receipt; inspect original handles')
    if time.monotonic()>deadline:raise RuntimeError('Guard observation expired; inspect original training/archiver, no restart')
    time.sleep(5)
