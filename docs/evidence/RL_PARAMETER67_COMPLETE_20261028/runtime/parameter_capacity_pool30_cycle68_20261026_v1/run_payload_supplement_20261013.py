"""Corrected bridge B once, then one predeclared common-friction probe C."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/original_esn_payload_bridge_20261013'

def main():
    for label,script in [('path_bridge_v2','run_payload_bridge_20261013.py'),
                         ('path_bridge_friction_probe','run_payload_friction_probe_20261013.py')]:
        run=OUT/label
        command=[sys.executable,'tools/'+script,
            '--reference','outputs/esn_office_delayed_conservative_full_20260928/rollout.json',
            '--config',str(run/'config.json'),
            '--checkpoint','outputs/paired_baseline_development_20261012_v2/checkpoints/esn.npz',
            '--output',str(run/'episode'),'--contact-audit']
        subprocess.run(command,cwd=ROOT,env=dict(os.environ,SII_SERVO_INTERPOLATION='1'),check=True)
        result=json.loads((run/'episode/execution.json').read_text())
        assert result['status']=='complete'
        print(label,result['audit'],flush=True)

if __name__=='__main__':main()
