"""No physics: real child exits exercise failure preservation and terminal evidence."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

SPEC = importlib.util.spec_from_file_location('sac_supervisor', Path(__file__).resolve().parents[1] / 'tools/supervise_sac_two_branch_20260925.py')
supervisor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(supervisor)


@pytest.mark.parametrize('code,phrase', [(124, 'deadline'), (137, 'not uniquely known'), (-9, 'signal 9'), (1, 'nonzero')])
def test_actual_exit_classification(tmp_path, code, phrase):
    result = supervisor.outcome({'output': str(tmp_path)}, code)
    assert result['returncode'] == code
    assert result['status'] == 'failed'
    assert phrase in result['failure_reason']


def test_failed_marker_overrides_success(tmp_path):
    (tmp_path / 'COMPLETE.json').write_text('{"status":"complete"}')
    (tmp_path / 'FAILED.json').write_text('{"error":"failure"}')
    assert supervisor.outcome({'output': str(tmp_path)}, 0)['status'] == 'failed'


@pytest.mark.parametrize('first', ['exit', 'launch_failure'])
def test_first_failure_preserves_peer_and_no_retry(tmp_path, monkeypatch, first):
    (tmp_path / 'source').mkdir()
    outputs = [tmp_path / 'training' / branch for branch in ('online_only', 'demo_prefill')]
    second = [sys.executable, '-c',
              'import pathlib,time; time.sleep(0.1); p=pathlib.Path(' + repr(str(outputs[1])) + '); '
              'p.mkdir(parents=True); (p/"COMPLETE.json").write_text(\'{"status":"complete"}\')']
    commands = [[sys.executable, '-c', 'raise SystemExit(124)'] if first == 'exit' else ['/missing-saci-command'], second]
    jobs = [dict(branch=branch, command=command, output=str(output), log=str(tmp_path / (branch + '.log')), environment={})
            for branch, command, output in zip(('online_only', 'demo_prefill'), commands, outputs)]
    monkeypatch.setattr(supervisor, 'verify', lambda *args: ({'jobs': jobs}, {}))
    monkeypatch.setattr(sys, 'argv', ['supervisor', '--root', str(tmp_path), '--plan-sha256', 'test',
                                    '--supervisor-sha256', 'test', '--launch'])
    with pytest.raises(SystemExit) as error:
        supervisor.main()
    assert error.value.code == 1
    state = json.loads((tmp_path / 'supervisor/status.json').read_text())
    assert state['status'] == 'failed'
    assert state['retries'] == 0
    assert len(state['jobs']) == 2
    assert state['jobs'][0]['status'] == 'failed'
    assert state['jobs'][0]['returncode'] == (124 if first == 'exit' else None)
    assert state['jobs'][1]['status'] == 'complete'
    assert state['jobs'][1]['returncode'] == 0
    assert (outputs[1] / 'COMPLETE.json').exists()
    assert (tmp_path / 'supervisor/FAILED.json').exists()
    assert not (tmp_path / 'supervisor/COMPLETE.json').exists()
