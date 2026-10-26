from pathlib import Path
import json,hashlib,math,time,os
os.sched_setaffinity(0,{53})
import numpy as np
import torch
torch.set_num_threads(1)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');p=B/'runs/serl_cycle14_temperature_states_20261026_v1'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
d=json.loads((p/'REVIEW.json').read_text());r=json.loads((p/'REGISTRATION.json').read_text());assert d['passed'] and json.loads((p/'FINISHED.json').read_text())['completed'];assert d['initial_state_digest']==d['final_state_digest'];assert d['full_network_optimizer_rng_unchanged'];assert d['optimizer_updates']==d['new_physics']==0
for k in ['checkpoint','actor_diagnostic_registration','actor_diagnostic_review','selected_rows','source']:assert sha(r[k]['path'])==r[k]['sha256']
x=torch.load(r['checkpoint']['path'],map_location='cpu',weights_only=False)
with np.load(r['selected_rows']['path']) as s:ids=s['uniform'].copy()
assert hashlib.sha256(ids.tobytes()).hexdigest()==d['row_ids_sha256']
a=x['replay']['arrays'];e=x['replay']['multistep_target_extension']['target_endpoints'][ids]
arrays=dict(current=a['observations'][ids],raw_next1=a['next_observations'][ids],derived_next32=a['next_observations'][e])
for k,obs in arrays.items():
 v=d['states'][k];assert hashlib.sha256(obs.tobytes()).hexdigest()==v['observation_sha256'];assert int(np.sum(obs[:,48]>=np.float32((1375-31)/1375)))==v['first32_states'];assert int(np.sum(obs[:,48]==1))==v['initial_states']
 loss=d['temperature']*(v['entropy']-d['target_entropy']);grad=(v['entropy']-d['target_entropy'])/(1+math.exp(-d['raw_softplus_parameter']))
 np.testing.assert_allclose(loss,v['official_temperature_loss'],rtol=2e-5,atol=2e-6);np.testing.assert_allclose(grad,v['raw_softplus_parameter_gradient'],rtol=2e-5,atol=2e-6)
 assert v['negative_gradient_direction']==('increase_temperature' if grad<0 else 'decrease_temperature')
keys=list(arrays);fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
axes[0].bar(keys,[d['states'][k]['entropy'] for k in keys]);axes[0].axhline(d['target_entropy'],color='red',linestyle='--',label='registered target -3.5');axes[0].set_ylabel('Sampled entropy');axes[0].legend();axes[0].set_title('Same8192 rows and action-noise key')
axes[1].bar(keys,[d['states'][k]['raw_softplus_parameter_gradient'] for k in keys]);axes[1].axhline(0,color='black',linewidth=.8);axes[1].set_ylabel('Official temperature-parameter gradient');axes[1].set_title('Negative gradient raises temperature; positive lowers it')
fig.suptitle('Frozen14, diagnostic highest FP32: no Adam update or task-effect claim');plot=p/'temperature_state_comparison.png';assert not plot.exists();fig.savefig(plot,dpi=160);plt.close(fig)
result=dict(time=time.time(),passed=True,report_sha256=sha(p/'REVIEW.json'),source_sha256=sha(__file__),plot_sha256=sha(plot),all_observation_hashes_and_coverage_recomputed=True,official_loss_and_softplus_gradient_arithmetic_checked=True,source_parent_hashes_verified=True,new_physics=0,optimizer_updates=0,scope='Independent saved-result arithmetic, source/parent hashes and exact8192 input-observation arrays; no neural entropy or gradient re-inference and no dynamics rerun.',convergence_claim=False)
(p/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
