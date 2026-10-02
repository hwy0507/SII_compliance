"""Freeze declared final models using completed development evidence only.

Historical baselines and paired student seeds are retained by name. Classical
search winners use a registered lexicographic rule, never final-condition data.
"""
import argparse,json,math
from pathlib import Path
from optimize_tool_contact_20261002 import sha,write,now

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--specification',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();spec=json.loads(a.specification.read_text())
    candidates=[];evidence=[];selection=[];cache={}
    def load(phase):
        if phase in cache:return cache[phase]
        path=root/phase;record=json.loads((path/'execution.json').read_text())
        assert record['status']=='complete' and not record.get('validation_lock_sha256'), 'Requires completed development batch'
        manifest=json.loads((path/'manifest.json').read_text());mapping={r['name']:r for r in manifest['candidates']}
        analyses=root/spec.get('analysis_aliases',{}).get(phase,phase+'_analysis')
        analysis=json.loads((analyses/'execution.json').read_text());assert analysis['status']=='complete'
        assert Path(analysis['phase']).resolve()==path
        independent=json.loads((analyses/'INDEPENDENT_AUDIT.json').read_text());assert not independent['pending']
        verified={Path(r['run']).name:r for r in independent['rows']}
        assert len(verified)==len(record['rows'])
        for row in record['rows']:
            assert row['returncode']==0 and row['name'] in verified
            v=verified[row['name']]
            assert v['frozen_source_hashes_verified'] and v['actuator_amplitude_and_command_slew_valid']
        result=(path,mapping,verified,analyses);cache[phase]=result;return result
    def add(phase,name,role):
        path,mapping,verified,analyses=load(phase);row=mapping[name];audit=verified[name]
        assert name not in [r['name'] for r in candidates]
        if row.get('checkpoint'):assert sha(Path(row['checkpoint']))==row['checkpoint_sha256']
        candidates.append(row)
        evidence.append(dict(name=name,role=role,development_run=str(path/name),
            task_success=audit['task_success'],strict_success=audit['strict_success'],
            development_trace_sha256=audit['trace_sha256'],development_audit_sha256=sha(analyses/'INDEPENDENT_AUDIT.json'),
            source_manifest_sha256=sha(path/'manifest.json')))
    for group in spec['fixed_groups']:
        _,mapping,_,_=load(group['phase'])
        names=list(mapping) if group.get('all') else group['names']
        for name in names:add(group['phase'],name,group['role'])
    for group in spec['classical_search']:
        _,mapping,verified,_=load(group['phase'])
        names=[n for n,c in mapping.items() if c['category']==group['category']]
        assert len(names)==group['expected_candidates']
        def score(name):
            v=verified[name];pen=max(v['penetration_mm'],v['edge_penetration_mm'])
            values=(pen,v['placement_error_xy_m'],v['rmse_mm']);assert all(math.isfinite(x) for x in values)
            return (-int(v['strict_success']),-int(v['task_success']),-int(v['full_horizon']),
                    max(0.,pen-.2),v['placement_error_xy_m'],v['rmse_mm'],name)
        ordered=sorted(names,key=score);winner=ordered[0]
        selection.append(dict(category=group['category'],selected=winner,ranked_development_candidates=[dict(name=n,key=score(n)) for n in ordered]))
        add(group['phase'],winner,group['role'])
    assert len(candidates)<=48
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    write(out/'manifest.json',dict(created_utc=now(),candidates=candidates))
    lock=dict(status='models_frozen_before_final_evaluation',created_utc=now(),candidates=candidates,
        specification_sha256=sha(a.specification),source_sha256=sha(Path(__file__)),development_evidence=evidence,
        classical_selection=selection,training_closed=True,
        rules='No fitting, tuning or model selection after final evaluation. Both paired seeds retained. Failure/abort results retained. No weighted superiority score.')
    write(out/'VALIDATION_LOCK.json',lock)
    formal=[c for c,e in zip(candidates,evidence) if e['strict_success']]
    write(out/'formal_manifest.json',dict(created_utc=now(),candidates=formal,
        eligibility='All selected models with unchanged task/strict success on the development anchor, frozen before final conditions'))
    write(out/'selection_specification.json',spec)
    print(json.dumps(dict(selected=len(candidates),formal_eligible=len(formal),lock_sha256=sha(out/'VALIDATION_LOCK.json'))))

if __name__=='__main__':main()
