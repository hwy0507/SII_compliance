from pathlib import Path
import ast,hashlib,json,re,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
rt=B/'runtime';src=rt/'serl_capacity24_monitor_templates_20261027_v1';dst=rt/'serl_capacity25_monitor_templates_20261027_v1';dst.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Change current-cycle paths only. Historical entry23 remains immutable.
for name in ['startup_review.py','review.py','coordinator.py','diagnose.py']:
 s=(src/name).read_text()
 s=s.replace('cycle24','cycle25').replace('cycle_00024','cycle_00025').replace('Cycle24','Cycle25').replace("['cycle']==24","['cycle']==25").replace("t['cycle']==24","t['cycle']==25").replace("e['cycle']==24","e['cycle']==25")
 if name=='diagnose.py':s=s.replace('==750','==780').replace('terminal_count=750','terminal_count=780')
 if name in ['startup_review.py','review.py']:
  indent=' ' if name=='startup_review.py' else '    '
  start=s.index(indent+"assert old['cycle']==23")
  end=s.index(indent+'capacity_review=dict',start)
  block='''assert old['cycle']==24 and old['boundary']=='complete_condition_cycle'
assert old['replay']['capacity']==2_000_000 and old['replay']['size']==old['replay']['cursor']==old['steps']
assert old['replay']['replay_capacity_extension']==CAPACITY_MARKER
parent_ref=reg['resume_parent_registration'];parent_reg_path=Path(parent_ref['path'])
assert sha(parent_reg_path)==parent_ref['sha256']==old['protocol_sha256']
parent_reg=json.loads(parent_reg_path.read_text())
assert reg['replay_capacity_stage']==parent_reg['replay_capacity_stage']
assert reg['replay_capacity_stage']['parent_cycle']==23
assert reg['reviewed_continuation_stage']['parent_cycle']==24
assert reg['reviewed_continuation_stage']['checkpoint']==dict(path=str(parent),sha256=sha(parent))
entry=reg['replay_capacity_stage']['entry_checkpoint'];assert sha(entry['path'])==entry['sha256']
'''
  s=s[:start]+''.join(indent+line+'\n' for line in block.splitlines())+s[end:]
  s=s.replace('capacity_review=dict(passed=True,old_capacity=1_000_000','capacity_review=dict(passed=True,historical_entry_cycle=23,inherited_stage_exact=True,old_capacity=2_000_000')
 ast.parse(s);(dst/name).write_text(s)
manifest=dict(time=time.time(),parent_templates=str(src),scope='Future finite25 inherited2m monitoring, no boundary rerun; not executed',templates={p.name:sha(p) for p in dst.glob('*.py')})
(dst/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
s=(rt/'setup_serl_capacity24_monitors_20261027.py').read_text().replace('capacity24','capacity25').replace('cycle24','cycle25')
s=s.replace("for name in ['startup_review.py','capacity_boundary_review.py']:","for name in ['startup_review.py']:")
s='\n'.join(line for line in s.splitlines() if "monitors['boundary']=" not in line)+'\n'
ast.parse(s);(rt/'setup_serl_capacity25_monitors_20261027.py').write_text(s)
s=(rt/'launch_serl_capacity24_20261027.py').read_text().replace('capacity24','capacity25').replace('cycle24','cycle25').replace('serl_multistep_batch65536_cycle23_review_20261026_v1','serl_capacity_batch65536_cycle24_review_20261027_v1')
s=s.replace("assert not (out/'LAUNCH.json').exists() and not Path('/proc/257351').exists()", "parent_launch=json.loads((B/'runs/serl_capacity_batch65536_cycle24_20261027_v1/LAUNCH.json').read_text())\nassert not (out/'LAUNCH.json').exists() and not Path(f\"/proc/{parent_launch['pid']}\").exists()")
ast.parse(s);(rt/'launch_serl_capacity25_20261027.py').write_text(s)
s=(rt/'prepare_serl_capacity24_20261027.py').read_text()
# Simultaneous exact path substitutions prevent accidental cascading.
replacements={
 'serl_multistep_batch65536_cycle23_20261026_v1':'serl_capacity_batch65536_cycle24_20261027_v1',
 'serl_capacity_batch65536_cycle24_20261027_v1':'serl_capacity_batch65536_cycle25_20261027_v1',
 'serl_multistep_batch65536_cycle23_review_20261026_v1':'serl_capacity_batch65536_cycle24_review_20261027_v1',
 'serl_multistep_batch65536_cycle23_archive_20261026_v1/direct/cycle_00023.pt':'serl_capacity_batch65536_cycle24_archive_20261027_v1/direct/cycle_00024.pt',
 'full23':'full24',"stage['parent_cycle']=23":"stage['parent_cycle']=24"}
s=re.sub('|'.join(re.escape(k) for k in replacements),lambda m:replacements[m.group()],s)
s=s.replace("assert not Path('/proc/257351').exists(), 'Original23 learner must exit before reusing CPU0'", "parent_launch=read(B/'runs'/oldname/'LAUNCH.json')\nassert not Path(f\"/proc/{parent_launch['pid']}\").exists(), 'Original24 learner must exit before reusing CPU0'")
start=s.index('import sys,torch');end=s.index("p['gather_stage']['source_hashes'][helper]",start)
s=s[:start]+'''import sys,torch
sys.path.insert(0,str(RT))
from serl_replay_capacity_20261027 import MARKER
x=torch.load(cp,map_location='cpu',weights_only=False)
assert x['cycle']==24 and x['boundary']=='complete_condition_cycle'
assert x['steps']==x['replay']['size']==x['replay']['cursor']
assert x['steps']+41250<=2_000_000
assert x['replay']['capacity']==2_000_000 and x['replay']['replay_capacity_extension']==MARKER
assert x['protocol_sha256']==sha(parent)
assert p['replay_capacity_stage']==read(parent)['replay_capacity_stage']
assert p['replay_capacity_stage']['parent_cycle']==23 and p['replay_capacity_stage']['marker']==MARKER
assert p['replay_capacity_stage']['helper_sha256']==sha(RT/helper)
preparation=Path(p['replay_capacity_stage']['driver_preparation_review']['path'])
assert sha(preparation)==p['replay_capacity_stage']['driver_preparation_review']['sha256']
d=read(preparation);assert d['passed'] and d['driver_sha256']==sha(RT/driver)
assert d['helper_sha256']==sha(RT/helper)
# Keep historical entry23 checkpoint/digest and validation evidence unchanged.
''' +s[end:]
start=s.index("stage['decision']=");end=s.index('\ndel x',start)
s=s[:start]+"stage['decision']='One finite cycle25 from exact complete24; inherit2m replay, historical entry23 and all learner/optimizer/targets/physics/reward. No auxiliary weights or convergence claim.'"+s[end:]
ast.parse(s);(rt/'prepare_serl_capacity25_20261027.py').write_text(s)
print(dst)
