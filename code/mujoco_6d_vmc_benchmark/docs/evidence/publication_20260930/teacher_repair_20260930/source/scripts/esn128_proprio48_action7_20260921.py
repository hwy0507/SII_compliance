"""48-D proprioceptive input, fixed 128-unit reservoir, 128-unit readout."""
import json
import numpy as np


class ESN128Proprio48Action7:
    kind = "esn"
    dt = .04
    reservoir = 128
    input_dim = 48

    def __init__(self, mean, std, seed=20260921):
        self.mean=np.asarray(mean,dtype=float);self.std=np.asarray(std,dtype=float)
        if self.mean.shape!=(self.input_dim,) or self.std.shape!=(self.input_dim,):raise ValueError("Expected 48-D normalization")
        self.seed=seed;self.input_mask=np.ones(self.input_dim);self.alpha=1.;self.output_gain=1.
        rng=np.random.default_rng(seed)
        self.win=rng.normal(0,.45/np.sqrt(self.input_dim),(self.reservoir,self.input_dim+1))
        w=rng.normal(size=(self.reservoir,self.reservoir))*(rng.random((self.reservoir,self.reservoir))<.08)
        self.w=w*(.9/np.max(np.abs(np.linalg.eigvals(w))))
        tau=np.concatenate([np.full(len(indices),value) for indices,value in zip(
            np.array_split(np.arange(self.reservoir),3),(.08,.4,1.6))])
        self.leak=1-np.exp(-self.dt/tau);self.head={};self.reset()

    def reset(self):
        self.state=np.zeros(self.reservoir);self.previous_action=np.zeros(7)

    def features(self, observation):
        x=np.asarray(observation,dtype=float)
        if x.shape!=(self.input_dim,) or not np.isfinite(x).all():raise ValueError("Expected finite proprio48 observation")
        x=np.clip((x-self.mean)/self.std,-12,12)*self.input_mask
        self.state+=self.leak*(np.tanh(self.win@np.r_[1.,x]+self.w@self.state)-self.state)
        return np.r_[x,self.state]

    def act(self, observation):
        features=(self.features(observation)-self.head["fmean"])/self.head["fstd"]
        hidden=np.tanh(self.head["w1"]@features+self.head["b1"])
        logits=self.head["w2"]@hidden+self.head["b2"]
        result=np.tanh(logits);result[0]=1/(1+np.exp(-np.clip(logits[0],-60,60)))
        result*=self.output_gain;self.previous_action+=self.alpha*(result-self.previous_action)
        return self.previous_action.copy()

    def save(self,path,metadata):
        with open(path,"wb") as stream:
            np.savez_compressed(stream,contract="proprio48_esn128_action7_v1",metadata=json.dumps(metadata),
                seed=self.seed,mean=self.mean,std=self.std,win=self.win,w=self.w,leak=self.leak,
                input_mask=self.input_mask,alpha=self.alpha,output_gain=self.output_gain,**self.head)

    @classmethod
    def load(cls,path):
        with np.load(path,allow_pickle=False) as data:
            if str(data["contract"])!="proprio48_esn128_action7_v1":raise ValueError("Wrong checkpoint contract")
            obj=cls.__new__(cls);obj.seed=int(data["seed"]);obj.input_mask=data["input_mask"].copy()
            obj.alpha=float(data["alpha"]);obj.output_gain=float(data["output_gain"])
            for key in ("mean","std","win","w","leak"):setattr(obj,key,data[key].copy())
            obj.head={key:data[key].copy() for key in ("fmean","fstd","w1","b1","w2","b2")}
        obj.reset();return obj
