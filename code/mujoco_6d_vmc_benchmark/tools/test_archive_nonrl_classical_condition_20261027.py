"""Synthetic small-file tests; these are not physical experiment receipts."""
import json
from pathlib import Path
import tempfile
import unittest

from archive_nonrl_classical_condition_20261027 import package,sha


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'run';self.root.mkdir()
        def write(p,data):
            p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data))
        self.write=write
        models=[dict(name=f'fixed_{i}',worker_kind='classical') for i in range(6)]
        write(self.root/'MODEL_LOCK.json',dict(status='frozen',models=models))
        write(self.root/'REGISTRATION.json',dict(schema='sii-nonrl-task-conditional-classical-v1',
              models_sha256=sha(self.root/'MODEL_LOCK.json')))
        for n in ('CONDITIONS.json','PROTOCOL.json'):write(self.root/n,{})
        source=self.base/'auditor.py';source.write_text('# Synthetic auditor fixture\n');self.source=source
        rows=[];entries=[]
        fields={'audit_sha256':'AUDIT.json','trace_sha256':'rollout.npz','execution_sha256':'execution.json',
                'model_sha256':'rollout.mjb','chain_sha256':'execution_chain.npz',
                'substep_metrics_sha256':'rollout_metrics/substep_metrics.npz','research_substeps_sha256':'research_substeps.npz'}
        for m in models:
            name=m['name']+'__condition0';run=self.root/'evaluation'/name;hashes={}
            for key,file in fields.items():
                write(run/file,dict(status='complete') if file=='execution.json' else {'fixture':name+file})
                hashes[key]=sha(run/file)
            metric=self.root/'metrics'/f'{name}.json';write(metric,{})
            hashes['metric_sha256']=sha(metric)
            rows.append(dict(method=m['name'],condition='condition0',run=str(run),source_hashes=hashes))
            entries.append(dict(name=name,status='complete'))
        write(self.root/'execution.json',dict(status='running',evaluation=entries))
        self.audit=self.base/'audit.json'
        write(self.audit,dict(status='completed_classical_condition_audit_passed_not_final',root=str(self.root),
              condition='condition0',rows=rows,registration_sha256=sha(self.root/'REGISTRATION.json'),
              model_lock_sha256=sha(self.root/'MODEL_LOCK.json'),auditor_sha256=sha(source)))

    def test_verified_package_preserves_sources(self):
        before=sha(self.root/'execution.json')
        receipt=package(self.root,self.audit,self.base/'out',self.source)
        self.assertEqual(receipt['episodes'],6)
        self.assertTrue(receipt['source_before_after_and_archive_payload_verified'])
        self.assertEqual(receipt['sha256'],sha(Path(receipt['archive'])))
        self.assertEqual(before,sha(self.root/'execution.json'))

    def test_unfinished_episode_refused_before_packaging(self):
        p=self.root/'execution.json';s=json.loads(p.read_text());s['evaluation'][2]['status']='running';self.write(p,s)
        with self.assertRaisesRegex(ValueError,'Unfinished'):package(self.root,self.audit,self.base/'out',self.source)
        self.assertFalse((self.base/'out').exists())

    def test_changed_trace_refused(self):
        (self.root/'evaluation/fixed_0__condition0/rollout.npz').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError,'Audited evidence changed'):package(self.root,self.audit,self.base/'out',self.source)

    def test_missing_configuration_refused(self):
        a=json.loads(self.audit.read_text());a['rows'].pop();self.write(self.audit,a)
        with self.assertRaisesRegex(ValueError,'All6'):package(self.root,self.audit,self.base/'out',self.source)


if __name__=='__main__':unittest.main()
