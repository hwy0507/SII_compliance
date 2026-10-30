from pathlib import Path
import json,math,hashlib,time
import numpy as np
D=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
r=read(D/'REVIEW.json');assert r['passed'];checked=0;actions=0
for m,v in r['methods'].items():
 for c in v['cases']:
  paths={Path(x['path']).name:Path(x['path']) for x in c['sources']}
  for x in c['sources']+[c['derived']]:
   p=Path(x['path']);assert p.stat().st_size==x['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
  lines=paths['actor_intervals.jsonl'].read_text().splitlines();terminal=read(paths['TERMINAL.json'])
  with np.load(c['derived']['path']) as z:
   previous=0.;elapsed=[];bad=[];cross=[]
   for i,line in enumerate(lines):
    row=json.loads(line);iv=row['interval']
    actual=0. if iv is None else float(iv['external_penetration_peak_m'])
    if iv is not None:elapsed.append(float(iv['elapsed_s']))
    assert actual==z['preaction_peak_m'][i] and actual>=previous
    assert bool(z['preaction_penetration_gate_valid'][i])==(actual<=.0002)
    assert abs(float(z['action_time_s'][i])-math.fsum(elapsed))<1e-6
    next_iv=json.loads(lines[i+1])['interval'] if i+1<len(lines) else terminal['interval']
    nxt=float(next_iv['external_penetration_peak_m']);assert nxt==z['next_observation_peak_m'][i]
    if actual>.0002:bad.append(i)
    if actual<=.0002<nxt:cross.append(i)
    previous=actual
   assert len(bad)==c['preactions_after_violation'] and (bad[0] if bad else None)==c['first_bad_preaction_index']
   assert cross==c['crossing_transition_indices']
   assert bool(z['preaction_peak_m'][-1]<=.0002<z['next_observation_peak_m'][-1])==c['terminal_only_violation']
  checked+=1;actions+=len(lines)
assert checked==90 and actions==123750
out=dict(passed=True,time=time.time(),episodes=checked,actions=actions,independent_scalar_journal_reread=True,math_fsum_clock=True,original_source_hashes_unchanged=True,limitation='Shared saved-journal/source evidence; not independent physical penetration reconstruction or full historical replay coverage.')
with (D/'SAVED_REVIEW.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(out)
