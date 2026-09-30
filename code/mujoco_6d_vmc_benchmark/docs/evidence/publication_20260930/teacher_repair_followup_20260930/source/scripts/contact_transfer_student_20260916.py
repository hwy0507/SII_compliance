"""Shared contact45 encoder; history MLP versus three-timescale ESN.

No force gates, scene routing, or rule-based avoidance runs inside either
student. Both predict slowdown and xyz residual actions from the same input.
"""
import json
from collections import deque
import numpy as np


class TransferStudent:
    def __init__(self,kind,mean,std,history=32,reservoir=128,taus=(.04,.4,2.),hidden=128,alpha=1.,seed=42,dt=.04,spectral_bound=None):
        self.kind=kind;self.mean=np.asarray(mean);self.std=np.asarray(std)
        self.history=history;self.reservoir=reservoir;self.taus=tuple(taus)
        self.hidden=hidden;self.alpha=alpha;self.seed=seed;self.head={};self.dt=dt;self.spectral_bound=spectral_bound
        if not np.isfinite(dt) or dt<=0:raise ValueError('Invalid policy dt')
        if self.mean.shape!=(45,) or self.std.shape!=(45,):raise ValueError("contact45_v2 input required")
        if kind not in ("mlp","esn"):raise ValueError(kind)
        if kind=="esn":
            rng=np.random.default_rng(seed)
            self.win=rng.normal(0,.45/np.sqrt(45),(reservoir,46))
            w=rng.normal(size=(reservoir,reservoir))*(rng.random((reservoir,reservoir))<.08)
            self.w=w*(.90/max(np.max(np.abs(np.linalg.eigvals(w))),1e-9))
            if spectral_bound is not None:
                if not 0<spectral_bound<1:raise ValueError('Contraction bound must be in (0,1)')
                self.w*=min(1.,spectral_bound/max(np.linalg.norm(self.w,2),1e-9))
            times=np.concatenate([np.full(len(part),tau) for part,tau in zip(np.array_split(np.arange(reservoir),len(taus)),taus)])
            self.leak=1.-np.exp(-dt/times)
        self.reset()

    def reset(self):
        self.queue=deque(maxlen=self.history);self.state=np.zeros(self.reservoir);self.previous=np.zeros(4)

    def features(self,observation):
        x=np.asarray(observation)
        if x.shape!=(45,) or not np.isfinite(x).all():raise ValueError("Invalid actor input")
        x=np.clip((x-self.mean)/self.std,-12,12)
        if self.kind=="mlp":
            if not self.queue:self.queue.extend(x.copy() for _ in range(self.history))
            else:self.queue.append(x.copy())
            return np.concatenate(self.queue)
        candidate=np.tanh(self.win@np.r_[1.,x]+self.w@self.state)
        self.state+=(candidate-self.state)*self.leak
        return np.r_[x,self.state]

    def act(self,observation):
        f=(self.features(observation)-self.head["fmean"])/self.head["fstd"]
        h=np.tanh(f@self.head["w1"].T+self.head["b1"])
        raw=np.tanh(h@self.head["w2"].T+self.head["b2"])
        self.previous=self.alpha*raw+(1.-self.alpha)*self.previous
        action=np.zeros(7);action[:4]=self.previous;action[0]=max(0.,action[0])
        return action

    def save(self,path,metadata):
        config={k:getattr(self,k) for k in ("kind","history","reservoir","taus","hidden","alpha","seed","dt","spectral_bound")}
        extra={} if self.kind=="mlp" else dict(win=self.win,w=self.w,leak=self.leak)
        np.savez_compressed(path,contract="contact45_v2",config=json.dumps(config),metadata=json.dumps(metadata),mean=self.mean,std=self.std,**extra,**self.head)

    @classmethod
    def load(cls,path):
        with np.load(path,allow_pickle=False) as a:
            if str(a["contract"])!="contact45_v2":raise ValueError("Wrong checkpoint contract")
            obj=cls.__new__(cls)
            for k,v in json.loads(str(a["config"])).items():setattr(obj,k,v)
            obj.dt=getattr(obj,'dt',.04);obj.spectral_bound=getattr(obj,'spectral_bound',None)
            obj.mean=a["mean"].copy();obj.std=a["std"].copy()
            obj.head={k:a[k].copy() for k in ("fmean","fstd","w1","b1","w2","b2")}
            if obj.kind=="esn":
                for k in ("win","w","leak"):setattr(obj,k,a[k].copy())
            obj.reset();return obj
