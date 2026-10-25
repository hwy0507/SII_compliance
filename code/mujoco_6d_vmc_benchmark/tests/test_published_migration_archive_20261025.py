"""Exercise archive coverage while migration's learner list grows."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import torch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import archive_published_cycle_checkpoints_20261025 as archive


class MigrationArchiveTests(unittest.TestCase):
    def test_waits_for_new_learner_archives_and_hands_off(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); run=root/'run'; run.mkdir()
            output=root/'archive'
            calls=[]
            def advance(_):
                calls.append(1)
                if len(calls)==1:
                    (run/'LAUNCH.json').write_text(json.dumps({'jobs':[{'controller':'direct','pid':123}]}))
                    folder=run/'direct'; folder.mkdir()
                    cycle={'cycle':1,'steps':20,'reward_mean':0.}
                    (folder/'CYCLES.json').write_text(json.dumps({'cycles':[cycle]}))
                    torch.save(dict(boundary='complete_condition_cycle',cycle=1,steps=20,
                        controller='direct',protocol_sha256='unit-test'),folder/'checkpoint_latest.pt')
                else:
                    (run/'MIGRATION_FINISHED.json').write_text('{}')
            with patch.object(archive,'process_identity',return_value='test-start-ticks'), \
                    patch.object(archive.time,'sleep',side_effect=advance):
                archive.main(argparse.Namespace(run=run,output=output,migration_only=True))
            finished=json.loads((output/'FINISHED.json').read_text())
            self.assertEqual(finished['archived'],['direct:1'])
            self.assertEqual(finished['missed'],[])
            self.assertTrue((output/'direct/cycle_00001.pt').exists())
            self.assertEqual(len(calls),2)


if __name__=='__main__':
    unittest.main()
