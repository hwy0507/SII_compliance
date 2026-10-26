from pathlib import Path
import json,hashlib,shutil,subprocess,os,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
gate=B/'runs/serl_cycle14_temperature_successor_gate_20261026_v2';g=json.loads((gate/'REVIEW.json').read_text());assert g['passed']
assert not Path('/proc/841719').exists()
c=g['default_numerical_comparison'];assert c['max_abs']==2.9802322387695312e-08 and c['nonfloat_counter_rng_exact'] and c['all_close_1e6_1e7']
changed=[v for v in c['leaves'] if not v['exact']];assert len(changed)==3
assert all('modules_actor/Dense_1/kernel' in v['path'] for v in changed)
assert g['default_metrics_comparison']['exact'] and g['native_alias_high_precision_formula_check']
for k in ['critic','actor']:assert g['isolation'][k]['full_state_and_metrics_exact']
assert g['isolation']['temperature']['only_temperature_params_and_optimizer_differ']
write(gate/'FINAL_SCIENTIFIC_REVIEW.json',dict(time=time.time(),implementation_gate=ref(gate/'REVIEW.json'),permit_finite_offline_probe=True,permit_formal_deployment=False,reviewed_default_max_abs=c['max_abs'],native_alias_bitwise_equal=False,changed_leaves=changed,reason='Default differences confined to one actor kernel and its Adam moments, max2.98e-8; metrics and nonfloat/counter/RNG exact. Highest-precision formula check and exact default critic/actor isolation pass. Both finite probe arms use the same wrapper and default precision, identical full formal14 state and row draws; only temperature successor differs. Preserve failed v1; this is numerical boundedness, not bitwise equivalence or deployment approval.'))
name='serl_cycle14_temperature_successor_probe_20261026_v1';out=B/'runs'/name;rt=B/'runtime'/name;out.mkdir();rt.mkdir()
reg=json.loads((gate/'REGISTRATION.json').read_text())
reg={k:reg[k] for k in ['checkpoint','cycle_review','health_review','training_registration','adapter_runtime','upstream','upstream_manifest','sources']}
for key in list(reg['sources']):
 if '/' not in key:del reg['sources'][key]
for name in ['probe_serl_temperature_successor_20261026.py','serl_temperature_state_candidate_20261026.py']:
 shutil.copyfile(R/'code/mujoco_6d_vmc_benchmark/tools'/name,rt/name);reg['sources'][name]=ref(rt/name)
assert reg['sources']['serl_temperature_state_candidate_20261026.py']['sha256']==json.loads((gate/'REGISTRATION.json').read_text())['sources']['serl_temperature_state_candidate_20261026.py']['sha256']
reg.update(time=time.time(),implementation_gate=ref(gate/'REVIEW.json'),gate_decision=ref(gate/'FINAL_SCIENTIFIC_REVIEW.json'),arms=['derived_next32','raw_next1'],outer_updates_per_arm=2000,batch_size=65536,record_every=200,seed=2026102619,new_physics=0,weights_saved=False,formal_deployment=False)
write(out/'REGISTRATION.json',reg)
cmd=[str(B/'serl_env/bin/python'),str(rt/'probe_serl_temperature_successor_20261026.py'),'--registration',str(out/'REGISTRATION.json'),'--output',str(out)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
with (out/'probe.log').open('x') as f:p=subprocess.Popen(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
write(out/'LAUNCH.json',dict(pid=p.pid,time=time.time(),command=cmd));print(p.pid)
