"""Episode-aware n-step sampling from retained RAW one-step transitions.

Uses the pinned upstream critic's gamma**n_step bootstrap. Short windows only
occur at true terminals, where bootstrap is zero. Time-limit truncation is not
supported by this finite-horizon office adapter. No cross-episode rewards,
fabricated terminal transitions, demonstrations, or repeated tail padding.
"""
import numpy as np
from research72_train_rl_20261003 import Replay


class MultiStepReplay(Replay):
    def __init__(self,capacity,dimension,seed,*,n_step,gamma):
        super().__init__(capacity,dimension,seed)
        assert isinstance(n_step,int) and n_step>=1 and 0<gamma<=1
        self.n_step=n_step;self.gamma=gamma;self.last_terminal=-1

    def add(self,**values):
        assert self.count<self.capacity,'No ring overwrite in finite registered budget'
        assert values['truncated']==0.,'Office finite horizon must be a true terminal'
        assert values['terminated'] in (0.,1.)
        if values['terminated']:self.last_terminal=self.count
        super().add(**values)

    @property
    def valid_count(self):
        return max(0,self.count-self.n_step+1,self.last_terminal+1)

    def at(self,ids):
        ids=np.asarray(ids,int)
        assert np.all((ids>=0)&(ids<self.valid_count))
        batch={k:v[ids].copy() for k,v in self.data.items()}
        total=np.zeros(len(ids),np.float64);alive=np.ones(len(ids),bool);ends=ids.copy()
        for offset in range(self.n_step):
            selected=np.flatnonzero(alive)
            if not len(selected):break
            indices=ids[selected]+offset
            assert np.all(indices<self.count)
            total[selected]+=self.gamma**offset*self.data['reward'][indices]
            ends[selected]=indices
            alive[selected]=~self.data['terminated'][indices].astype(bool)
        batch['reward']=total.astype(np.float32)
        batch['terminated']=self.data['terminated'][ends].copy()
        batch['next_observation']=self.data['next_observation'][ends].copy()
        return batch

    def sample(self,n):
        assert self.valid_count>0
        return self.at(self.rng.integers(self.valid_count,size=n))

    def save(self,path):
        metadata=super().save(path)
        metadata.update(n_step=self.n_step,gamma=self.gamma,last_terminal=self.last_terminal)
        return metadata

    def restore(self,path,state):
        assert state['n_step']==self.n_step and state['gamma']==self.gamma
        super().restore(path,state)
        assert not self.data['truncated'][:self.count].any()
        terminals=np.flatnonzero(self.data['terminated'][:self.count])
        self.last_terminal=int(terminals[-1]) if len(terminals) else -1
        assert self.last_terminal==state['last_terminal']
