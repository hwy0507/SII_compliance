"""Apply the registered controller ranking; never uses sealed conditions."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--screen',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--final-choice',action='store_true')
    a=p.parse_args();spec=read(a.screen/'SPECIFICATION.json');summary=read(a.screen/'SUMMARY.json')
    assert read(a.screen/'execution.json')['status']=='complete'
    assert summary['expected']==summary['completed']==len(spec['conditions'])*len(spec['candidates'])
    assert spec['protocol_sha256']==sha(a.root/'PROTOCOL.json')
    registered={c['id']:c for c in read(a.root/'CONDITIONS.json')['conditions']}
    assert all(registered[c]['role']=='development' for c in spec['conditions'])
    ranked={}
    for candidate in spec['candidates']:
        rows=[r for r in summary['rows'] if r['candidate']==candidate['name']]
        assert len(rows)==len(spec['conditions']) and {r['condition_id'] for r in rows}==set(spec['conditions'])
        assert all(sha(Path(r['run'])/'AUDIT.json')==r['audit_sha256'] for r in rows)
        strict=sum(r['audit']['strict_success'] for r in rows);task=sum(r['audit']['task_success'] for r in rows)
        incomplete=sum(not read(Path(r['run'])/'rollout.json')['full_task_horizon_completed'] for r in rows)
        penetration=max(max(r['audit']['penetration_mm'],r['audit']['edge_penetration_mm']) for r in rows)
        rmse=statistics.mean(r['audit']['rmse_mm'] for r in rows);torque=statistics.mean(r['audit']['peak_torque_nm'] for r in rows)
        score=[-strict,-task,incomplete,penetration,rmse,torque,candidate['name']]
        ranked.setdefault(candidate['category'],[]).append(dict(candidate=candidate,score=score,
            strict=strict,task=task,denominator=len(rows),incomplete=incomplete,mean_rmse_mm=rmse,
            mean_peak_torque_nm=torque,worst_penetration_mm=penetration))
    count=1 if a.final_choice else 2
    for values in ranked.values():values.sort(key=lambda x:x['score'])
    assert len(ranked)==4 and all(len(v)>=count for v in ranked.values())
    chosen=[entry['candidate'] for values in ranked.values() for entry in values[:count]]
    result=dict(protocol_sha256=spec['protocol_sha256'],baseline_priors_sha256=spec['baseline_priors_sha256'],
        source_sha256=sha(Path(__file__)),screen_spec_sha256=sha(a.screen/'SPECIFICATION.json'),
        screen_summary_sha256=sha(a.screen/'SUMMARY.json'),ranked=ranked,candidates=chosen,
        conditions=[f'development_{i:03d}' for i in range(8)],
        selection='Registered strict/task counts, full horizon, worst penetration, RMSE, actuator peak, lexical name; no speed maximization.',
        outcome='one per family selected on all eight development identities' if a.final_choice else 'two per family advance to common eight-identity confirmation',
        repeated_conditions='The two screen conditions repeated during confirmation are not independent new generalization tests.',
        training_or_final_use='development selection only; neither a final result nor permission to read sealed conditions')
    if a.final_choice:assert len(spec['conditions'])==8
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(selected=[c['name'] for c in chosen],output=str(a.output),sha256=sha(a.output))))


if __name__=='__main__':main()
