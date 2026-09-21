"""Evaluate current MLP and ESN checkpoints on identical manifest splits."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np

def load_mlp(path):
 z=np.load(path);return dict(mean=z['mean'],std=z['std'],w0=z['0.weight'],b0=z['0.bias'],w1=z['2.weight'],b1=z['2.bias'],w2=z['4.weight'],b2=z['4.bias'])
def mlp_predict(m,x):
 h=np.tanh((x-m['mean'])/m['std']@m['w0'].T+m['b0'])
 h=np.tanh(h@m['w1'].T+m['b1']);raw=h@m['w2'].T+m['b2']
 return np.c_[1/(1+np.exp(-np.clip(raw[:,0],-60,60))),np.tanh(raw[:,1:])]
def eval_model(kind,model_path,root,rows):
 if kind=='mlp':m=load_mlp(model_path)
 else:
  import sys;sys.path.insert(0,str(Path(__file__).parent));from esn128_action7_20260918 import ESN128Action7
  m=ESN128Action7.load(model_path)
 out=[]
 for r in rows:
  p=Path(r['trace']);p=p if p.is_absolute() else root/p
  with np.load(p,allow_pickle=False) as z:x=z['observation'];y=z['teacher_action']
  if kind=='mlp':pred=mlp_predict(m,x)
  else:
   m.reset();pred=np.stack([m.act(o) for o in x])
  err=(pred-y)**2
  out.append(dict(scene=r['scene'],episode=r['id'],mse=float(err.mean()),mae=float(np.abs(pred-y).mean()),
      slow_mse=float(err[:,0].mean()),velocity_mse=float(err[:,1:4].mean()),angular_mse=float(err[:,4:7].mean())))
 return out
def summarize(rows):
 scenes=sorted(set(r['scene'] for r in rows));return dict(overall_mse=float(np.mean([r['mse'] for r in rows])),overall_mae=float(np.mean([r['mae'] for r in rows])),per_scene={s:{k:float(np.mean([r[k] for r in rows if r['scene']==s])) for k in ('mse','mae','slow_mse','velocity_mse','angular_mse')} for s in scenes})
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dataset',type=Path,required=True);ap.add_argument('--mlp',type=Path,required=True);ap.add_argument('--esn',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();m=json.load(open(a.dataset/'manifest.json'));result=dict(dataset_manifest_sha256=hashlib.sha256((a.dataset/'manifest.json').read_bytes()).hexdigest(),models={})
 for kind,path in (('mlp',a.mlp),('esn',a.esn)):
  result['models'][kind]={}
  for split in ('validation','test'):
   rows=eval_model(kind,path,a.dataset,m[split]);result['models'][kind][split]=dict(summary=summarize(rows),episodes=rows)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2));print(json.dumps({k:{s:v['summary'] for s,v in d.items()}for k,d in result['models'].items()},indent=2))
if __name__=='__main__':main()
