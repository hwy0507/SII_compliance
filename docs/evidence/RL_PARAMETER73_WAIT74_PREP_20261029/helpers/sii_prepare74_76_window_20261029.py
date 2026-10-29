from pathlib import Path
import re,json,hashlib,ast,difflib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1';new=B/'runs/parameter_capacity74_76_reward_stability_20261029_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
assert sha(old/'PLAN.json')=='c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf'
root=B/'runs/parameter_capacity_pool30_cycle73_20261026_v1'
for j in read(root/'LAUNCH.json')['jobs']+[read(old/'LAUNCH.json')]:
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
for c in [74,75,76]:assert not (B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/LAUNCH.json').exists()
new.mkdir(exist_ok=False);mapping={'71':'74','72':'75','73':'76'};items=[]
for name in ['audit_parameter71_73_reward_stability_20261028.py','review_saved.py','wait_register_and_audit.py']:
 a=(old/name).read_text();protected={}
 def protect(m):
  k='__HASH_'+chr(65+len(protected))+'__';protected[k]=m.group();return k
 masked=re.sub(r'\b[0-9a-f]{64}\b',protect,a)
 s=re.sub(r'(?<!\d)(71|72|73)(?!\d)',lambda m:mapping[m.group()],masked)
 inv={v:k for k,v in mapping.items()};assert re.sub(r'(?<!\d)(74|75|76)(?!\d)',lambda m:inv[m.group()],s)==masked
 for k,v in protected.items():s=s.replace(k,v)
 # The audit source name retains its historical date suffix; all plan/run paths use the exact new directory.
 dest=re.sub(r'(?<!\d)(71|72|73)(?!\d)',lambda m:mapping[m.group()],name);ast.parse(s);(new/dest).write_text(s)
 (new/(dest+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(old/name),tofile=str(new/dest))))
 items.append(dict(name=dest,parent=str(old/name),parent_sha256=sha(old/name),sha256=sha(new/dest),inverse_exact=True,ast_passed=True))
p=read(old/'PLAN.json');p.update(cycles=[74,75,76],source_sha256=sha(new/'audit_parameter74_76_reward_stability_20261028.py'),time=time.time(),registration_state='Complete72 reviewed; original73 live;74/75/76 not launched. Conditional next consecutive nonoverlapping window; all prior windows retained.',registration_progress={m:read(root/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']},reason='Next consecutive future window only if continuation remains necessary after full73 and original71-73 review; no outcome-selected endpoints. Original71-73 remains live and must be fully reported. Original68-70 and all historical assessments retained. Original formula/5percent/nearzero1/seed2026102855/5000 bootstrap/anchor55 retained.',previous_plan=dict(path=str(old/'PLAN.json'),sha256=sha(old/'PLAN.json')),waiter_start_policy='Start only after scientifically reviewed actual74 launch if continuation is needed; fixed14400s wait then covers74-76. No automatic training or stopping.',waiter_launched=False)
for x in p['anchor_protocol55'].values():assert sha(Path(x['path']))==x['sha256']
assert p['bootstrap_seed']==2026102855 and p['replicates']==5000 and p['near_zero_guard']==1 and p['relative_limit']==.05
write(new/'PLAN.json',p);write(new/'SOURCE_REVIEW.json',dict(time=time.time(),passed=True,files=items,mapping=mapping,formula_threshold_seed_bootstrap_anchor55_unchanged=True,previous71_73_plan_unchanged_sha256=sha(old/'PLAN.json'),no_future_training_launched=True,no_waiter_launched=True,automatic_training=False,diagnostic_only=True))
print('Conditional74-76 PLAN',sha(new/'PLAN.json'))
