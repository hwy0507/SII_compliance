"""Synthetic plotting checks; never accesses actual condition manifests."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest

from plot_research72_comparison_20261003 import ORDER, validate, render
from research72_comparison_report_20261003 import assemble
from test_research72_comparison_report_20261003 import metrics


def synthetic_report():
    deterministic={'enhanced_teacher','classical_admittance','classical_impedance','classical_vmc','nominal_zero'}
    candidates=[];rows=[];conditions=[f'synthetic_{i}' for i in range(6)]
    for fi,family in enumerate(ORDER):
        for seed in ([None] if family in deterministic else [1,2,3]):
            name=f'{family}_{seed}';candidate=dict(name=name,category=family)
            if seed is not None:candidate['seed']=seed
            candidates.append(candidate)
            for ci,condition in enumerate(conditions):
                # Deliberate missingness, short failures, absent exposures and
                # an all-failed baseline must remain visible in the figures.
                if family=='ordinary_mlp' and ci==5:continue
                success=family!='nominal_zero' and (ci+fi+(seed or 0))%5!=0
                full=not (family=='ordinary_rnn' and ci==0)
                record=metrics(success=success and full,full=full,
                    exposed=family!='classical_vmc',force=10.+(-1)**fi*fi*.4+ci*.1+(seed or 0)*.2)
                record['task_success']=full and (success or ci==2)
                rows.append(dict(candidate=name,category=family,condition_id=condition,metrics=record))
    report=assemble(candidates,conditions,rows);report['synthetic_demo']=True
    return report


class PlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=synthetic_report()

    def test_synthetic_cannot_pass_as_real(self):
        with self.assertRaises(AssertionError):validate(self.report,False)

    def test_every_family_and_missing_denominator_retained(self):
        self.assertEqual(validate(self.report,True),list(ORDER))
        self.assertEqual(self.report['families']['ordinary_mlp']['strict']['missing'],3)
        self.assertIsNone(self.report['families']['ordinary_mlp']['strict']['rate'])
        self.assertEqual(self.report['esn_minus_baseline']['nominal_zero']['jointly_strict_full_exposed_contacts']['rod']['impulse_ns']['paired_cells'],0)
        differences=[r['jointly_strict_full_exposed_contacts']['rod']['impulse_ns']['difference']
                     for r in self.report['esn_minus_baseline'].values()]
        self.assertTrue(any(x < 0 for x in differences if x is not None))
        self.assertTrue(any(x > 0 for x in differences if x is not None))

    def test_exports_and_empty_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'figures';before=json.dumps(self.report,sort_keys=True)
            result=render(self.report,out,True)
            self.assertEqual(json.dumps(self.report,sort_keys=True),before)
            self.assertEqual(set(result['files_sha256']),{'outcomes.svg','outcomes.png','contact_pairs.svg','contact_pairs.png',
                                                        'contact_pairs_ball_pillar.svg','contact_pairs_ball_pillar.png'})
            self.assertEqual((out/'outcomes.png').read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
            svg=(out/'contact_pairs.svg').read_text()
            self.assertIn('SYNTHETIC LAYOUT ONLY',svg);self.assertIn('NA (n=0)',svg)
            self.assertIn('Nominal WBC',svg)
            extra=(out/'contact_pairs_ball_pillar.svg').read_text()
            self.assertIn('Ball impact',extra);self.assertIn('Pillar',extra)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--write-demo',type=Path)
    args,rest=parser.parse_known_args()
    if args.write_demo:
        report=synthetic_report()
        with args.write_demo.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    else:unittest.main(argv=[__file__,*rest])
