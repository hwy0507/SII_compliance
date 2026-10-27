from pathlib import Path
import json,hashlib,ast,time,shutil,difflib,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';oldrt=B/'runtime/serl_cycle16_frozen_full30_20261026_v1';rt=B/'runtime/serl_cycle26_frozen_full30_20261027_v1';out=B/'runs/serl26_frozen_capacity_validation_20261027_v1';rt.mkdir(exist_ok=False);out.mkdir(exist_ok=False)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
oldreg=json.loads((B/'runs/serl_cycle16_frozen_full30_20261026_v1/REGISTRATION.json').read_text())
for name,ref in oldreg['sources'].items():
 p=Path(ref['path']);assert sha(p)==ref['sha256'];shutil.copyfile(p,rt/name)
formal=B/'runtime/serl_capacity_batch65536_cycle25_20261027_v1'
for n,h in [('serl_replay_capacity_20261027.py','c39abba32814bc713c58945eb3405f33118e1881b76fb60622c87a010132dd27'),('resume_serl_capacity_reviewed_continuation_20261027.py','0ca9b613fb0e2e0f360769ca3ec9ae9f1674ef7b295f4de25986a3ba054b9e81')]:
 assert sha(formal/n)==h;shutil.copyfile(formal/n,rt/n)
old=oldrt/'evaluate_serl_seeded_multistep_20261026.py';s=old.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace('    torch.set_num_threads(1)', '''    if not args.check_only and args.expected_cycle != 26:
        raise ValueError('Physical evaluation is registered only for complete26')
    if args.expected_cycle < 24:
        raise ValueError('Expanded replay checkpoints only')
    torch.set_num_threads(1)''')
replace("    controller, algorithm = checkpoint['controller'], checkpoint['learner']['algorithm']", """    if checkpoint['cycle'] != args.expected_cycle:
        raise ValueError('Exact registered checkpoint cycle required')
    controller, algorithm = checkpoint['controller'], checkpoint['learner']['algorithm']""")
replace("    prior = json.loads((root/'parameter/PRIORS.json').read_text())", """    # Restore the persisted2m replay with the already validated strict loader.
    # No sampling, insertion, legacy migration or optimization is performed.
    from resume_serl_capacity_reviewed_continuation_20261027 import validate_capacity, capacity_replay
    from train_serl_state_20261026 import Replay
    previous_ref = protocol['resume_parent_registration']
    if sha(previous_ref['path']) != previous_ref['sha256']:
        raise ValueError('Previous registration hash changed')
    previous = json.loads(Path(previous_ref['path']).read_text())
    validate_capacity(protocol, previous)
    if checkpoint['cycle'] != protocol['reviewed_continuation_stage']['parent_cycle'] + 1:
        raise ValueError('Checkpoint and registered continuation do not match')
    for name, expected in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        if sha(root/'source'/name) != expected:
            raise ValueError('Frozen source mismatch: '+name)
    if checkpoint['replay'].get('replay_capacity_extension') != protocol['replay_capacity_stage']['marker']:
        raise ValueError('Persisted capacity marker required; evaluation cannot migrate')
    expanded = capacity_replay(Replay, protocol, checkpoint)
    replay = expanded(7, 49, 20261079)
    replay.load_state_dict(checkpoint['replay'])
    replay_digest = digest(replay.state_dict())
    if replay_digest != digest(checkpoint['replay']):
        raise ValueError('Full expanded replay restoration changed state')
    history_digest = digest(checkpoint.get('history'))
    prior = json.loads((root/'parameter/PRIORS.json').read_text())""")
replace("    receipt = dict(scope=", """    write(output/'FULL_STATE_RESTORE.json', dict(passed=True,
        checkpoint_sha256=sha(snapshot), cycle=checkpoint['cycle'],
        full_learner_state_exact=True, full_replay_state_exact=True,
        learner_digest=initial_state, replay_digest=replay_digest,
        history_digest=history_digest, replay_capacity=replay.capacity,
        replay_size=replay.size, historical_capacity_entry=23,
        optimizer_updates=0, new_physics=0, replay_writes=0))
    if args.check_only:
        assert digest(replay.state_dict()) == replay_digest
        assert digest(learner.state_dict()) == initial_state
        write(output/'CHECK_ONLY_REVIEW.json', dict(passed=True,
            full_learner_state_exact=True, full_replay_state_exact=True,
            external_action_rng_gate=bool(args.stochastic),
            optimizer_updates=0, new_physics=0, replay_writes=0,
            checkpoint_sha256=sha(snapshot), cycle=checkpoint['cycle']))
        return
    receipt = dict(scope=""")
replace("    unchanged = digest(learner.state_dict()) == initial_state", """    replay_unchanged = digest(replay.state_dict()) == replay_digest
    assert replay_unchanged and digest(checkpoint.get('history')) == history_digest
    unchanged = digest(learner.state_dict()) == initial_state""")
replace("        new_optimizer_updates=learner.learner.num_gradient_steps-initial_updates))", """        new_optimizer_updates=learner.learner.num_gradient_steps-initial_updates,
        full_replay_state_unchanged=replay_unchanged, replay_writes=0,
        replay_digest=replay_digest, history_digest=history_digest))""")
replace("    parser.add_argument('--device', default='cuda:0')", """    parser.add_argument('--expected-cycle', type=int, required=True)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--device', default='cuda:0')""")
name='evaluate_serl_capacity_frozen_20261027.py';ast.parse(s);(rt/name).write_text(s);(R/'code/mujoco_6d_vmc_benchmark/tools'/name).write_text(s)
(out/'SOURCE.diff').write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),s.splitlines(True),fromfile=str(old),tofile=str(rt/name))))
# Actual24 probe is restore+external action sampling only, no dynamics or optimizer.
parent=B/'runs/serl_capacity_batch65536_cycle24_20261027_v1/REGISTRATION.json';checkpoint=B/'runs/serl_capacity_batch65536_cycle24_archive_20261027_v1/direct/cycle_00024.pt';review=B/'runs/serl_capacity_batch65536_cycle24_review_20261027_v1/REVIEW.json'
assert json.loads(review.read_text())['methods']['direct']['checkpoint_sha256']==sha(checkpoint)
protocol=json.loads(parent.read_text());helper_checks=[]
for name,expected in {**protocol['source_adapter_hashes'],**protocol['multistep_stage']['source_hashes'],**protocol['gather_stage']['source_hashes']}.items():
 if (rt/name).exists():assert sha(rt/name)==expected;helper_checks.append(name)
reg=dict(time=time.time(),purpose='Validate new capacity-aware frozen evaluator on immutable complete24 before prospective complete26 evaluation; no24 physics, no optimization, no repeated completed rollout.',expected_cycle=24,source_sha256=sha(rt/'evaluate_serl_capacity_frozen_20261027.py'),checkpoint=str(checkpoint),checkpoint_sha256=sha(checkpoint),training_registration=str(parent),training_registration_sha256=sha(parent),unchanged_helper_checks=helper_checks,timeout_seconds=600,optimizer_updates=0,new_physics=0)
(out/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n')
command=[str(B/'serl_env/bin/python'),str(rt/'evaluate_serl_capacity_frozen_20261027.py'),'--runtime',str(B/'runtime/source_train17_clock'),'--registration',str(parent),'--checkpoint',str(checkpoint),'--output',str(out/'restore24'),'--expected-cycle','24','--check-only','--device','cpu','--learner-cpu','52','--physics-cpu','53','--serl-upstream',str(B/'runtime/serl_upstream_1fa2af7'),'--serl-manifest',str(B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json'),'--sampler-python',str(B/'env/bin/python'),'--stochastic','--action-seed','2026102626','--audit-substeps']
(out/'COMMAND.json').write_text(json.dumps(command,indent=2)+'\n')
subprocess.run([str(B/'serl_env/bin/python'),str(rt/'evaluate_serl_capacity_frozen_20261027.py'),'--help'],check=True,stdout=subprocess.DEVNULL)
with (out/'driver.log').open('x') as log:p=subprocess.Popen(['timeout','600',*command],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(__import__('os').environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
(out/'LAUNCH.json').write_text(json.dumps(dict(pid=p.pid,time=time.time(),command=command),indent=2)+'\n');print('Capacity frozen restore-only validation',p.pid)
