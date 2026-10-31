from pathlib import Path
import ast,json,time,hashlib,difflib,shutil
D=Path(__file__).resolve().parent;B=D.parents[1];OLD=B/'runtime/history88_frozen_preparation_20261030_v1';BIT=B/'runtime/history89_violation_pipeline_20261030_v1'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def save(parent,name,s):
 ast.parse(s);(D/name).write_text(s);(D/(name+'.diff')).write_text(''.join(difflib.unified_diff(parent.read_text().splitlines(True),s.splitlines(True),fromfile=str(parent),tofile=str(D/name))))
for p in OLD.glob('*.py'):
 if p.name.startswith(('published_','parameter_','audit_','summarize_','replay_','validate_')) or p.name=='persisted_history_critic.py':shutil.copyfile(p,D/p.name)
for n in ['persisted_violation_critic.py','violation_consumers.py']:shutil.copyfile(BIT/n,D/n)
p=BIT/'frozen_helpers.py';s=p.read_text()
s=once(s,"            assert obs.shape == (52,) and obs[49] == np.float32((1375-index)/1375)","            assert obs.shape == (52,) and obs[49] == np.float32((1375-index)/1375)\n            from persisted_history_critic import feature\n            peak = 0. if row['interval'] is None else row['interval']['external_penetration_peak_m']\n            assert obs[50] == feature(peak) and obs[51] == float(peak > .0002)")
s=once(s,"        learner.consume_interval(terminal['interval'])\n    finally:","        learner.consume_interval(terminal['interval'])\n        terminal_obs = learner.terminal_observation(obs)\n        peak = terminal['interval']['external_penetration_peak_m']\n        assert terminal_obs[49] == np.float32((1375-len(rows))/1375)\n        assert terminal_obs[50] == feature(peak) and terminal_obs[51] == float(peak > .0002)\n    finally:")
s=s.rstrip()+'\n';save(p,'frozen_helpers.py',s)
p=OLD/'evaluate_history88.py';s=p.read_text().replace('88','90').replace('validation87','validation89')
architecture='''def validate_architecture(ck, protocol):
    from persisted_history_critic import KEY as HK, marker as hm
    from persisted_violation_critic import KEY as VK, marker as vm
    h = protocol['history_critic_amendment'];v = protocol['violation_critic_amendment'];b = v['binding']
    assert h['first_cycle'] == 88 and v['first_cycle'] == 90 and b['history_binding'] == h['binding']
    assert ck['history_critic_amendment'] == h and ck['violation_critic_amendment'] == v
    assert ck['controller'] == b['method'] and ck['cycle'] == 90 and ck['seed'] == 20261025
    assert b['rows'] < ck['steps'] <= b['rows']+41250
    for key in ['learner','replay']:
        assert ck[key][HK] == hm(h['binding']) and ck[key][VK] == vm(b)
    assert ck['replay']['size'] == ck['replay']['cursor'] == ck['steps']
    for key in ['observations','next_observations']:
        assert ck['replay']['arrays'][key].shape == (ck['steps'],52)


'''
s=once(s,'def validate_recovery(ck, protocol, expected_cycle):',architecture+'def validate_recovery(ck, protocol, expected_cycle):\n    validate_architecture(ck, protocol)')
s=once(s,"    from persisted_history_critic import history_class, history_replay_class, marker as history_marker, KEY", "    from persisted_history_critic import history_class, marker as history_marker, KEY\n    from persisted_violation_critic import violation_class, violation_replay_class\n    vb = protocol['violation_critic_amendment']['binding']")
s=once(s,"replay = history_replay_class(replay_class(Replay), binding)(ck['replay']['arrays']['actions'].shape[1], 51, 2026102638)","replay = violation_replay_class(replay_class(Replay), vb)(ck['replay']['arrays']['actions'].shape[1], 52, 2026102638)")
s=once(s,'learner = history_class(pair_class(PublishedLearner, reduction), binding)(root','learner = violation_class(history_class(pair_class(PublishedLearner, reduction), binding), vb)(root')
s=once(s,"    if check_only:\n        assert digest(replay.state_dict()) == replay_digest\n        return", "    if check_only:\n        assert digest(replay.state_dict()) == replay_digest\n        assert digest(learner.state_dict()) == initial and sha(reg['checkpoint']) == reg['checkpoint_sha256']\n        return")
s=once(s,"    assert not (output/'EVALUATION.json').exists()", "    launch = json.loads((output.parent/'LAUNCH_AUTHORIZATION.json').read_text())\n    assert launch['parent_cycle'] == 90 and launch['registration_hashes'][reg['controller']] == sha(registration)\n    assert launch['episodes'] == 90 and launch['maximum_actions'] == 123750 and launch['optimizer_updates'] == 0\n    assert not (output/'EVALUATION.json').exists()")
save(p,'evaluate_violation90.py',s)
p=OLD/'check_updated_frozen.py';s=p.read_text().replace('partial88','partial90').replace('complete88','complete90').replace('updated88','updated90').replace('complete88','complete90').replace('evaluate_history88','evaluate_violation90').replace('validate_recovery(ck, protocol, 88)','validate_recovery(ck, protocol, 90)')
s=s.replace('from persisted_history_critic import feature, history_replay_class','from persisted_history_critic import feature\nfrom persisted_violation_critic import violation_replay_class, KEY as VK\nfrom evaluate_violation90 import validate_architecture')
s=s.replace('from history_consumers import restore_learner','from violation_consumers import restore_learner')
s=s.replace("binding = reg['history_binding']","binding = reg['violation_binding']")
s=s.replace("        rejected = False", "        validate_architecture(ck, protocol)\n        rejected = False")
s=s.replace("history_replay_class(replay_class(Replay), binding)(binding['action_dimension'], 51, 2026102638)","violation_replay_class(replay_class(Replay), binding)(binding['action_dimension'], 52, 2026102638)")
s=s.replace('[:,50].abs().max()', '[:,51].abs().max()').replace('_history_weight_absmax','_bit_weight_absmax').replace('_history_absmax','_bit_absmax')
s=s.replace('obs.shape == (51,)','obs.shape == (52,)')
s=once(s,'                    assert obs[50] == feature(peak)','                    assert obs[50] == feature(peak) and obs[51] == float(peak > .0002)')
s=once(s,"                assert term_obs[49] == 0 and term_obs[50] == feature(terminal['interval']['external_penetration_peak_m'])", "                assert term_obs[49] == 0 and term_obs[50] == feature(terminal['interval']['external_penetration_peak_m'])\n                assert term_obs[51] == float(terminal['interval']['external_penetration_peak_m'] > .0002)")
s=s.replace('learned_history=learned','learned_bit=learned').replace('terminal_history_exact=True','terminal_history_and_bit_exact=True').replace('Recorded inputs from87 with updated partial90 weights','Recorded inputs from89 with updated partial90 weights')
save(p,'check_updated_frozen.py',s)
p=OLD/'register_complete88.py';s=p.read_text().replace('register_complete88','register_complete90').replace('frozen88','frozen90').replace('complete88','complete90').replace('Complete88','Complete90').replace('parameter88_history_frozen_full30','parameter90_violation_frozen_full30').replace('parameter_history_cycle88','parameter_violation_cycle90').replace('20261030_v2','20261030_v1').replace('cycle_00088','cycle_00090').replace('loss88.png','loss90.png').replace("==88","==90")
s=once(s,"assert loss['methods'][method]['rows']==41250 and loss['methods'][method]['all_finite']", "assert 0<loss['methods'][method]['rows']<=41250 and loss['methods'][method]['rows']==review['methods'][method]['new_transitions'] and loss['methods'][method]['all_finite']")
s=once(s,"assert protocol['history_critic_amendment']['binding']==reg['history_binding']", "assert protocol['history_critic_amendment']['binding']==reg['history_binding']\n        assert protocol['violation_critic_amendment']['binding']==reg['violation_binding']")
save(p,'register_complete90.py',s)
print('Frozen90 evaluator and partial90 exact replay checker built; no launch')
