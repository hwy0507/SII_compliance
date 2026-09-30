"""Independent action6/action7 wrapper with complete, durable transition logs.

The original simulator/Gym bridge is unchanged. A private copy of its episode
function differs only in enabling MJB archival. Parameter control always sees
raw float64 canonical48; VecNormalize is outside this wrapper.
"""
from __future__ import annotations
import copy
import inspect
import json
from pathlib import Path
import queue
import threading
import gymnasium as gym
import numpy as np
import canonical48_rl_env_20260923 as original
from canonical48_potential_reward_20260924 import environment_class,protocol as reward_protocol
from canonical48_vmc_tuning_20260924 import Canonical48VMCTuning


def make_archiving_runner():
    source=inspect.getsource(original.run_episode)
    old="SKIP_MODEL_ARCHIVE='1'"
    if source.count(old)!=1:raise RuntimeError('Original MJB archival hook changed')
    namespace=dict(vars(original))
    exec(compile(source.replace(old,"SKIP_MODEL_ARCHIVE='0'"),__file__,'exec'),namespace)
    return namespace['run_episode']


run_archived_episode=make_archiving_runner()


class ArchivingCanonical48Env(original.Canonical48Env):
    def reset(self,*,seed=None,options=None):
        # Same queue/reset as the original, with only the private runner target.
        gym.Env.reset(self,seed=seed)
        self.close();original.resource_check()
        self.publish,self.receive=queue.Queue(),queue.Queue()
        output=self.output_root/f'episode_{self.episode_index:05d}'/'rollout'
        self.episode_index+=1
        self.worker=threading.Thread(target=run_archived_episode,
            args=(self.spec,self.menagerie,output,self.publish,self.receive,self.duration),daemon=True)
        self.worker.start()
        event,observation,phase=self._next()
        if event!='observation':raise RuntimeError('Reset did not reach actor boundary')
        self.obs,self.phase=observation,phase
        self.previous_action=np.zeros(7);self.last_result=None
        return self.obs.astype(np.float32),{}


PotentialArchiveEnv=environment_class(ArchivingCanonical48Env)


class TransitionJournal:
    """Write every completed transition immediately, including partial's last next."""
    def __init__(self,directory,metadata):
        self.directory=Path(directory);self.rows=[];self.closed=False
        self.stream=(self.directory/'transitions.jsonl').open('x',buffering=1)
        original.save_json(self.directory/'transition_contract.json',metadata)

    def append(self,row):
        if self.closed:raise RuntimeError('Transition journal closed')
        row=dict(row,step_index=len(self.rows),actor_period_s=.04)
        # Convert into owned JSON values before the next controller mutation.
        row=json.loads(json.dumps(row,allow_nan=False,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item()))
        self.stream.write(json.dumps(row,allow_nan=False,separators=(',',':'))+'\n')
        self.rows.append(row)

    def close(self,reason):
        if self.closed:return
        self.stream.close();self.closed=True
        fields=('step_index','actor_period_s','observation','next_observation','next_observation_valid','requested_action','policy_action',
            'parameter_request','parameter_control_active','log_scale','stiffness','damping','execution_action',
            'reward','stage','next_stage','terminated','truncated')
        arrays={key:np.asarray([r[key] for r in self.rows]) for key in fields}
        if self.rows:
            for key in self.rows[0]['reward_terms']:
                arrays['reward_term_'+key]=np.asarray([r['reward_terms'][key] for r in self.rows])
        np.savez_compressed(self.directory/'transitions.npz',**arrays)
        original.save_json(self.directory/'transition_summary.json',dict(reason=reason,transitions=len(self.rows),
            completed=bool(self.rows and self.rows[-1]['terminated']),
            last_next_observation_valid=bool(self.rows and self.rows[-1]['next_observation_valid']),
            terminal_observation='last actor observation placeholder with valid=false; no terminal bootstrap',
            partial_observation='last completed transition has actual next actor observation, valid=true'))


class PairedControlEnv(gym.Wrapper):
    def __init__(self,spec,menagerie,output_root,*,mode,nominal_options,duration=None,backend=None):
        if mode not in ('parameter6','direct7'):raise ValueError('Unknown control mode')
        env=backend if backend is not None else PotentialArchiveEnv(spec,menagerie,output_root,duration)
        super().__init__(env)
        self.mode=mode;self.nominal_options=copy.deepcopy(nominal_options)
        self.controller=Canonical48VMCTuning(self.nominal_options)
        self.journal=None;self.active=False
        if mode=='parameter6':self.action_space=gym.spaces.Box(-1.,1.,shape=(6,),dtype=np.float32)
        self.output_root=Path(output_root)
        self.runtime_spec=copy.deepcopy(spec)

    def reset(self,*,seed=None,options=None):
        self.close()
        observation,info=self.env.reset(seed=seed,options=options)
        self.controller.reset();self.active=True
        folder=self.output_root/f'episode_{self.env.episode_index-1:05d}'
        self.journal=TransitionJournal(folder,dict(mode=self.mode,observation_dim=48,
            policy_action_dim=int(self.action_space.shape[0]),execution_action_dim=7,
            runtime_core_config=json.loads(self.runtime_spec['command']['environment']['CORE_VMC_CONFIG']),
            adapter_train_nominal_options=self.nominal_options,adapter_active=self.mode=='parameter6',
            nominal_configuration_rule='Always training CORE for adapter; runtime fixture CORE unchanged',
            reward=reward_protocol(),actor_privileged_fields=[],critic_privileged_fields=[],
            parameter_input='raw SI float64 canonical48; never VecNormalize result',
            direct_parameter_fields='inactive nominal metadata only; parameter_control_active=false',
            requested_action='Gym boundary request; SB3 clips Gaussian sample before env, not unbounded policy latent',
            terminal_next='last actor observation placeholder, next_observation_valid=false',
            base_bridge_sha256=original.sha(Path(original.__file__)),
            runner_change="exactly one SKIP_MODEL_ARCHIVE='1' -> '0'; original module unchanged"))
        return observation,info

    def step(self,action):
        if not self.active:raise RuntimeError('Step requires reset and nonterminal episode')
        request=np.asarray(action,dtype=np.float64)
        if request.shape!=self.action_space.shape or not np.isfinite(request).all():raise ValueError('Invalid policy action')
        applied=np.clip(request,self.action_space.low,self.action_space.high)
        previous=self.env.obs.copy();stage=int(self.env.phase)
        if self.mode=='parameter6':
            execution=self.controller.act(previous,applied)
            parameters=self.controller.last_parameters
        else:
            execution=applied.copy()
            parameters=dict(request=np.zeros(6),log_scale=np.zeros(6),
                stiffness=self.controller.nominal_k.copy(),damping=self.controller.nominal_d.copy())
        observation,reward,terminated,truncated,info=self.env.step(execution)
        if truncated:raise RuntimeError('Finite-horizon protocol must terminate, not bootstrap truncation')
        self.journal.append(dict(observation=previous,next_observation=self.env.obs.copy(),
            next_observation_valid=not terminated,requested_action=request,policy_action=applied,
            parameter_request=parameters['request'],parameter_control_active=self.mode=='parameter6',
            log_scale=parameters['log_scale'],stiffness=parameters['stiffness'],damping=parameters['damping'],
            execution_action=execution,reward=float(reward),reward_terms=copy.deepcopy(info['reward_terms']),
            stage=stage,next_stage=int(self.env.phase),terminated=bool(terminated),truncated=bool(truncated)))
        info=dict(info,control_mode=self.mode,next_observation_valid=not terminated,
            terminal_observation_is_placeholder=bool(terminated),gym_reward_float64=float(reward))
        if terminated:
            self.active=False;self.journal.close('task_horizon_or_safety_termination')
        return observation,float(reward),terminated,truncated,info

    def close(self):
        self.env.close()
        if self.journal is not None:self.journal.close('budget_or_reset_interruption')
        self.journal=None;self.active=False
