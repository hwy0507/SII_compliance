"""Destructive retention must reject unsafe inputs and restore original bytes."""
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import offline_goal_episode_20261016 as offline


class OfflineEpisodeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bench = Path(self.tmp.name).resolve()
        self.root = self.bench / 'outputs/rl_goal_fixture'
        self.run = self.root / 'control'
        self.episode = self.run / 'episode_00000_failure'
        (self.episode / 'rollout_metrics').mkdir(parents=True)
        self.put(self.episode / 'AUDIT.json', {'training': True, 'task_success': False})
        self.put(self.episode / 'execution.json', {'ended_utc': 'closed'})
        self.put(self.root / 'REGISTRATION.json', {
            'schema': 'sii-rl-persistent-goal-stage-v1', 'run_root': str(self.root),
            'jobs': [{'output': str(self.run)}]})
        self.put(self.run / 'execution.json', {'status': 'complete', 'rows': [{
            'run': str(self.episode), 'ended_utc': 'closed', 'step_after': 1375,
            'audit_sha256': offline.sha(self.episode / 'AUDIT.json')}]})
        self.originals = {}
        for index, name in enumerate(offline.FILES):
            data = bytes(range(256)) * (index + 1)
            (self.episode / name).write_bytes(data)
            self.originals[name] = data
        self.checkpoint = self.run / 'checkpoint_0001375'
        self.checkpoint.mkdir()
        (self.checkpoint / 'actor.bin').write_bytes(b'keep checkpoint')
        (self.episode / 'trace.npz').write_bytes(b'keep diagnostic trace')
        self.archive = self.bench / 'archive.tar.gz'
        self.make_archive()
        self.remote = offline.REMOTE_BASE + 'fixture/evidence.tar.gz'
        self.remote_patch = patch.object(offline, 'remote_verify')
        self.remote_mock = self.remote_patch.start()
        self.addCleanup(self.remote_patch.stop)

    @staticmethod
    def put(path, data):
        path.write_text(json.dumps(data))

    def make_archive(self, duplicate=False, linked=False, corrupt=False):
        with tarfile.open(self.archive, 'w:gz') as tar:
            for index, name in enumerate(offline.FILES):
                path = self.episode / name
                member = str(path.relative_to(self.bench))
                if index == 0 and linked:
                    item = tarfile.TarInfo(member)
                    item.type = tarfile.SYMTYPE
                    item.linkname = '/etc/passwd'
                    tar.addfile(item)
                elif index == 0 and corrupt:
                    data = b'x' * path.stat().st_size
                    item = tarfile.TarInfo(member)
                    item.size = len(data)
                    tar.addfile(item, io.BytesIO(data))
                else:
                    tar.add(path, arcname=member)
                if index == 0 and duplicate:
                    tar.add(path, arcname=member)

    def plan(self):
        return offline.plan(self.episode, self.archive, self.remote,
                            offline.sha(self.archive), self.bench)

    def assert_originals(self):
        for name, data in self.originals.items():
            self.assertEqual((self.episode / name).read_bytes(), data)

    def test_failed_episode_exact_roundtrip_and_idempotent_restore(self):
        receipt = self.plan()
        offline.evict(receipt, self.archive, self.root / 'journal.jsonl', self.bench)
        self.assertTrue(all(not (self.episode / n).exists() for n in offline.FILES))
        self.assertEqual((self.checkpoint / 'actor.bin').read_bytes(), b'keep checkpoint')
        self.assertEqual((self.episode / 'trace.npz').read_bytes(), b'keep diagnostic trace')
        offline.restore(receipt, self.archive, self.bench)
        self.assert_originals()
        offline.restore(receipt, self.archive, self.bench)
        self.assert_originals()
        events = [json.loads(line)['event'] for line in (self.root / 'journal.jsonl').read_text().splitlines()]
        self.assertEqual(events, ['before_remove', 'removed'] * 4)

    def test_inflight_arm_and_changed_identity_rejected(self):
        receipt = self.plan()
        path = self.run / 'execution.json'
        state = offline.read(path)
        state['status'] = 'running'
        self.put(path, state)
        with self.assertRaises(ValueError):
            self.plan()
        with self.assertRaises(ValueError):
            offline.evict(receipt, self.archive, self.root / 'journal', self.bench)
        self.assert_originals()

    def test_wrong_archive_digest_and_member_content_rejected(self):
        with self.assertRaises(ValueError):
            offline.plan(self.episode, self.archive, self.remote, '0' * 64, self.bench)
        self.make_archive(corrupt=True)
        with self.assertRaises(ValueError):
            self.plan()
        self.assert_originals()

    def test_duplicate_and_link_members_rejected(self):
        for keyword in ('duplicate', 'linked'):
            self.make_archive(**{keyword: True})
            with self.assertRaises(ValueError):
                self.plan()
            self.assert_originals()

    def test_checkpoint_target_tamper_rejected_before_any_removal(self):
        receipt = self.plan()
        receipt['files'][-1]['path'] = str(self.checkpoint / 'actor.bin')
        with self.assertRaises(ValueError):
            offline.evict(receipt, self.archive, self.root / 'journal', self.bench)
        self.assert_originals()
        self.assertTrue((self.checkpoint / 'actor.bin').exists())

    def test_changed_last_original_prevents_all_removal(self):
        receipt = self.plan()
        target = self.episode / offline.FILES[-1]
        target.write_bytes(b'changed original')
        with self.assertRaises(ValueError):
            offline.evict(receipt, self.archive, self.root / 'journal', self.bench)
        self.assertTrue(all((self.episode / n).exists() for n in offline.FILES))
        self.assertFalse((self.root / 'journal').exists())

    def test_symlink_original_rejected(self):
        receipt = self.plan()
        target = self.episode / offline.FILES[-1]
        target.unlink()
        target.symlink_to(self.checkpoint / 'actor.bin')
        with self.assertRaises(ValueError):
            offline.evict(receipt, self.archive, self.root / 'journal', self.bench)
        self.assertTrue((self.episode / offline.FILES[0]).exists())

    def test_remote_failure_prevents_removal(self):
        receipt = self.plan()
        self.remote_mock.side_effect = ValueError('remote mismatch')
        with self.assertRaises(ValueError):
            offline.evict(receipt, self.archive, self.root / 'journal', self.bench)
        self.assert_originals()

    def test_restore_never_overwrites_different_file(self):
        receipt = self.plan()
        offline.evict(receipt, self.archive, self.root / 'journal', self.bench)
        target = self.episode / offline.FILES[0]
        target.write_bytes(b'concurrent file')
        with self.assertRaises(ValueError):
            offline.restore(receipt, self.archive, self.bench)
        self.assertEqual(target.read_bytes(), b'concurrent file')

    def test_remote_path_cannot_escape_or_use_incoming(self):
        self.remote_patch.stop()
        with patch.object(offline.subprocess, 'check_output') as call:
            for path in (offline.REMOTE_BASE + '../bad/evidence.tar.gz',
                         offline.REMOTE_BASE + 'x/y/evidence.tar.gz',
                         '/home/arm1/sii_shared/SII_compliance/incoming/x/evidence.tar.gz'):
                with self.assertRaises(ValueError):
                    offline.remote_verify(path, 1, '0' * 64)
            call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
