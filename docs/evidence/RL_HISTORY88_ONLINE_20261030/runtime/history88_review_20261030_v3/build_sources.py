from pathlib import Path
import ast,json,hashlib,difflib
D=Path(__file__).parent;B=D.parents[1];I=B/'runtime/history87_critic_interface_20261030_v1';OLD=B/'runtime/parameter86_half_std_paired_20261030_v3';V=B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in OLD.glob('*.py'):
 if p.name not in {'prepare.py','launch.py','preflight.py'}:(D/p.name).write_bytes(p.read_bytes())
for n in ['persisted_history_critic.py','history_consumers.py']:(D/n).write_bytes((I/n).read_bytes())
records=[]
def save(name,source,original):
 ast.parse(source);(D/name).write_text(source);(D/(name+'.diff')).write_text(''.join(difflib.unified_diff(original.read_text().splitlines(True),source.splitlines(True),fromfile=str(original),tofile=str(D/name))));records.append(dict(name=name,parent=str(original),parent_sha256=sha(original),sha256=sha(D/name)))
p=OLD/'evaluate_parameter29_seeded_switch_20261026.py';s=p.read_text();s=s[:s.index('\ndef main(')]
# Gate now receives raw journal rows, so clock/history timing is testable.
a="        native = [learner.act(obs, step=checkpoint['steps'], deterministic=False)\n                  for obs in observations]";b="        native = []\n        for row in observations:\n            learner.consume_interval(row['interval'])\n            native.append(learner.act(row['observation'], step=checkpoint['steps'], deterministic=False))";assert s.count(a)==1;s=s.replace(a,b)
a="        actual = external.call(learner.act, observation, step=checkpoint['steps'], deterministic=False)";b="        learner.consume_interval(observation['interval'])\n        actual = external.call(learner.act, observation['observation'], step=checkpoint['steps'], deterministic=False)";assert s.count(a)==1;s=s.replace(a,b)
s=s.replace("    different = other.call(learner.act, observations[0], step=checkpoint['steps'], deterministic=False)","    learner.consume_interval(observations[0]['interval'])\n    different = other.call(learner.act, observations[0]['observation'], step=checkpoint['steps'], deterministic=False)")
a="            obs, raw, action, context = learner.act(row['observation'], step=ck['steps'], deterministic=False)";assert s.count(a)==1;s=s.replace(a,"            learner.consume_interval(row['interval'])\n"+a)
s=s.replace("assert obs.shape == (50,) and obs[-1]", "assert obs.shape == (51,) and obs[49]")
a="            max_error = max(max_error, float(np.max(abs(action-np.asarray(row['action'])))))";assert s.count(a)==1;s=s.replace(a,a+"\n        learner.consume_interval(terminal['interval'])")
s="\"\"\"History51 gate and native replay; preserves original physical/filter/torque review.\"\"\"\n"+s[s.index('from pathlib'):];save('frozen_helpers.py',s,p)
p=OLD/'evaluate_parameter82_frozen_full30_20261030.py';s=p.read_text().replace('evaluate_parameter29_seeded_switch_20261026','frozen_helpers').replace('complete82','complete88').replace('planned82','planned88').replace('validation81','validation87').replace('expected_cycle=82','expected_cycle=88').replace('(81, 82)','(88,)').replace('expected_cycle != 82','expected_cycle != 88')
s=s.replace("    replay = replay_class(Replay)(ck['replay']['arrays']['actions'].shape[1], 50, 2026102638)","    from persisted_history_critic import history_class, history_replay_class, marker as history_marker, KEY\n    binding = protocol['history_critic_amendment']['binding']\n    assert ck['history_critic_amendment'] == protocol['history_critic_amendment']\n    assert ck['learner'][KEY] == ck['replay'][KEY] == history_marker(binding)\n    replay = history_replay_class(replay_class(Replay), binding)(ck['replay']['arrays']['actions'].shape[1], 51, 2026102638)")
s=s.replace('learner = pair_class(PublishedLearner, reduction)(root,','learner = history_class(pair_class(PublishedLearner, reduction), binding)(root,')
s=s.replace("observations = [json.loads(next(stream))['observation'] for _ in range(3)]","observations = [json.loads(next(stream)) for _ in range(3)]")
a="                    if event['kind'] == 'terminal':";assert s.count(a)==1;s=s.replace(a,"                    learner.consume_interval(event['interval'])\n"+a)
s=s.replace("choices=(81, 82)","choices=(88,)").replace('default=82','default=88').replace('choices=[81,82]','choices=[88]')
s=s.replace('complete82 frozen','complete88 frozen');save('evaluate_history88.py',s,p)
p=V/'diagnose_published_training_20261025.py';s=p.read_text();a="        learner = PublishedLearner(root, dimension=dimension, direct=method == 'direct',";b="        from persisted_history_critic import history_class, marker as history_marker, KEY\n        protocol = json.loads((folder.resolve().parent/'REGISTRATION.json').read_text())\n        binding = protocol['history_critic_amendment']['binding']\n        assert state[KEY] == checkpoint['replay'][KEY] == history_marker(binding)\n        learner = history_class(PublishedLearner, binding)(root, dimension=dimension, direct=method == 'direct',";assert s.count(a)==1;s=s.replace(a,b);s=s.replace('Critic includes known remaining time; actor does not receive the clock feature. ','Critic includes remaining time and causal history; actor directly receives neither feature. ');save('health88.py',s,p)
(D/'diagnose_published_value_bound_20261025.py').write_bytes((V/'diagnose_published_value_bound_20261025.py').read_bytes())
(D/'GENERATED_SOURCES.json').write_text(json.dumps(dict(passed=True,files=records,full_frozen_evaluator_prepared_not_launched=True),indent=2)+'\n')
print('Prepared frozen gate/replay, full30 evaluator and health consumer')
