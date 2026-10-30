"""Finite frozen-loss diagnostic; intercept original train before its first mutation."""
from pathlib import Path
import hashlib, json, os, sys, time, traceback
from types import SimpleNamespace
D = Path(__file__).parent
B = D.parents[1]
os.sched_setaffinity(0, {0})
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def put(p, x):
    with p.open('x') as f: json.dump(x, f, indent=2); f.write('\n')
class BeforeOptimizer(Exception): pass
def stop_before_optimizer(*args, **kwargs): raise BeforeOptimizer('Read-only stop before zero_grad/backward/step')
def forbid_mutation(*args, **kwargs): raise AssertionError('Unexpected optimizer/target update reached')
try:
    import numpy as np
    import torch
    torch.set_num_threads(1)
    plan = read(D/'PLAN.json')
    assert plan['batches'] == 512 and plan['batch_size'] == 65536 and plan['seed'] == 2026103080
    assert sha(__file__) == plan['audit_source_sha256']
    for ref in plan['inputs'].values(): assert sha(ref['path']) == ref['sha256']
    reg = read(plan['inputs']['registration']['path'])
    runtime = Path(reg['runtime'])
    helper = Path(plan['helper'])
    assert sha(runtime/'RUNTIME.json') == reg['runtime_sha256']
    for name, h in read(runtime/'SOURCE_HASHES.json').items(): assert sha(runtime/'source'/name) == h
    for name, h in reg['batch_size_stage']['dependency_hashes'].items(): assert sha(helper/name) == h
    sys.path[:0] = [str(helper), str(runtime/'source/tools')]
    from published_compliance_learner_20261025 import PublishedLearner
    from published_pair_reduction_learner_20261026 import pair_class
    from published_exact_pipeline_20261026 import cache_class
    from published_replay_device_cache_20261025 import DeviceReplayCache
    from validate_published_finite_check_20261025 import digest
    ck = torch.load(plan['inputs']['checkpoint']['path'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 80 and ck['boundary'] == 'complete_condition_cycle' and ck['controller'] == 'vmc'
    assert ck['replay']['size'] == 3321000 and ck['replay']['capacity'] == 4000000
    arrays = ck['replay']['arrays']
    assert int(arrays['dones'].sum()) == 2394
    state = ck['learner']
    assert state['terminal_loss_weight'] == 128 and state['target_pair_reduction']['target'] == 'mean'
    cls = pair_class(PublishedLearner, 'mean')
    wrapper = cls(runtime, dimension=7, direct=False, seed=plan['seed'], device='cuda:0',
                  algorithm='cheq', critic_layer_norm=True, numerical_amendments=True, critic_clock=True)
    wrapper.load_state_dict(state)
    learner = wrapper.learner
    def frozen_state():
        return dict(agent=learner.agent.state_dict(), actor_optimizer=learner.actor_optimizer.state_dict(),
            q_optimizer=learner.q_optimizer.state_dict(), alpha_optimizer=learner.a_optimizer.state_dict(),
            log_alpha=learner.log_alpha, alpha=learner.alpha, num_gradient_steps=learner.num_gradient_steps,
            parameters_updated=learner.parameters_updated, step_metrics=learner.step_metrics)
    before = digest(frozen_state())
    assert before == digest({k: state[k] for k in frozen_state()})
    replay_before = digest(ck['replay'])
    source = (runtime/'published_cheq/agents/rl/sac_ensemble.py').read_text()
    assert source.count('self.q_optimizer.zero_grad()') == 1
    assert source.index('q_loss = q_loss + loss') < source.index('self.q_optimizer.zero_grad()') < source.index('q_loss.backward()')
    train_code = learner.train.__func__.__code__
    learner.q_optimizer.zero_grad = stop_before_optimizer
    for optimizer in [learner.q_optimizer, learner.actor_optimizer, learner.a_optimizer]: optimizer.step = forbid_mutation
    learner.actor_optimizer.zero_grad = forbid_mutation
    learner.a_optimizer.zero_grad = forbid_mutation
    learner.update_target_networks = forbid_mutation
    class RecordingRNG:
        def __init__(self, seed): self.generator=np.random.default_rng(seed); self.calls=0; self.last=None
        def integers(self, *args, **kwargs):
            self.last=self.generator.integers(*args, **kwargs); self.calls+=1; return self.last
    sample_rng = RecordingRNG(plan['seed'])
    replay = SimpleNamespace(arrays=arrays, size=ck['replay']['size'], rng=sample_rng)
    cache = cache_class(DeviceReplayCache)(replay, 'cuda:0')
    np.random.seed(plan['seed']+1)
    torch.manual_seed(plan['seed']+2)
    from utils.data_utils import BernoulliMaskReplayBufferSamples
    indices_file = np.lib.format.open_memmap(D/'sample_indices.npy', mode='w+', dtype=np.int64, shape=(512,65536))
    rows=[]; max_loss=-1.; focus_saved=False; started=time.monotonic()
    focus_index=plan['focus_replay_index']; old_end=plan['complete79_replay_size']
    assert focus_index == 3318758 and old_end == 3279750
    put(D/'STARTUP_REVIEW.json', dict(passed=True, time=time.time(), full_frozen_state_exact=True,
        replay_digest=replay_before, learner_digest=before, replay_rows=replay.size,
        objective_receipt=wrapper.pair_reduction_receipt, device='cuda:0', cpu_affinity=sorted(os.sched_getaffinity(0)),
        optimizer_intercept='before first q_optimizer.zero_grad; all optimizer.step and target updates forbidden',
        independent_diagnostic_rng=True, original_checkpoint_rng_and_files_unchanged=True))
    for number in range(512):
        sample=cache.sample(65536); indices=sample_rng.last.copy(); indices_file[number]=indices
        batch=BernoulliMaskReplayBufferSamples(**{k:v.unsqueeze(0) for k,v in sample.items()})
        caught=None
        try:
            with torch.no_grad(): learner.train(batch)
        except BeforeOptimizer as e:
            tb=e.__traceback__
            while tb is not None:
                if tb.tb_frame.f_code is train_code: caught=tb.tb_frame.f_locals.copy(); break
                tb=tb.tb_next
        assert caught is not None and set(['q_loss','q_losses','q_a_values','next_q_value','indices','data']) <= caught.keys()
        q=torch.stack(caught['q_a_values']).detach().cpu().numpy()
        target=caught['next_q_value'].detach().cpu().numpy()
        masks=sample['masks'].detach().cpu().numpy().T
        dones=sample['dones'].detach().cpu().numpy().reshape(-1)
        reward=sample['rewards'].detach().cpu().numpy().reshape(-1)
        assert np.array_equal(target[dones==1], reward[dones==1])
        assert np.isfinite(q).all() and np.isfinite(target).all()
        weights=masks.astype(np.float64)*(1+127*dones.astype(np.float64))[None,:]
        squared=(q.astype(np.float64)-target.astype(np.float64)[None,:])**2
        den=weights.sum(axis=1); numerator=(squared*weights).sum(axis=1)
        independent=numerator/den
        native=np.asarray([float(v.detach().cpu()) for v in caught['q_losses']])
        assert np.allclose(independent,native,rtol=2e-5,atol=2e-6), (number,independent,native)
        native_total=float(caught['q_loss'].detach().cpu()); scalar_total=float(independent.sum())
        assert np.isclose(native_total,scalar_total,rtol=2e-5,atol=2e-6)
        def contribution(mask): return float(((squared[:,mask]*weights[:,mask]).sum(axis=1)/den).sum())
        term=dones==1; new=term & (indices>=old_end); focus=indices==focus_index
        terminal=contribution(term); nonterminal=contribution(~term)
        assert np.isclose(terminal+nonterminal,scalar_total,rtol=1e-12,atol=1e-12)
        row=dict(batch=number,native_loss=native_total,scalar_loss=scalar_total,terminal_contribution=terminal,
            nonterminal_contribution=nonterminal,new30_contribution=contribution(new),focus_contribution=contribution(focus),
            terminal_draws=int(term.sum()),new30_draws=int(new.sum()),focus_draws=int(focus.sum()),
            target_pair=caught['indices'].tolist(),denominators=den.tolist(),numerators=numerator.tolist(),
            native_per_critic=native.tolist(),max_absolute_td=float(np.abs(q-target[None,:]).max()),
            sample_indices_sha256=hashlib.sha256(indices.tobytes()).hexdigest())
        rows.append(row)
        with (D/'BATCHES.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
        evidence=dict(indices=indices,q=q,target=target,masks=masks,dones=dones,rewards=reward,batch=np.asarray(number))
        if number==0: np.savez_compressed(D/'first_batch.npz',**evidence)
        if native_total>max_loss:
            max_loss=native_total; np.savez_compressed(D/'maximum_batch.npz',**evidence)
        if focus.any() and not focus_saved:
            np.savez_compressed(D/'first_focus_batch.npz',**evidence);focus_saved=True
        if number==0:
            assert digest(frozen_state())==before
            assert all(p.grad is None for p in learner.agent.parameters())
        if number%32==0:
            (D/'PROGRESS.json').write_text(json.dumps(dict(time=time.time(),batches_completed=number+1,elapsed=time.monotonic()-started))+'\n')
            print(json.dumps(dict(batch=number+1,loss=native_total,terminal=terminal,focus_draws=int(focus.sum()),elapsed=time.monotonic()-started)),flush=True)
        del caught,batch,sample,q,target,masks,weights,squared,evidence
    indices_file.flush();del indices_file
    assert digest(frozen_state())==before and digest(ck['replay'])==replay_before
    assert all(p.grad is None for p in learner.agent.parameters())
    for ref in plan['inputs'].values(): assert sha(ref['path'])==ref['sha256']
    losses=np.asarray([r['native_loss'] for r in rows]);focus=np.asarray([r['focus_draws']>0 for r in rows])
    def stats(v): return dict(count=len(v),mean=float(v.mean()),minimum=float(v.min()),maximum=float(v.max()),quantiles=np.quantile(v,[.5,.9,.95,.99]).tolist()) if len(v) else dict(count=0)
    result=dict(passed=True,time=time.time(),batches=512,batch_size=65536,total_diagnostic_draws=512*65536,
        loss=stats(losses),focus_present_loss=stats(losses[focus]),focus_absent_loss=stats(losses[~focus]),
        mean_terminal_contribution=float(np.mean([r['terminal_contribution'] for r in rows])),
        mean_nonterminal_contribution=float(np.mean([r['nonterminal_contribution'] for r in rows])),
        mean_new30_contribution=float(np.mean([r['new30_contribution'] for r in rows])),
        focus_batches=int(focus.sum()),focus_draws=sum(r['focus_draws'] for r in rows),
        expected_focus_draws=512*65536/replay.size,accepted_sampling_rng_calls=sample_rng.calls,
        frozen_state_and_replay_unchanged=True,no_gradients=True,new_physics=0,optimizer_updates=0,
        checkpoint_sha256=plan['inputs']['checkpoint']['sha256'],sample_indices_sha256=sha(D/'sample_indices.npy'),
        batches_sha256=sha(D/'BATCHES.jsonl'),original_train_function_used=True,
        all512_native_loss_vs_float64_scalar_reduction_verified=True,convergence_claim=False,causal_claim=False,
        limitation=plan['limitation'])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    axes[0].plot(losses,label='Frozen total loss',lw=.8)
    axes[0].plot([r['terminal_contribution'] for r in rows],label='Terminal contribution',lw=.7)
    axes[0].scatter(np.flatnonzero(focus),losses[focus],s=16,color='red',label='short0600 sampled')
    axes[0].set(xlabel='Diagnostic batch',ylabel='Original weighted critic loss');axes[0].legend(fontsize=8)
    axes[1].hist(losses,bins=40);axes[1].set(xlabel='Frozen total loss',ylabel='Batch count')
    fig.suptitle('VMC complete80: 512 frozen diagnostic batches; no optimizer updates')
    fig.savefig(D/'frozen_loss.png',dpi=140);plt.close(fig);result['plot_sha256']=sha(D/'frozen_loss.png')
    put(D/'REVIEW.json',result);put(D/'FINISHED.json',dict(passed=True,time=time.time(),batches=512,new_physics=0,optimizer_updates=0))
    print(json.dumps(result),flush=True)
except BaseException as e:
    put(D/'FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()))
    raise
