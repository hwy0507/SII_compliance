"""Serial campaign driver: measured diagnostics, then frozen budget search.

The two phases never overlap, and each phase is limited to four workers.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--measurement-root',type=Path,required=True)
    p.add_argument('--budget-root',type=Path,required=True)
    p.add_argument('--base-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--menagerie',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Fresh campaign output required')
    args.output.mkdir(parents=True)
    measurement=args.output/'measured28'
    budget=args.output/'fixed_budget'
    methods=['esn_no_x_yield','esn_lowpass_025','mlp_lowpass_025','vmc_lowpass_025',
             'vmc','impedance','admittance','mlp','esn','impedance_k300_reference',
             'impedance_k900_reference','admittance_r2_reference']
    commands=[['measured',sys.executable,str(args.measurement_root/'scripts/run_measured_panel_matrix_20260923.py'),
               '--base-root',str(args.base_root),'--output',str(measurement),'--workers','4','--methods',*methods],
              ['fixed_budget',sys.executable,str(args.budget_root/'scripts/run_classical_fixed_budget_20260923.py'),
               '--base-protocol',str(args.base_root/'panel_matched48/protocol.json'),
               '--menagerie',str(args.menagerie),'--output',str(budget),'--workers','4']]
    (args.output/'queue.json').write_text(json.dumps(dict(max_workers=4,sequential_phases=commands),indent=2))
    for phase,*command in commands:
        (args.output/'status.json').write_text(json.dumps(dict(phase=phase,status='running',started_unix=time.time())))
        with (args.output/(phase+'.log')).open('w') as log:
            completed=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        if completed.returncode:
            (args.output/'status.json').write_text(json.dumps(dict(phase=phase,status='failed',returncode=completed.returncode)))
            raise RuntimeError(f'{phase} exited {completed.returncode}')
        if phase=='measured':
            result=json.loads((measurement/'FINAL_RESULT.json').read_text())
            if len(result['rows'])!=28 or any(r['returncode']!=0 for r in result['rows']):
                raise RuntimeError('Measured phase incomplete; budget search not started')
            for row in result['rows']:
                if row.get('audit_error') or len(row.get('metrics',[]))!=1:
                    raise RuntimeError('Measured audit missing; budget search not started')
                audit=row['metrics'][0]
                if audit['samples']<int(23.99/audit['timestep_s']):
                    raise RuntimeError('Measured physical trace incomplete; budget search not started')
        elif not (budget/'COMPLETE.json').exists():
            raise RuntimeError('Fixed-budget completion marker missing')
    (args.output/'status.json').write_text(json.dumps(dict(status='complete',completed_unix=time.time())))
    (args.output/'COMPLETE.json').write_text(json.dumps(dict(measured_episodes=28,budget_development=48,budget_validation=30)))


if __name__=='__main__':main()
