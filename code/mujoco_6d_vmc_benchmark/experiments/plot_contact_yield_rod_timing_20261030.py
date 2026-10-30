"""Plot measured, independently audited teacher events; no model/test claims."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def plot(evidence,prefix):
 evidence=Path(evidence);prefix=Path(prefix);data=json.loads(evidence.read_text())
 assert data['status']=='all10_development_rods_independently_qualified'
 rows=data['rod_audits'];assert len(rows)==10
 fields=[('hand_contact_first_s','Contact','#0072b2','o'),('yield_start_s','Yield','#e69f00','^'),('pass_s','Geometric pass','#cc79a7','s'),('rejoin_confirmed_s','Persistent rejoin confirmed','#009e73','D'),('retract_start_s','Withdrawal starts','#333333','x')]
 fig,ax=plt.subplots(figsize=(12,5.8));margins=[];events=[]
 for i,row in enumerate(rows):
  b=row['behavior'];assert b['status']=='passed' and all(b['checks'].values())
  assert b['hand_contact_first_s']<=b['yield_start_s']<b['pass_s']<=b['rejoin_confirmed_s']<b['retract_start_s']
  vals=[b[k] for k,*_ in fields];margin=vals[-1]-vals[-2];margins.append(margin)
  ax.plot(vals[:-1],[i]*4,color='#cccccc',lw=2,zorder=1)
  ax.plot(vals[-2:],[i]*2,color='#009e73',alpha=.2,lw=7,zorder=1)
  for (key,label,color,marker),t in zip(fields,vals):ax.scatter(t,i,c=color,marker=marker,s=43,label=label if i==0 else None,zorder=3)
  ax.annotate(f'{margin:.2f} s',(13.25,i),fontsize=9,va='center',color='#007552')
  events.append(dict(id=row['id'],**{k:b[k] for k,*_ in fields},rejoin_margin_s=margin))
 labels=[r['id']+('  (validation)' if r['id'] in ('rod_08','rod_09') else '  (train)') for r in rows]
 ax.set_yticks(range(10),labels);ax.invert_yaxis();ax.set_xlim(4.5,14.1)
 ax.set_xlabel('Measured simulation time (s)');ax.grid(axis='x',alpha=.2)
 ax.set_title('VMC teacher: contact → yield → pass → rejoin before withdrawal\n10 development identities; not ESN/MLP/RNN or unseen-test results',fontsize=12,pad=13)
 ax.text(13.25,-.65,'Time margin',fontsize=9,color='#007552')
 ax.spines[['top','right']].set_visible(False);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.15),ncol=5,frameon=False,fontsize=9)
 fig.subplots_adjust(left=.18,right=.98,top=.82,bottom=.2)
 for ext in ('.png','.pdf'):
  path=Path(str(prefix)+ext);assert not path.exists();fig.savefig(path,dpi=180)
 plt.close(fig)
 receipt=dict(status='measured_development_teacher_timing',evidence_sha256=sha(evidence),plotter_sha256=sha(Path(__file__)),events=events,minimum_margin_s=min(margins),maximum_margin_s=max(margins),figure_sha256={ext:sha(Path(str(prefix)+ext)) for ext in ('.png','.pdf')},scope='10 audited development teacher identities; not model learning or unseen-test success. Geometry at 40ms samples, contact from physical substeps. No new integration.')
 output=Path(str(prefix)+'.json');assert not output.exists();output.write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(dict(rods=len(rows),minimum_margin_s=min(margins),maximum_margin_s=max(margins))))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output-prefix',type=Path,required=True);a=p.parse_args();plot(a.evidence,a.output_prefix)
