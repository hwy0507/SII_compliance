"""Versioned full-mask conditional terminal expectation; no online dispatcher.

The sampler and all actor/target/temperature code are retained exactly. Finite
Adam trajectories differ. Native sampled loss is reported separately.
"""
from pathlib import Path
import ast, copy, hashlib, inspect, marshal, textwrap, types
import numpy as np
import torch
from published_exact_pipeline_20261026 import cache_class
from published_replay_device_cache_20261025 import DeviceReplayCache

KEY = 'conditional_terminal_census'
RULE = dict(version=1, strata='complete_binary_five_critic_mask', terminal_weight=128,
            denominator='original_sampled_weighted_mask_sum', nonterminal='original_sampled_td',
            population='all_current_retained_terminals', sampling='unchanged_uniform_rejection',
            statistic='mean_squared_residual_not_squared_mean', actor_target_temperature='unchanged')

def marker():
    return dict(RULE, implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

def binary(x):
    return bool(np.all((x == 0) | (x == 1)))

class CensusCache(cache_class(DeviceReplayCache)):
    def __init__(self, replay, device):
        self.scanned = 0
        self.terminal_indices = np.empty(0, dtype=np.int64)
        self.scanned_rows_total = 0
        self._array_ids = {k:id(v) for k,v in replay.arrays.items()}
        super().__init__(replay, device)

    def sync_terminals(self):
        r = self.replay
        if r.cursor != r.size or not self.scanned <= r.size <= r.capacity:
            raise ValueError('Terminal cache requires append-only untruncated replay')
        if self._array_ids != {k:id(v) for k,v in r.arrays.items()}:
            raise ValueError('Replay storage replaced without explicit cache rebuild')
        if self.scanned == r.size and hasattr(self, 'terminal'):
            return
        lo, hi = self.scanned, r.size
        done = r.arrays['dones'][lo:hi]
        masks = r.arrays['masks'][lo:hi]
        if done.shape != (hi-lo,1) or masks.shape != (hi-lo,5) or not binary(done) or not binary(masks):
            raise ValueError('Binary done and five-critic mask rows required')
        new = np.flatnonzero(done[:,0] == 1) + lo
        if len(new)==0 and hasattr(self, 'terminal'):
            self.scanned_rows_total += hi-lo
            self.scanned = hi
            return
        indices = np.concatenate((self.terminal_indices, new))
        di = torch.as_tensor(indices, device=self.device)
        terminal = {k:torch.index_select(self.arrays[k],0,di) for k in ('observations','actions','rewards','masks')}
        codes = (terminal['masks'].long()*torch.tensor([1,2,4,8,16],device=self.device)).sum(1)
        self.terminal, self.codes = terminal, codes
        self.population = torch.bincount(codes,minlength=32)
        self.terminal_indices = indices
        self.scanned_rows_total += hi-lo
        self.scanned = hi

    def refresh(self):
        # Original exact cache validates masks and refreshes the device mirror.
        # Terminal discovery scans only newly appended rows.
        r = self.replay
        if r.cursor != r.size or r.size < self.scanned:
            raise ValueError('Cannot refresh a truncated or wrapped replay')
        if self._array_ids != {k:id(v) for k,v in r.arrays.items()}:
            raise ValueError('Explicit rebuild required after storage replacement')
        if not binary(r.arrays['dones'][self.scanned:r.size]):
            raise ValueError('Invalid appended dones')
        super().refresh()
        self.sync_terminals()

    def add(self, **row):
        # Validate before the authoritative add consumes RNG or changes storage.
        if not binary(np.asarray(row['dones'])):
            raise ValueError('Invalid appended done')
        super().add(**row)
        self.sync_terminals()

    def load_state_dict(self, state):
        # A load may replace rows at the same size: always rebuild the derived cache.
        if not binary(state['arrays']['dones']):
            raise ValueError('Invalid restored dones')
        self.replay.load_state_dict(state)
        self.scanned = 0
        self.terminal_indices = np.empty(0,dtype=np.int64)
        self._array_ids = {k:id(v) for k,v in self.replay.arrays.items()}
        self.refresh()


def native_source(wrapper):
    from published_terminal_loss_weight_20261026 import install as terminal_install
    source=(Path(wrapper.runtime)/'published_cheq/agents/rl/sac_ensemble.py').read_text()
    cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='SACEnsemble')
    n=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='train')
    base=textwrap.dedent(''.join(source.splitlines(keepends=True)[n.lineno-1:n.end_lineno]))
    base=base.replace('min_q_pi = torch.min(q1_pi, q2_pi).view(-1)','min_q_pi = torch.min(q1_pi, q2_pi).view(-1, 1)')
    if hashlib.sha256(base.encode()).hexdigest()!=wrapper.numerical_patch_receipt['ensemble_sac']['replacement_sha256']:
        raise ValueError('Numerical source drift')
    tree=ast.parse(textwrap.dedent(inspect.getsource(terminal_install)))
    strings={x.targets[0].id:x.value.value for x in ast.walk(tree) if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name) and isinstance(x.value,ast.Constant) and isinstance(x.value.value,str)}
    if base.count(strings['old'])!=1:raise ValueError('Terminal seam drift')
    base=base.replace(strings['old'],strings['new'])
    old='min_q_next_target = torch.min(q1_next_target, q2_next_target) - self.alpha * next_state_log_pi'
    new='min_q_next_target = _project_q(_reduce_pair(q1_next_target, q2_next_target, _mean_pair), data.next_observations, self.alpha, self.gamma, _log_volume, _projection_enabled) - self.alpha * next_state_log_pi'
    if base.count(old)!=1:raise ValueError('Projection seam drift')
    base=base.replace(old,new)
    ns=dict(wrapper.learner.train.__func__.__globals__)
    exec(compile(base,'<registered_finite_target_projection>','exec'),ns)
    if marshal.dumps(ns['train'].__code__)!=marshal.dumps(wrapper.learner.train.__func__.__code__):
        raise ValueError('Reconstructed native train code differs')
    return base


def losses(learner, data, q_values, target, cache):
    cache.sync_terminals()
    if cache.device != learner.device or len(q_values)!=5:
        raise ValueError('Census cache device/ensemble mismatch')
    done=data.dones.flatten();masks=data.masks
    if not torch.all((done==0)|(done==1)) or not torch.all((masks==0)|(masks==1)):
        raise ValueError('Invalid sampled dones or masks')
    codes=(masks.long()*torch.tensor([1,2,4,8,16],device=done.device)).sum(1)
    counts=torch.bincount(codes[done==1],minlength=32)
    if torch.any((counts>0)&(cache.population==0)):
        raise ValueError('Sampled terminal stratum absent from population')
    rates=counts.to(torch.float64)/cache.population.clamp_min(1).to(torch.float64)
    terminal=cache.terminal
    original=[];candidate=[]
    for j in range(5):
        err=(q_values[j]-target)**2
        weight=masks[:,j]*(1+127*done);den=weight.sum()
        if not bool(den>0):raise ValueError('Empty accepted critic mask')
        original.append((err.detach()*weight).sum()/den)
        q=learner.agent.get_q_value(state=terminal['observations'],action=terminal['actions'],q_net=j,target=False).view(-1)
        # Cast the fully normalized float64 weights once, as in the reviewed ablation.
        w=(128*rates[cache.codes]*terminal['masks'][:,j].double()/den.double()).float()
        candidate.append((err*masks[:,j]*(1-done)).sum()/den+((q-terminal['rewards'].flatten())**2*w).sum())
    cache.last_diagnostics=dict(original_sampled_q_loss=float(sum(original)),
                               conditional_terminal_q_loss=float(sum(x.detach() for x in candidate)),
                               terminal_population=len(cache.terminal_indices), sampled_terminal_rows=int(done.sum()))
    return candidate


def install(wrapper, cache, helper=losses):
    base=native_source(wrapper)
    line=next(line for line in base.splitlines() if line.lstrip().startswith('q_losses = '))
    replacement=line[:len(line)-len(line.lstrip())]+'q_losses = _census_losses(self, data, q_a_values, next_q_value, _census_cache)'
    candidate=base.replace(line,replacement)
    ns=dict(wrapper.learner.train.__func__.__globals__,_census_losses=helper,_census_cache=cache)
    exec(compile(candidate,'<registered_conditional_terminal_census>','exec'),ns)
    wrapper.learner.train=types.MethodType(ns['train'],wrapper.learner)
    return dict(native_code_exact=True,native_sha256=hashlib.sha256(base.encode()).hexdigest(),candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),changed_assignment='q_losses only')


def census_class(base):
    class CensusLearner(base):
        def __init__(self,*args,**kwargs):
            self.census_cache=None
            super().__init__(*args,**kwargs)
        def load_state_dict(self,state):
            if state.get(KEY)!=marker():raise ValueError('Exact persisted estimator marker required')
            plain=dict(state);plain.pop(KEY)
            super().load_state_dict(plain)
            self.census_cache=None
        def migrate_parent(self,state):
            if KEY in state:raise ValueError('Parent already has estimator marker')
            self.load_state_dict(dict(state,**{KEY:marker()}))
        def bind_cache(self,cache):
            if self.census_cache is not None:raise ValueError('Already bound; reload before rebinding')
            self.census_receipt=install(self,cache)
            self.census_cache=cache
        def update(self,arrays):
            if self.census_cache is None:raise ValueError('Restored census learner requires current replay binding')
            metrics=super().update(arrays)
            metrics.update({'agent_train/'+k:v for k,v in self.census_cache.last_diagnostics.items()})
            return metrics
        def state_dict(self):return dict(super().state_dict(),**{KEY:marker()})
    return CensusLearner


def strict_restore(learner,state,digest):
    if state.get(KEY)!=marker():raise ValueError('Estimator marker missing or changed')
    learner.load_state_dict(state)
    if digest(learner.state_dict())!=digest(state):
        raise ValueError('Restored learner dropped or changed persisted state')
