"""Stale recovery preserves evidence and never scores infrastructure failures."""
import json
from pathlib import Path
import socket
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import teacher_bank_campaign_20260930 as campaign


def fake_process(proc, pid, command, *, ticks=1234, state='S'):
    folder = proc / str(pid)
    folder.mkdir(parents=True)
    boot = proc / 'sys/kernel/random/boot_id'
    boot.parent.mkdir(parents=True, exist_ok=True)
    boot.write_text('test-boot')
    fields = [state] + ['0'] * 49
    fields[19] = str(ticks)
    (folder / 'stat').write_text(f'{pid} (worker (complex name)) ' + ' '.join(fields))
    (folder / 'cmdline').write_bytes(b'\0'.join(v.encode() for v in command) + b'\0')
    return folder


def test_live_exact_request_blocks_even_without_saved_pid(tmp_path):
    command = ['/python', '/rollout.py', '--request', '/specific/request.json']
    fake_process(tmp_path, 123, command)
    with pytest.raises(RuntimeError, match='alive'):
        campaign.stale_execution_evidence(dict(host=socket.gethostname()), command, tmp_path)


def test_live_saved_identity_with_changed_argv_is_not_restarted(tmp_path):
    fake_process(tmp_path, 123, ['/renamed-worker'])
    identity = campaign.process_identity(123, tmp_path)
    old = dict(host=socket.gethostname(), pid=123, process_identity=identity)
    with pytest.raises(RuntimeError, match='changed argv'):
        campaign.stale_execution_evidence(old, ['/original-worker'], tmp_path)


def test_reused_pid_different_start_time_is_stale_but_never_signaled(tmp_path):
    fake_process(tmp_path, 123, ['/unrelated-job'], ticks=9000)
    old = dict(host=socket.gethostname(), pid=123,
               process_identity=dict(pid=123, start_ticks=1234, boot_id='test-boot'))
    evidence = campaign.stale_execution_evidence(old, ['/original-worker'], tmp_path)
    assert evidence['observed_identity']['start_ticks'] == 9000
    assert (tmp_path / '123/stat').exists()


def test_unknown_host_and_inaccessible_process_fail_closed(tmp_path):
    with pytest.raises(RuntimeError, match='another host'):
        campaign.stale_execution_evidence(dict(host='other-compute-host'), ['/worker'], tmp_path)
    (tmp_path / '123').mkdir()
    with pytest.raises(RuntimeError, match='Incomplete process identity'):
        campaign.stale_execution_evidence(dict(pid=123), ['/worker'], tmp_path)


def saved_attempt(root, status='running', returncode=None):
    relative = 'search/passive_corner/vmc/c00/0'
    folder = root / relative
    folder.mkdir(parents=True)
    execution = dict(status=status, host=socket.gethostname(), pid=99999,
                     returncode=returncode,
                     command=[sys.executable, str(root/'source/tools/teacher_bank_rollout_20260930.py'),
                              '--root', str(root), '--request', str(folder/'request.json')])
    (folder / 'execution.json').write_text(json.dumps(execution))
    (folder / 'request.json').write_text('{"original":true}')
    (folder / 'partial_raw.npz').write_bytes(b'preserve interrupted raw evidence')
    return relative, folder


def test_stale_recovery_uses_distinct_folder_and_is_idempotent(tmp_path, monkeypatch):
    relative, folder = saved_attempt(tmp_path)
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    monkeypatch.setattr(campaign, 'stale_execution_evidence', lambda *args: dict(reason='absent'))
    recovered = campaign.resolve_attempt_recovery(tmp_path, relative)
    assert recovered == f'recovery_attempts/{relative}/retry0001'
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == before
    assert campaign.resolve_attempt_recovery(tmp_path, relative) == recovered
    mapping = json.loads((tmp_path / 'recovery_records' / (relative + '.json')).read_text())
    assert mapping['history'][0]['source_relative'] == relative
    assert mapping['history'][0]['preserved_without_modification']


def test_infrastructure_failure_is_not_returned_as_optimization_sample(tmp_path, monkeypatch):
    relative, folder = saved_attempt(tmp_path, status='failed', returncode=1)
    # A partially completed audit does not override an infrastructure failure.
    (folder / 'audit.json').write_text('{"eligible":true,"score":0}')
    monkeypatch.setattr(campaign, 'stale_execution_evidence', lambda *args: dict(reason='absent'))
    with pytest.raises(RuntimeError, match='not an optimization sample'):
        campaign.attempt(tmp_path, relative, {'category':'passive_corner'}, [.5]*7, 'search', False)


def test_same_plan_pilot_reuse_checks_controller_and_preserves_raw(tmp_path, monkeypatch):
    (tmp_path/'plan.json').write_text('{"schema":1}')
    relative='pilot/passive_corner/vmc';folder=tmp_path/relative
    folder.mkdir(parents=True)
    fixture={'category':'passive_corner','id':'passive_corner_train_0000'};point=[.5]*7
    request=dict(fixture=fixture,method='vmc',teacher=campaign.controller_config(point,'vmc'),
                 plan_sha256=campaign.sha(tmp_path/'plan.json'),phase='pilot')
    (folder/'request.json').write_text(json.dumps(request))
    command=[sys.executable,str(tmp_path/'source/tools/teacher_bank_rollout_20260930.py'),
             '--root',str(tmp_path),'--request',str(folder/'request.json')]
    (folder/'execution.json').write_text(json.dumps(dict(status='completed',returncode=0,command=command)))
    (folder/'audit.json').write_text(json.dumps(dict(eligible=False,score=2.,constraint=1.)))
    before={p.name:p.read_bytes() for p in folder.iterdir()}
    monkeypatch.setattr(campaign,'stale_execution_evidence',lambda *args:dict(reason='absent'))
    result=campaign.attempt(tmp_path,'search/passive_corner/vmc/c00/0',fixture,point,'search',False)
    assert result['folder']==relative
    assert {p.name:p.read_bytes() for p in folder.iterdir()}==before
    assert not (tmp_path/'search').exists()
    with pytest.raises(RuntimeError,match='does not match'):
        campaign.attempt(tmp_path,relative,fixture,[.6]*7,'pilot',False)
    assert not (tmp_path / 'recovery_records').exists()


def test_completed_success_reuses_audit_only_after_child_exit(tmp_path, monkeypatch):
    relative, folder = saved_attempt(tmp_path, status='completed', returncode=0)
    (folder / 'audit.json').write_text('{"eligible":false}')
    def live(*args):
        raise RuntimeError('Prior rollout is alive; do not restart')
    monkeypatch.setattr(campaign, 'stale_execution_evidence', live)
    with pytest.raises(RuntimeError, match='alive'):
        campaign.resolve_attempt_recovery(tmp_path, relative)
    monkeypatch.setattr(campaign, 'stale_execution_evidence', lambda *args: dict(reason='absent'))
    assert campaign.resolve_attempt_recovery(tmp_path, relative) == relative
