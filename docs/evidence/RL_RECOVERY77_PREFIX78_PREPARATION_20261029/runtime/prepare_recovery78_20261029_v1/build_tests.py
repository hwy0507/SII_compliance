from pathlib import Path
import ast,difflib
D=Path(__file__).parent;OLD=D.parent/'prepare_recovery77_20261029_v1'
s=(OLD/'test_contract.py').read_text();v=s.replace('77','__NEXT__').replace('76','77').replace('__NEXT__','78')
v=v.replace("recovery_driver=ref(B/'runtime/parameter75_interruption_recovery_20261029_v1/resume_partial75.py'))", "recovery_driver=ref(B/'runtime/parameter75_interruption_recovery_20261029_v1/resume_partial75.py'),previous_driver=ref(B/'runtime/prepare_recovery77_20261029_v1/resume_recovery76.py'))")
v=v.replace("'parent_registration','recovery_driver']", "'parent_registration','recovery_driver','previous_driver']")
v=v.replace("interruption_recovery=previous['interrupted_episode_recovery'])", "interruption_recovery=previous['interrupted_episode_recovery'],recovery_continuation=previous['post_interruption_continuation'])")
v=v.replace("('interruption_recovery',{})]", "('interruption_recovery',{}),('recovery_continuation',{})]")
needle=" results[method]=dict(protocol_positive_fixture=True"
insert=""" bad_previous=copy.deepcopy(previous);bad_previous['post_interruption_continuation']['new_cycles']=2
 changed=T/(method+'_invalid_historical_registration.json');write(changed,bad_previous)
 bad=copy.deepcopy(p);bad['post_interruption_continuation']['parent_registration']=ref(changed)
 try:mod.validate_protocol(sha(changed),bad,'')
 except ValueError:rejected.append('historical_continuation_chain')
 else:raise AssertionError('Changed historical continuation accepted')
"""
assert needle in v;v=v.replace(needle,insert+needle)
v=v.replace('per method17 protocol +7 boundary negatives','per method19 protocol +8 boundary negatives')
ast.parse(v);(D/'test_contract.py').write_text(v);(D/'test_contract.py.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True))))
