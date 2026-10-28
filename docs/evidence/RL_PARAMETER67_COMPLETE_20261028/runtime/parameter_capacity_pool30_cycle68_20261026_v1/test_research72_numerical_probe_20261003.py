"""Only model serialization and public-role guards; zero simulation steps."""
import json
from pathlib import Path
import tempfile
import unittest
import mujoco
from research72_numerical_probe_20261003 import derive_timestep, known_condition, sha, DTS


class NumericalProbeTests(unittest.TestCase):
    def test_only_timestep_changes_and_source_bytes_remain_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'model.mjb'
            model = mujoco.MjModel.from_xml_string('<mujoco><option timestep="0.0001"/><worldbody><geom type="sphere" size="0.1"/></worldbody></mujoco>')
            mujoco.mj_saveModel(model, str(path), None)
            before = sha(path)
            hashes = []
            for dt in DTS:
                value, proof = derive_timestep(path, dt)
                self.assertTrue(proof['restored_bytes_exact'])
                self.assertEqual(sha(path), before)
                self.assertEqual(proof['changed_model_fields'], ['opt.timestep'])
                hashes.append(value)
            self.assertEqual(hashes[0], before)
            self.assertEqual(len(set(hashes)), 3)
            with self.assertRaises(AssertionError):
                derive_timestep(path, .002)

    def test_only_original_teacher_and_known_training_identity_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'teacher.json').write_text('{}')
            (root/'CONDITIONS.json').write_text(json.dumps({'conditions': [dict(id='train_000', role='train')]}))
            (root/'PROTOCOL.json').write_text(json.dumps(dict(condition_file_sha256=sha(root/'CONDITIONS.json'),
                teacher_config_sha256=sha(root/'teacher.json'))))
            _, condition = known_condition(root)
            self.assertEqual(condition['role'], 'train')
            (root/'teacher.json').write_text('{"changed":true}')
            with self.assertRaises(AssertionError):
                known_condition(root)

    def test_real_unseal_receipt_blocks_probe_before_reading_any_other_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'FINAL_UNSEAL_RECEIPT.json').write_text('{}')
            with self.assertRaises(AssertionError):
                known_condition(root)


if __name__ == '__main__':
    unittest.main()
