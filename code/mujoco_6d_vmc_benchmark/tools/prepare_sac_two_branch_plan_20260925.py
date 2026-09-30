"""DGX no-physics preflight and concrete two-branch SAC plan; never launch jobs."""
from __future__ import annotations
import argparse
import gc
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import traceback
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
SOURCE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(SOURCE/'scripts'),str(SOURCE/'tools')]
import run_canonical48_sac_20260925 as entry
from canonical48_sac_audit_20260925 import AuditedReplayBuffer,prefill,stats,require

def source_files():
    return {str(p.relative_to(SOURCE)):entry.sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def implementation_hashes():
    return {name:entry.sha(Path(inspect.getfile(cls))) for name,cls in
        [('SAC',entry.sb3.SAC),('SACPolicy',entry.SACPolicy),('OffPolicyAlgorithm',entry.OffPolicyAlgorithm),
         ('ReplayBuffer',entry.ReplayBuffer),('VecNormalize',entry.VecNormalize)]}

def fingerprint(model):
    values={name:tensor.detach().cpu().numpy() for name,tensor in model.policy.state_dict().items()}
    values['log_ent_coef']=model.log_ent_coef.detach().cpu().numpy()
    return {name:dict(shape=list(array.shape),dtype=str(array.dtype),sha256=hashlib.sha256(array.tobytes()).hexdigest())
        for name,array in sorted(values.items())}

def rng_state():
    state=entry.np.random.get_state()
    return dict(numpy=[state[0],state[1].tolist(),*state[2:]],torch=entry.torch.random.get_rng_state().tolist(),
        cuda=[value.tolist() for value in entry.torch.cuda.get_rng_state_all()])

def initial_probe(root,data):
    """Only spaces: reset/step both raise, and learn/train are never invoked."""
    evidence={}
    for branch,count in (('online_only',0),('demo_prefill',600)):
        normalizer=entry.VecNormalize(entry.DummyVecEnv([entry.demo_protocol.NoSimulationEnv]),
            norm_obs=True,norm_reward=False,clip_obs=12.)
        model=None
        try:
            model=entry.sb3.SAC('MlpPolicy',normalizer,**entry.hyperparameters(),device='cuda',
                replay_buffer_class=AuditedReplayBuffer,
                replay_buffer_kwargs=dict(audit_directory=root/'preflight'/branch,expected_demo=count,handle_timeout_termination=True),verbose=0)
            before=fingerprint(model);before_stats=stats(normalizer);before_rng=rng_state()
            require(model.num_timesteps==model._n_updates==0,'Probe unexpectedly trained')
            if count:
                model.replay_buffer.start_audit();prefill(model.replay_buffer,data)
            require(fingerprint(model)==before and stats(normalizer)==before_stats,'Demo changed initial model or RMS')
            require(rng_state()==before_rng,'Demo insertion changed RNG state')
            require(model.replay_buffer.size()==count and model.replay_buffer.online_steps==0 and model.replay_buffer.sample_calls==0,'Unexpected preflight data/update budget')
            evidence[branch]=dict(initial_policy=before,initial_normalization=before_stats,
                demo_transitions=count,online_steps=0,gradient_updates=0,initial_alpha=float(model.log_ent_coef.exp().detach().cpu()),
                target_entropy=model.target_entropy,prefill_model_rms_rng_unchanged=True)
        finally:
            if model is not None:model.replay_buffer.close_logs()
            normalizer.close();del model;gc.collect();entry.torch.cuda.empty_cache()
    require(evidence['online_only']['initial_policy']==evidence['demo_prefill']['initial_policy'],'Two branches did not start with exact same network/alpha')
    require(evidence['online_only']['initial_normalization']==evidence['demo_prefill']['initial_normalization'],'Two branches did not start with same RMS')
    return dict(passed=True,simulator_steps=0,gradient_updates=0,branches=evidence,initial_pair_exact=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','assets','menagerie','proof-root'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    for name in ('root','assets','menagerie','proof_root'):setattr(args,name,getattr(args,name).resolve())
    root=args.root
    require(root==SOURCE.parent,'Plan must belong to this isolated snapshot')
    for name in ('training','PLAN.json','PREFLIGHT.json','PREFLIGHT_FAILED.json','preflight'):
        require(not (root/name).exists(),'Fresh preflight/output required: '+name)
    (root/'preflight').mkdir()
    try:
        entry.torch.set_num_threads(1);entry.torch.set_num_interop_threads(1)
        entry.resource_check();require(entry.torch.cuda.is_available(),'DGX CUDA required')
        entry.torch.cuda.set_per_process_memory_fraction(.15)
        require(len(os.sched_getaffinity(0))>6,'CPU5/6 unavailable')
        build=json.loads((root/'BUILD.json').read_text())
        sources=source_files();require(sources==build['source_sha256'],'Uploaded source drift')
        require(all(not ((SOURCE/name).stat().st_mode&0o222) for name in sources),'Source is not readonly')
        implementations=implementation_hashes()
        require(implementations==build['reviewed_sb3_source_sha256'],'DGX SB3 implementation differs from reviewed local bytes')
        specs,intersections=entry.load_fixture_specs(args.assets)
        nominal=json.loads(specs['train']['command']['environment']['CORE_VMC_CONFIG'])
        runtime=dict(python=sys.version,mujoco=entry.mujoco.__version__,numpy=entry.np.__version__,torch=entry.torch.__version__,
            sb3=entry.sb3.__version__,cuda_available=True,cuda_runtime=entry.torch.version.cuda,gpu=entry.torch.cuda.get_device_name())
        manifest=dict(source_hashes=entry.paired.source_hashes(),asset_hashes=entry.paired.asset_hashes(args.menagerie),
            fixture_specs=specs,nominal_options=nominal,runtime=runtime,device='cuda',reward=entry.reward_protocol(),
            base_protocol_sha256=entry.sha(SOURCE/'docs/RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md'))
        proofs=entry.verify_proofs(args.proof_root,manifest)
        data,demo=entry.read_demo(root/'demo')
        require(demo['manifest_sha256']==build['demo_manifest_sha256'],'Pinned demo mismatch')
        probe=initial_probe(root,data)
        require(source_files()==sources and entry.paired.asset_hashes(args.menagerie)==manifest['asset_hashes'],'Probe changed source/assets')
        evidence=dict(passed=True,simulator_steps=0,gradient_updates=0,source_sha256=sources,
            sb3_source_sha256=implementations,manifest=manifest,proof_sha256=proofs,demo=demo,
            initial_probe=probe,split_intersections=intersections,protocol_sha256=entry.sha(SOURCE/'docs/CANONICAL48_SAC_DIRECT7_PROPOSAL_20260925.md'))
        entry.save_json(root/'PREFLIGHT.json',evidence)
        jobs=[]
        for branch,cpu in (('online_only',5),('demo_prefill',6)):
            output=root/'training'/branch
            command=['/usr/bin/timeout','--signal=TERM','--kill-after=15s','7200s',sys.executable,'-u',
                str(SOURCE/'tools/run_canonical48_sac_20260925.py'),'--branch',branch,'--output',str(output),
                '--assets',str(args.assets),'--menagerie',str(args.menagerie),'--proof-root',str(args.proof_root),'--cpu-offset',str(cpu)]
            if branch=='demo_prefill':command.extend(['--demo',str(root/'demo')])
            jobs.append(dict(branch=branch,seed=20260923,online_steps=8192,demo_transitions=600 if branch=='demo_prefill' else 0,
                expected_updates=8092,output=str(output),command=command,cpu_offset=cpu,threads=1,device='cuda',timeout_s=7200,
                log=str(root/(branch+'.log')),environment=dict(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',MUJOCO_GL='egl')))
        plan=dict(status='prepared_not_started',simulations_started=0,gradient_updates=0,jobs=jobs,max_workers=2,global_worker_cap=4,
            source_sha256=sources,sb3_source_sha256=implementations,asset_hashes=manifest['asset_hashes'],proof_sha256=proofs,demo=demo,
            build_sha256=entry.sha(root/'BUILD.json'),preflight_sha256=entry.sha(root/'PREFLIGHT.json'),protocol_sha256=evidence['protocol_sha256'],
            launch_requires_root_review_and_fresh_resource_check=True,resource_guard=dict(max_rss_gib=7,min_available_gib=2.5),
            checkpoint_rule='Fixed final8192 after8092 actual updates; intermediates diagnostic only',
            initial_acceptance='Each actual sac_initial policy/alpha and vecnormalize_initial RMS must match preflight fingerprints and each other; prefill must not alter model/RMS/RNG',
            final_acceptance='Each branch reloads final seed/8192/8092, actual actor/critic/entropy steps8092; own final RMS frozen across four evals. Final models/RMS need not equal across branches.',
            full_training_evidence='Original8192 journals, actual post-add replay and SB3 rewards, terminal masks, partial next, all four evals and failures retained',
            no_new_algorithm_claim='Standard SAC plus uniform demo prefill, not RLPD; online8192 vs total8792 data distinguished')
        with (root/'PLAN.json').open('x') as stream:json.dump(plan,stream,indent=2,allow_nan=False)
        print(json.dumps(dict(passed=True,simulator_steps=0,gradient_updates=0,jobs=2,plan_sha256=entry.sha(root/'PLAN.json'))))
    except BaseException as error:
        entry.save_json(root/'PREFLIGHT_FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),simulator_steps=0,gradient_updates=0))
        raise

if __name__=='__main__':main()
