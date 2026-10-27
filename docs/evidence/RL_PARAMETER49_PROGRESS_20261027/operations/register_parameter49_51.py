from pathlib import Path
import ast,json,hashlib,difflib,time,os,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');S=B/'runs/parameter_capacity46_48_reward_stability_20261027_v1';O=B/'runs/parameter_capacity49_51_reward_stability_20261027_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
old=(S/'audit_parameter46_48_reward_stability_20261027.py').read_text();new=old.replace('46-48','49-51').replace('[46, 47, 48]','[49, 50, 51]').replace('2026102747','2026102748').replace('paired46_to48','paired49_to51')
a=new.index('            if cycle < 48:');b=new.index('            protocols.append(p)',a)
new=new[:a]+'''            followup = p['replay_capacity_followup_stage']
            assert followup['parent_cycle'] == 47 and followup['historical_entry_cycle'] == 23
            assert followup['old_capacity'] == 2_000_000 and followup['new_capacity'] == 4_000_000
            assert followup['marker'] == reg['followup_marker']
            assert not followup['auxiliary_weights_imported'] and not followup['optimizer_settings_changed']
            assert row['replay_capacity_followup'] == followup['marker'] and row['current_replay_capacity'] == 4_000_000
            assert deps == baseline_deps
            if protocols:
                assert followup == protocols[0]['replay_capacity_followup_stage']
            for evidence_key in ['preparation_review','malformed_state_review']:
                ref=followup[evidence_key]; assert sha(ref['path'])==ref['sha256']
                assert json.loads(Path(ref['path']).read_text())['passed']
            entry=followup['entry_checkpoint']
            assert sha(entry['path']) == entry['sha256']
            historical_review = B/'runs/parameter_capacity_pool30_cycle47_review_20261026_v1/REVIEW.json'
            historic=json.loads(historical_review.read_text()); assert historic['passed']
            assert entry['sha256'] == historic['methods'][method]['checkpoint_sha256']
            assert deps['parameter_replay_capacity4m_20261027.py'] == followup['helper_sha256']
            assert deps['resume_cheq_capacity4m_pool30_20261027.py'] == p['batch_size_stage']['driver_sha256']
'''+new[b:]
new=new.replace('def main(root):',"B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')\n\ndef main(root):")
a=new.index("        limitation='");b=new.index("')\n    (root/'REVIEW.json')",a)
new=new[:a]+"        limitation='Fixed49-51 window on30 registered training conditions, chosen while49 had0 completed conditions and50-51 were not launched. All complete outcomes are future at registration. Capacity4m throughout, with immutable historicalentry23/47 and identical dependencies. Original5percent/nearzero1/5000 condition bootstrap and real episode lengths retained. Online policies change; paired intervals measure condition-composition sensitivity, not independent training seeds or frozen-policy performance. Finite losses and5percent alone do not declare healthy convergence or unlock test."+new[b:]
wait=(S/'wait_register_and_audit.py').read_text().replace('46-48','49-51').replace('[46, 47, 48]','[49, 50, 51]').replace('audit_parameter46_48','audit_parameter49_51').replace('cycle == 46','cycle == 49').replace("plan['protocol46']","plan['protocol49']")
# Verify the statistical body is unchanged except the explicit window result label.
start='        ids = sorted(maps[0])';end='        axes[mi, 0].plot'
assert old[old.index(start):old.index(end)].replace('paired46_to48','paired49_to51')==new[new.index(start):new.index(end)]
for s in [new,wait]:ast.parse(s)
progress={};refs={}
for m in ['impedance','admittance','vmc']:
 r=B/'runs/parameter_capacity_pool30_cycle49_20261026_v1'/m;p=json.loads((r/'train/PROGRESS.json').read_text());assert p['completed_conditions']==0;progress[m]=p;refs[m]=dict(path=str(r/'REGISTRATION.json'),sha256=sha(r/'REGISTRATION.json'))
for c in [50,51]:assert not (B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/LAUNCH.json').exists()
O.mkdir();source=O/'audit_parameter49_51_reward_stability_20261027.py';source.write_text(new);(O/'wait_register_and_audit.py').write_text(wait);(O/'SOURCE.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original46_48',tofile='prospective49_51')))
plan=json.loads((S/'PLAN.json').read_text());plan.update(cycles=[49,50,51],bootstrap_seed=2026102748,source_sha256=sha(source),time=time.time(),registration_state='49 live with0 completed conditions;50/51 unlaunched;4m throughout',registration_progress=progress,reason='Next future fixed three-cycle window; original formulas unchanged, no outcome-selected window;4m throughout and historicalentry47 unchanged',protocol49=refs);del plan['protocol46'];write(O/'PLAN.json',plan)
write(O/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),original_source_sha256=sha(S/'audit_parameter46_48_reward_stability_20261027.py'),source_sha256=sha(source),statistical_body_unchanged_except_window_label=True,capacity=4000000,historical_entries=[23,47],new_physics=0,optimizer_updates=0))
cmd=['taskset','-c','54',str(B/'env/bin/python'),str(O/'wait_register_and_audit.py')]
with (O/'driver.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
write(O/'LAUNCH.json',dict(pid=p.pid,time=time.time(),command=cmd,start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19]));print(p.pid)
