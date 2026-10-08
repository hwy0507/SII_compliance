"""Continue the registered cohort after draining the original dispatcher.

Only scheduling changes. All simulations use the original immutable source.
Existing successful worker outputs are audited, never simulated a second time.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import json
from pathlib import Path
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--workers', type=int, choices=(8,), default=8)
    p.add_argument('--run', action='store_true')
    p.add_argument('--drain', action='store_true', help='Stop new dispatch only; let all existing simulations finish')
    a = p.parse_args(); root = a.root.resolve(); source = root/'source'
    sys.path.insert(0, str(source/'tools'))
    import office_v7_uniform24_20261008 as old
    protocol = old.read(root/'PROTOCOL.json')
    for name, key in (('SOURCE_HASHES.json','source_manifest_sha256'),
                      ('MODEL_MANIFEST.json','model_manifest_sha256'),
                      ('CONDITIONS.json','condition_file_sha256')):
        assert old.sha(root/name) == protocol[key]
    for rel, digest in old.read(root/'SOURCE_HASHES.json').items():
        assert old.sha(source/rel) == digest, rel
    candidates = old.read(root/'MODEL_MANIFEST.json')['candidates']
    conditions = old.read(root/'CONDITIONS.json')['conditions']
    jobs = [(c,d) for d in conditions for c in candidates]
    counts = {}
    for c,d in jobs:
        receipt = root/'episodes'/(c['family']+'__'+d['id']+'.execution.json')
        status = old.read(receipt)['status'] if receipt.exists() else 'not_dispatched'
        counts[status] = counts.get(status,0)+1
    print(json.dumps(dict(plan=counts,workers=a.workers,simulation_source='unchanged')),flush=True)
    original_unit = 'sii-office-v7-uniform24-20261008.service'
    assert not (a.run and a.drain)
    if a.drain:
        record = root/'DRAIN_V2.json'
        assert not record.exists()
        assert not (root/'report_final').exists()
        running = subprocess.check_output(['systemctl','--user','list-units','sii-v724-*',
                                          '--state=running','--no-legend','--plain'],text=True)
        assert len(running.splitlines())==4, 'Drain only at the observed four-worker wait boundary'
        command = subprocess.check_output(['systemctl','--user','show',original_unit,'-p','ExecStart','--value'],text=True)
        assert str(source/'tools/office_v7_uniform24_20261008.py') in command
        old.write(record,dict(started_utc=old.now(),counts=counts,active_worker_units=running,
                             dispatcher_command=command,source_sha256=old.sha(__file__),
                             action='pause only original dispatcher; let worker units finish'))
        subprocess.run(['systemctl','--user','stop','sii-office-v7-uniform24-report-20261008.service'],check=True)
        subprocess.run(['systemctl','--user','kill','--kill-whom=main','--signal=SIGSTOP',original_unit],check=True)
        return
    if not a.run:
        return
    state = subprocess.run(['systemctl','--user','is-active',original_unit],capture_output=True,text=True)
    assert state.stdout.strip() in ('inactive','failed','unknown'), state.stdout
    units = subprocess.check_output(['systemctl','--user','list-units','sii-v724-*',
                                     '--state=running','--no-legend','--plain'],text=True)
    assert not units.strip(), 'Existing workers must finish before dispatch handoff'
    with (root/'.coordinator.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        addendum = root/'DISPATCH_V2.json'
        assert not addendum.exists(), 'Never overwrite an existing dispatch revision'
        old.write(addendum, dict(created_utc=old.now(),authorization='2026-10-08 user: fully use compute',
            previous_workers=4,workers=8,source_sha256=old.sha(__file__),
            protocol_sha256=old.sha(root/'PROTOCOL.json'),unchanged='physics, gates, models, conditions, actor inputs',
            memory_max_per_worker='3GiB',threads_per_worker=1,cpu_affinity='5-9,15-19',
            original_dispatch_status=old.read(root/'execution.json'),initial_counts=counts))
        managed = old.managed
        def fast_managed(source, command, label):
            command_line = managed(source, command, label)
            command_line.insert(1,'--property=AllowedCPUs=5-9,15-19')
            command_line.insert(1,'--property=CPUAffinity=5-9,15-19')
            return command_line
        old.managed = fast_managed
        recovery = root/'analysis_dispatch_v2'; recovery.mkdir(exist_ok=False)
        def finish_existing(c,d):
            name = c['family']+'__'+d['id']; run = root/'episodes'/name
            receipt = root/'episodes'/(name+'.execution.json'); row = old.read(receipt)
            assert row['status']=='running', (name,row['status'])
            log = (root/'episodes'/(name+'.log')).read_text()
            assert 'Finished with result: success' in log, name+' worker did not finish successfully'
            assert (run/'OFFICE_V7_ROLE.json').is_file()
            audit = old.read(run/'AUDIT.json'); args = old.read(run/'execution.json')['arguments']
            assert audit['model_sha256']==old.FORMAL
            assert all(args[k]==v for k,v in d['overrides'].items())
            assert args['dt']==protocol['physics_dt_s']
            metric = recovery/(name+'.json')
            cmd = [sys.executable,str(source/'tools/paper_metrics_20261002.py'),'--run',str(run),'--output',str(metric)]
            with metric.with_suffix('.log').open('x') as out:
                subprocess.run(old.managed(source,cmd,'sii-v724-resume-'+name.replace('_','-')),
                               stdout=out,stderr=subprocess.STDOUT,check=True)
            m = old.read(metric)
            assert m['trace_sha256']==audit['trace_sha256']==old.sha(run/'rollout.npz')
            for k in ('rmse_mm','peak_torque_nm','peak_speed_mps'):
                assert abs(m[k]-audit[k])<1e-4
            # Preserve the original receipt as evidence of the planned handoff.
            old.write(recovery/(name+'.original_receipt.json'),row)
            row.update(status='complete',returncode=0,ended_utc=old.now(),audit=audit,
                audit_sha256=old.sha(run/'AUDIT.json'),trace_sha256=old.sha(run/'rollout.npz'),
                metrics=str(metric),metrics_sha256=old.sha(metric),
                resumed_after_dispatch_drain=True,physics_rerun=False)
            old.write(receipt,row)
            return row
        # Finish pending audits before launching any new physics.
        for c,d in jobs:
            receipt = root/'episodes'/(c['family']+'__'+d['id']+'.execution.json')
            if receipt.exists() and old.read(receipt)['status']!='complete':
                finish_existing(c,d)
        old.write(root/'execution.json',dict(status='running',dispatch_revision=2,workers=8,
                   started_utc=old.now(),expected=384))
        errors=[]
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            futures={pool.submit(old.one,root,c,d): (c['family'],d['id']) for c,d in jobs}
            for future in as_completed(futures):
                try: future.result()
                except Exception as exc:
                    errors.append(dict(job=futures[future],error=repr(exc)))
                    for pending in futures: pending.cancel()
                    # Running episodes finish; undispatched episodes remain pending.
                    break
        summary=old.summarize(root)
        old.write(root/'execution.json',dict(status='complete' if summary['completed']==384 else 'incomplete_preserved',
            dispatch_revision=2,workers=8,ended_utc=old.now(),completed=summary['completed'],expected=384,errors=errors))
        if errors: raise RuntimeError(errors)


if __name__=='__main__':
    main()
