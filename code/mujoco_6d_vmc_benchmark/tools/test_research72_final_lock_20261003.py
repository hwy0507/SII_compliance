"""Synthetic-only regressions; never points at the research heldout directory."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from research72_final_lock_20261003 import authorize_final_read, runtime_hashes, sha


class FinalLockTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='sii-final-lock-test-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/'source'
        for folder in ('tools','scripts','assets'):(self.source/folder).mkdir(parents=True)
        (self.source/'tools/worker.py').write_text('synthetic worker\n')
        (self.source/'assets/fixture.xml').write_text('<synthetic/>\n')
        (self.root/'sealed').mkdir()
        # Not even JSON: authorization checks hashes without parsing conditions.
        (self.root/'sealed/HELDOUT.json').write_text('SYNTHETIC ONLY - NOT A CONDITION')
        self.save('PROTOCOL.json',dict(sealed_condition_sha256=sha(self.root/'sealed/HELDOUT.json')))
        self.output=self.root/'evaluation'
        self.lock=dict(schema='sii-research72-final-lock-v1',training_closed=True,
            amendment_sha256={},
            all_registered_finalists_included=True,protocol_sha256=sha(self.root/'PROTOCOL.json'),
            sealed_condition_sha256=sha(self.root/'sealed/HELDOUT.json'),
            frozen_utc=datetime.now(timezone.utc).isoformat(),
            candidates=[dict(name='synthetic_teacher',category='enhanced_teacher')],
            runtime_source_sha256=runtime_hashes(self.source))
        self.save('LOCK.json',self.lock)
        self.lock_sha=sha(self.root/'LOCK.json')
        self.receipt=dict(model_lock_sha256=self.lock_sha,
            sealed_condition_sha256=self.lock['sealed_condition_sha256'],
            protocol_sha256=self.lock['protocol_sha256'],output=str(self.output))
        self.save('FINAL_UNSEAL_RECEIPT.json',self.receipt)

    def save(self,name,value):
        (self.root/name).write_text(json.dumps(value))

    def check(self):
        return authorize_final_read(self.root,self.root/'LOCK.json',self.lock_sha,self.source,self.output)

    def test_unchanged_artifacts_authorize_without_parsing_conditions(self):
        self.assertEqual(self.check()[0],self.lock)

    def test_direct_queue_without_opening_receipt_is_rejected(self):
        (self.root/'FINAL_UNSEAL_RECEIPT.json').unlink()
        with self.assertRaises(FileNotFoundError):self.check()

    def test_added_source_file_is_rejected(self):
        (self.source/'tools/extra.py').write_text('changed import resolution')
        with self.assertRaises(AssertionError):self.check()

    def test_added_or_changed_amendment_is_rejected(self):
        amendment=dict(protocol_sha256=sha(self.root/'PROTOCOL.json'),cap=48)
        self.save('AMENDMENT_01.json',amendment)
        with self.assertRaises(AssertionError):self.check()
        self.lock['amendment_sha256']={'AMENDMENT_01.json':sha(self.root/'AMENDMENT_01.json')}
        self.save('LOCK.json',self.lock);self.lock_sha=sha(self.root/'LOCK.json')
        self.receipt['model_lock_sha256']=self.lock_sha;self.save('FINAL_UNSEAL_RECEIPT.json',self.receipt)
        self.check()
        amendment['cap']=60;self.save('AMENDMENT_01.json',amendment)
        with self.assertRaises(AssertionError):self.check()

    def test_changed_asset_is_rejected(self):
        (self.source/'assets/fixture.xml').write_text('<changed/>')
        with self.assertRaises(AssertionError):self.check()

    def test_changed_checkpoint_is_rejected(self):
        checkpoint=self.root/'model.npz';checkpoint.write_bytes(b'original')
        lock=copy.deepcopy(self.lock)
        lock['candidates']=[dict(name='synthetic_esn',category='esn',checkpoint=str(checkpoint),
                                 checkpoint_sha256=sha(checkpoint))]
        self.save('LOCK.json',lock);self.lock_sha=sha(self.root/'LOCK.json')
        self.receipt['model_lock_sha256']=self.lock_sha;self.save('FINAL_UNSEAL_RECEIPT.json',self.receipt)
        checkpoint.write_bytes(b'changed')
        with self.assertRaises(AssertionError):self.check()

    def test_changed_lock_receipt_output_and_condition_rejected(self):
        for field in ('model_lock_sha256','sealed_condition_sha256','protocol_sha256','output'):
            with self.subTest(field=field):
                receipt=dict(self.receipt);receipt[field]='different'
                self.save('FINAL_UNSEAL_RECEIPT.json',receipt)
                with self.assertRaises(AssertionError):self.check()
        self.save('FINAL_UNSEAL_RECEIPT.json',self.receipt)
        (self.root/'sealed/HELDOUT.json').write_text('changed synthetic fixture')
        with self.assertRaises(AssertionError):self.check()


if __name__=='__main__':unittest.main()
