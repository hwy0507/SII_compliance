"""Balanced behavior cloning MLP for the current four-scene teacher bank."""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
import torch
from torch import nn

def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2));q.replace(p)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dataset',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--epochs',type=int,default=120);ap.add_argument('--hidden',type=int,default=128);ap.add_argument('--corner-repeat',type=int,default=1);a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=True)
 m=json.load(open(a.dataset/'manifest.json'));assert json.load(open(a.dataset/'READY.json'))['ready']
 original_train=list(m['train']);extra=[r for r in original_train if r['scene']=='corner']*(max(1,a.corner_repeat)-1);m['train']=original_train+extra
 rows=m['train']+m['validation']+m['test'];train_n=len(m['train']);val_n=len(m['validation'])
 xs=[];ys=[];lengths=[]
 for r in rows:
  trace=Path(r['trace']); trace=trace if trace.is_absolute() else a.dataset/trace
  with np.load(trace,allow_pickle=False) as z:xs.append(z['observation'].astype('float32'));ys.append(z['teacher_action'].astype('float32'));lengths.append(len(xs[-1]))
 mean=np.concatenate(xs[:train_n]).mean(0);std=np.concatenate(xs[:train_n]).std(0).clip(min=.03);device='cuda' if torch.cuda.is_available() else 'cpu';torch.set_num_threads(8);torch.manual_seed(20260921)
 X=[torch.tensor((x-mean)/std,dtype=torch.float32) for x in xs];Y=[torch.tensor(y,dtype=torch.float32) for y in ys]
 model=nn.Sequential(nn.Linear(45,a.hidden),nn.Tanh(),nn.Linear(a.hidden,a.hidden),nn.Tanh(),nn.Linear(a.hidden,7)).to(device);opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-5)
 starts=np.r_[0,np.cumsum(lengths)];catx=torch.cat(X[:train_n]).to(device);caty=torch.cat(Y[:train_n]).to(device);vX=torch.cat(X[train_n:train_n+val_n]).to(device);vY=torch.cat(Y[train_n:train_n+val_n]).to(device);best=1e9;best_state=None;hist=[]
 for ep in range(a.epochs):
  model.train();perm=torch.randperm(len(catx),device=device);loss=0
  for j in range(0,len(perm),8192):
   idx=perm[j:j+8192];opt.zero_grad();raw=model(catx[idx]);pred=torch.cat((torch.sigmoid(raw[:,:1]),torch.tanh(raw[:,1:])),1);l=((pred-caty[idx])**2).mean();l.backward();opt.step();loss+=float(l)
  model.eval()
  with torch.no_grad():raw=model(vX);pred=torch.cat((torch.sigmoid(raw[:,:1]),torch.tanh(raw[:,1:])),1);val=float(((pred-vY)**2).mean())
  hist.append(dict(epoch=ep+1,train_loss=loss,val_mse=val))
  if val<best:best=val;best_state={k:v.detach().cpu().numpy() for k,v in model.state_dict().items()}
  if (ep+1)%10==0: print(json.dumps(hist[-1]),flush=True)
 np.savez_compressed(out/'best.npz',contract='current_four_scene_action7_mlp_v1',mean=mean,std=std,hidden=np.int64(a.hidden),**best_state)
 result=dict(complete=True,method='mlp_behavior_cloning',observation_dim=45,action_dim=7,hidden=a.hidden,epochs=a.epochs,corner_repeat=a.corner_repeat,best_validation_mse=best,train_episodes=train_n,validation_episodes=val_n,test_episodes=len(m['test']),dataset_manifest_sha256=hashlib.sha256((a.dataset/'manifest.json').read_bytes()).hexdigest(),office_used=False,history=hist)
 dump(out/'TRAINING_COMPLETE.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
