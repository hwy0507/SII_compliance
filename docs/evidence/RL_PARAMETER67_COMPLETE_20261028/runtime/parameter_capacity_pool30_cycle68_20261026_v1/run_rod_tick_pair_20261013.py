"""Exactly two full episodes: logged old behavior and same-tick correction."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/original_esn_rod_tick_20261013'

def main():
    for arm,flag in [('lagged','0'),('same_tick','1')]:
        run=OUT/arm
        command=[sys.executable,'tools/run_rod_tick_repair_20261013.py',
            '--reference','outputs/esn_office_delayed_conservative_full_20260928/rollout.json',
            '--config',str(run/'config.json'),
            '--checkpoint','outputs/paired_baseline_development_20261012_v2/checkpoints/esn.npz',
            '--output',str(run/'episode'),'--contact-audit']
        subprocess.run(command,cwd=ROOT,env=dict(os.environ,SII_CURRENT_FEEDBACK_TICK=flag),check=True)
        result=json.loads((run/'episode/execution.json').read_text())
        assert result['status']=='complete'
        print(arm,result['audit'],flush=True)

if __name__=='__main__':main()
