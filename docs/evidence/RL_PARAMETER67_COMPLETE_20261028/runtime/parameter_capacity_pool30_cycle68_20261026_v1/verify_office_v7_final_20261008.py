import json,pathlib,hashlib,importlib.util,datetime,math
p=pathlib.Path('/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008')
s=p/'reporting_source/report_office_v7_uniform24_20261008.py'
sp=importlib.util.spec_from_file_location('report',s); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
r=json.loads((p/'report_final/REPORT.json').read_text())
assert r==m.build(p)
assert r['complete'] and r['completed']==384
assert len({(v['family'],v['condition_id']) for v in r['rows']})==384
assert all(f['completed']==24 and f['short']==0 for f in r['families'])
for row in r['rows']:
 assert hashlib.sha256(pathlib.Path(row['receipt']).read_bytes()).hexdigest()==row['receipt_sha256']
rl={}
for f in ['parameter_vmc','parameter_admittance','parameter_impedance','direct_metric','direct_office_task']:
 rr=[v for v in r['rows'] if v['family']==f]
 assert all(v['audit']['raw_actor_replay_max_abs']==0 and v['audit']['normalization_unchanged'] for v in rr)
 rl[f]=len(rr)
a={v['condition_id']:v['audit'] for v in r['rows'] if v['family']=='esn'}
b={v['condition_id']:v['audit'] for v in r['rows'] if v['family']=='matched_rnn'}
paired={}
for k in ['task_success','strict_success']:
 w=sum(a[c][k] and not b[c][k] for c in a); l=sum(b[c][k] and not a[c][k] for c in a); n=w+l
 prob=min(1,2*sum(math.comb(n,i) for i in range(min(w,l)+1))/2**n) if n else 1
 paired[k]=dict(esn_only=w,rnn_only=l,exact_mcnemar_two_sided_p=prob)
out={k:r[k] for k in ['complete','planned','completed','families','protocol_sha256','model_manifest_sha256','condition_file_sha256','report_source_sha256','interpretation','root']}
out.update(verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),report_hashes={f:hashlib.sha256((p/'report_final'/f).read_bytes()).hexdigest() for f in ['REPORT.md','REPORT.json']},verification=dict(rebuilt_report_exact=True,unique_episode_identities=384,all_receipt_audit_metrics_hashes=True,all_full_horizon=True,rl_exact_replays_and_frozen_normalization=rl),paired_esn_matched_rnn=paired,execution=json.loads((p/'execution.json').read_text()))
print('VERIFIED_JSON_BEGIN')
print(json.dumps(out,indent=2))
