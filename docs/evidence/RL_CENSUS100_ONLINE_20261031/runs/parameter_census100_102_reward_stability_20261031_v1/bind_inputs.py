"""Bind all nine actually completed cycles from an explicit input map; never launch training."""
from pathlib import Path
import argparse,json,os,time
from binding_rules import locked,ref,validate_registration
ROOT=Path(__file__).resolve().parent
def build(inputs):
 p=locked(ROOT)
 return dict(cycles=p['cycles'],seed=p['bootstrap_seed'],bootstrap_replicates=p['replicates'],near_zero_guard=p['near_zero_guard'],relative_limit=p['relative_limit'],source_sha256=p['source_sha256'],review_source_sha256=p['review_source_sha256'],followup_marker=p['followup_marker'],anchor_protocol55=p['anchor_protocol55'],history_amendment=p['history_amendment'],violation_amendment=p['violation_amendment'],conditional_amendment=p['conditional_amendment'],inputs=inputs,original_prospective_plan=p['intent'],original_failed_window=p['original_failed_report'],original_early_failure=p['original_early_failure'],binding_source=ref(ROOT/'bind_inputs.py'),automatic_training=False,third_capacity_stage=p['third_capacity_stage'],previous94_96_failed_report=p['previous94_96_failed_report'],previous97_99_failed_report=p['previous97_99_failed_report'])
if __name__=='__main__':
 os.sched_setaffinity(0,{54});parser=argparse.ArgumentParser();parser.add_argument('--input-map',type=Path,required=True);args=parser.parse_args();reg=build(json.loads(args.input_map.read_text()));validate_registration(ROOT,reg,check_checkpoints=True)
 with (ROOT/'REGISTRATION.json').open('x') as f:json.dump(reg,f,indent=2);f.write('\n')
 with (ROOT/'BINDING_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),all_nine_actual_checkpoints_checked=True,inputs=ref(args.input_map),registration=ref(ROOT/'REGISTRATION.json'),new_physics=0,optimizer_updates=0),f,indent=2);f.write('\n')
