"""Prospective storage must fail closed and restore failed episodes exactly."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import goal_prospective_storage_20261017 as storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()/'outputs/rl_goal_stream_fixture'
        self.root.mkdir(parents=True);self.run=self.root/'control'
        self.put(self.root/'REGISTRATION.json',dict(schema='sii-rl-persistent-goal-stage-v1',
            run_root=str(self.root),working_set_policy=storage.SCHEMA,server_compute=False,
            jobs=[dict(name='control',output=str(self.run))]))
        storage.seal(self.root)
        self.rows=[];self.checkpoints=[];self.archives={}
        self.publisher=patch.object(storage,'publish',side_effect=self.publish).start()
        self.verifier=patch.object(storage,'remote_verify',side_effect=self.verify).start()
        self.addCleanup(patch.stopall)

    def put(self,path,data): path.write_text(json.dumps(data))

    def episode(self,index=0,closed=True):
        episode=self.run/f'episode_{index:05d}_failure'
        (episode/'rollout_metrics').mkdir(parents=True)
        self.put(episode/'AUDIT.json',dict(training=True,task_success=False,strict_success=False))
        self.put(episode/'execution.json',dict(ended_utc='closed'))
        for name in (*storage.FILES,'rollout.npz'):
            (episode/name).write_bytes((name+str(index)).encode()*100)
        step=(index+1)*1375;cp=self.run/f'checkpoint_{step:07d}';cp.mkdir()
        self.put(cp/'office_runner.json',dict(step=step,episode_boundary=True,pending_transition=None))
        (cp/'weights.bin').write_bytes(b'weights'+bytes([index]))
        (cp/'replay.bin').write_bytes(b'replay'+bytes([index]))
        checkpoint=dict(path=str(cp),step=step,hashes={p.name:storage.sha(p) for p in cp.iterdir()})
        self.checkpoints.append(checkpoint)
        row=dict(run=str(episode),episode=index,step_after=step,
            audit_sha256=storage.sha(episode/'AUDIT.json'),trace_sha256=storage.sha(episode/'rollout.npz'))
        if closed: row['ended_utc']='closed'
        self.rows.append(row)
        self.put(self.run/'execution.json',dict(status='running',rows=self.rows,checkpoint_rows=self.checkpoints))
        return episode,cp

    def publish(self,archive,receipt):
        target=Path(self.tmp.name)/('archive-'+str(len(self.archives))+'.tar.gz')
        shutil.copy2(archive,target);self.archives[receipt['remote']]=target
        self.verify(receipt['remote'],receipt['archive_bytes'],receipt['archive_sha256'])

    def verify(self,remote,size,digest):
        path=self.archives[remote]
        if path.stat().st_size!=size or storage.sha(path)!=digest: raise ValueError('remote mismatch')

    def assert_preserved(self,episode):
        for name in storage.FILES: self.assertTrue((episode/name).is_file())

    def test_reject_historical_or_preexisting_outputs(self):
        other=self.root.parent/'rl_goal_historical';other.mkdir()
        with self.assertRaises(ValueError): storage.seal(other)
        self.run.mkdir()
        with self.assertRaisesRegex(ValueError,'retrofit'): storage.seal(self.root)

    def test_inflight_and_symlink_rejected_without_publish(self):
        episode,_=self.episode(closed=False)
        with self.assertRaisesRegex(ValueError,'flight'): storage.archive_episode(self.root,episode)
        self.publisher.assert_not_called()
        self.rows[0]['ended_utc']='closed'
        self.put(self.run/'execution.json',dict(rows=self.rows,checkpoint_rows=self.checkpoints))
        p=episode/storage.FILES[0];p.unlink();p.symlink_to(episode/'rollout.npz')
        with self.assertRaises(ValueError): storage.archive_episode(self.root,episode)
        self.publisher.assert_not_called()

    def test_network_failure_preserves_every_file(self):
        episode,cp=self.episode()
        self.publisher.side_effect=TimeoutError('offline')
        with self.assertRaises(TimeoutError): storage.archive_episode(self.root,episode)
        self.assert_preserved(episode);self.assertTrue((cp/'weights.bin').exists())

    def test_source_mutation_after_plan_prevents_release(self):
        episode,_=self.episode()
        def mutate(archive,receipt):
            self.publish(archive,receipt)
            (episode/storage.FILES[0]).write_bytes(b'changed')
        self.publisher.side_effect=mutate
        with self.assertRaisesRegex(ValueError,'changed'): storage.archive_episode(self.root,episode)
        self.assert_preserved(episode)

    def test_three_failures_roundtrip_keeps_newest_two_checkpoints(self):
        first=None
        for index in range(3):
            episode,cp=self.episode(index)
            originals={str(p.relative_to(self.root)):p.read_bytes() for directory in (episode,cp)
                       for p in directory.rglob('*') if p.is_file()}
            receipt=storage.archive_episode(self.root,episode)
            if first is None: first=(episode,cp,receipt,originals)
            for name in storage.FILES: self.assertFalse((episode/name).exists())
            self.assertTrue((episode/'AUDIT.json').exists())
        self.assertFalse((first[1]/'weights.bin').exists())
        for cp in self.checkpoints[-2:]:
            for name,digest in cp['hashes'].items(): self.assertEqual(storage.sha(Path(cp['path'])/name),digest)
        episode,cp,receipt,originals=first
        archive=self.archives[receipt['remote']]
        storage.restore(self.root,episode,archive)
        storage.restore(self.root,episode,archive)
        for name,data in originals.items(): self.assertEqual((self.root/name).read_bytes(),data)
        self.assertEqual({p.name for p in cp.iterdir()},set(self.checkpoints[0]['hashes']))

    def test_restore_rejects_tamper_and_existing_difference(self):
        episode,_=self.episode();receipt=storage.archive_episode(self.root,episode)
        archive=self.archives[receipt['remote']]
        (episode/'rollout.npz').write_bytes(b'different')
        with self.assertRaisesRegex(ValueError,'overwrite'): storage.restore(self.root,episode,archive)
        archive.write_bytes(b'broken')
        with self.assertRaisesRegex(ValueError,'hash'): storage.restore(self.root,episode,archive)

    def test_interrupted_release_resumes_from_verified_archive(self):
        episode,_=self.episode()
        unlink=Path.unlink
        def interrupt(path,*args,**kwargs):
            if path==episode/storage.FILES[1]: raise OSError('interrupted')
            return unlink(path,*args,**kwargs)
        with patch.object(Path,'unlink',interrupt):
            with self.assertRaises(OSError): storage.archive_episode(self.root,episode)
        self.assertFalse((episode/storage.FILES[0]).exists())
        self.assertTrue((episode/storage.FILES[1]).exists())
        receipt=storage.archive_episode(self.root,episode)
        storage.restore(self.root,episode,self.archives[receipt['remote']])
        self.assert_preserved(episode)

    def test_corrupted_pending_transfer_never_releases_files(self):
        episode,_=self.episode()
        self.publisher.side_effect=TimeoutError('offline')
        with self.assertRaises(TimeoutError): storage.archive_episode(self.root,episode)
        (self.run/'storage_receipts'/episode.name/'transfer.tar.gz').write_bytes(b'corrupted')
        with self.assertRaisesRegex(ValueError,'cache changed'): storage.archive_episode(self.root,episode)
        self.assert_preserved(episode)


if __name__=='__main__': unittest.main()
