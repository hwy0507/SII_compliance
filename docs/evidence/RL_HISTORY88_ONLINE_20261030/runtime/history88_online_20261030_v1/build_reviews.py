from pathlib import Path
import ast,difflib,json,hashlib
D=Path(__file__).parent;B=D.parents[1];OLD=B/'runtime/prepare_recovery87_20261030_v1';V=B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1'
files=[]
def save(n,s,p):
 ast.parse(s);(D/n).write_text(s);(D/(n+'.diff')).write_text(''.join(difflib.unified_diff(p.read_text().splitlines(True),s.splitlines(True),fromfile=str(p),tofile=str(D/n))));files.append(dict(name=n,parent=str(p),sha256=hashlib.sha256(s.encode()).hexdigest()))
for name,parent in [('startup88.py',OLD/'startup87.py'),('review88.py',V/'review.py')]:
 s=parent.read_text().replace('parameter_partial75_recovery_cycle87_20261029_v1','parameter_history_cycle88_20261030_v1').replace('parameter_partial75_recovery_cycle87_archive_20261029_v1','parameter_history_cycle88_archive_20261030_v1').replace('cycle_00087','cycle_00088').replace("x['cycle']==87","x['cycle']==88").replace("old['cycle']==86","old['cycle']==87").replace("['parent_cycle']==86","['parent_cycle']==87").replace("['new_cycle']==87","['new_cycle']==88").replace("['cycle']==87","['cycle']==88").replace('Cycle87 archive','Cycle88 archive').replace('complete recovery86','complete recovery87')
 if name=='startup88.py':
  s=s.replace("OUT=Path(__file__).parent/'startup'","OUT=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle88_20261030_v1/startup')")
  a=" for k,v in old['replay']['arrays'].items():np.testing.assert_array_equal(v,a[k][:n])";b=" for k,v in old['replay']['arrays'].items():np.testing.assert_array_equal(v,a[k][:n,:50] if k in ('observations','next_observations') else a[k][:n])";assert a in s;s=s.replace(a,b)
  seam=" previous=json.loads(Path(reg['post_interruption_continuation']['parent_registration']['path']).read_text())"
  add="""
 from persisted_history_critic import marker,feature,KEY
 h=reg['history_critic_amendment'];assert x['history_critic_amendment']==h and s[KEY]==x['replay'][KEY]==marker(h['binding'])
 peaks=np.load(h['sidecar']['path'],mmap_mode='r')
 for col,key in enumerate(('observations','next_observations')):np.testing.assert_array_equal(a[key][:n,50],feature(peaks[:,col]))
 assert e['replay_observation_dimension']==51 and e['actor_observation_dimension']==49
"""
  assert seam in s;s=s.replace(seam,add+seam)
  seam="   np.testing.assert_array_equal(a['observations'][k,:48]"
  offset=s.index(seam);s=s[:offset]+"   assert a['observations'][k,50]==feature(0. if j['interval'] is None else j['interval']['external_penetration_peak_m']) and a['next_observations'][k,50]==feature(nxt['interval']['external_penetration_peak_m'])\n"+s[offset:]
 else:
  s=s.replace("OUT=Path(__file__).parent","OUT=B/'runs/parameter_history_cycle88_review_20261030_v1'")
  a="    for k,v in old['replay']['arrays'].items():assert np.array_equal(v,arr[k][:n])";assert a in s;s=s.replace(a,"    for k,v in old['replay']['arrays'].items():assert np.array_equal(v,arr[k][:n,:50] if k in ('observations','next_observations') else arr[k][:n])\n    from persisted_history_critic import marker,feature,KEY\n    h=reg['history_critic_amendment'];assert x['history_critic_amendment']==h and x['learner'][KEY]==x['replay'][KEY]==marker(h['binding'])\n    peaks=np.load(h['sidecar']['path'],mmap_mode='r')\n    for col,key in enumerate(('observations','next_observations')):np.testing.assert_array_equal(arr[key][:n,50],feature(peaks[:,col]))")
  seam="            error=abs(value-t['reward']);max_reward_error=max(max_reward_error,error);assert error<1e-10";assert seam in s
  s=s.replace(seam,seam+"""
            k=t['step']-1
            assert arr['observations'][k,50]==feature(0. if j['interval'] is None else j['interval']['external_penetration_peak_m'])
            assert arr['next_observations'][k,50]==feature(nxt['interval']['external_penetration_peak_m'])
            expected_current=np.r_[np.asarray(j['observation'],np.float32)/x['learner']['observation_scale'],np.float32(t['context']),np.float32((1375-i)/1375)].astype(np.float32)
            np.testing.assert_array_equal(arr['observations'][k,:50],expected_current)
            if t['done']:expected_next=np.r_[expected_current[:49],np.float32((1374-i)/1375)].astype(np.float32)
            else:expected_next=np.r_[np.asarray(nxt['observation'],np.float32)/x['learner']['observation_scale'],np.float32(ts[i+1]['context']),np.float32((1374-i)/1375)].astype(np.float32)
            np.testing.assert_array_equal(arr['next_observations'][k,:50],expected_next)
            np.testing.assert_array_equal(arr['actions'][k]*np.float32(t['context']),np.asarray(j['action'],np.float32))
""")
  s=s.replace('retained_replay_all_fields_exact=True,','retained_replay_all_old_fields_exact=True,retained_history_features_exact=True,new_current_next51_and_raw_mixed_action_exact=True,')
 save(name,s,parent)
# CLI choice correction found during source inspection, before execution.
p=D/'evaluate_history88.py';s=p.read_text().replace('choices=[81,82]','choices=[88]');p.write_text(s)
(D/'REVIEW_SOURCE_BUILD.json').write_text(json.dumps(dict(passed=True,files=files),indent=2)+'\n')
print('Built independent startup/full replay/history/reward review')
