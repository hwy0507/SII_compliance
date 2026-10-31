from pathlib import Path
import sys,json
B=Path(__file__).resolve().parents[2];S=B/'runtime/census100_continuation_20261031_v1'
def verify_science(p,previous):
 # All scientific fields including historical capacity stages are inherited verbatim.
 assert {k:v for k,v in p.items() if k!='post_interruption_continuation'}=={k:v for k,v in previous.items() if k!='post_interruption_continuation'}
 sys.path.insert(0,str(S))
 from driver import expected_protocol
 m=p['post_interruption_continuation']['controller'];assert p==expected_protocol(m)
 cap=p['replay_capacity_third_stage'];assert cap==previous['replay_capacity_third_stage']
 assert cap['parent_cycle']==96 and cap['first_cycle']==97 and cap['marker']['capacity']==6000000 and cap['marker']['previous_capacity']==4000000 and cap['old_rows_preserved']
 assert cap['entry_checkpoint']!=p['post_interruption_continuation']['checkpoint']
 return True
