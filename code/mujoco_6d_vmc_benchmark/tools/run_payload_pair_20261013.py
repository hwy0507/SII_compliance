"""Two predeclared sequential local episodes; keep both outcomes."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/original_esn_payload_bridge_20261013'

def main():
    for label,enabled in [('path_only','0'),('path_bridge','1')]:
        run=OUT/label
        command=[sys.executable,'tools/run_payload_bridge_20261013.py',
            '--reference','outputs/esn_office_delayed_conservative_full_20260928/rollout.json',
            '--config',str(run/'config.json'),'--checkpoint','outputs/paired_baseline_development_20261012_v2/checkpoints/esn.npz',
            '--output',str(run/'episode'),'--contact-audit']
        subprocess.run(command,cwd=ROOT,env=dict(os.environ,SII_SERVO_INTERPOLATION=enabled),check=True)
        receipt=json.loads((run/'episode/execution.json').read_text())
        assert receipt['status']=='complete'
        print(label,receipt['audit'],flush=True)

if __name__=='__main__':main()
