from pathlib import Path
import json,sys,time,ast,hashlib,difflib
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/history89_violation_pipeline_preflight_20261030_v1';C=B/'runtime/history89_violation_consumers_20261030_v1';I=B/'runtime/history89_violation_interface_20261030_v2';P=B/'runs/parameter_history_cycle89_20261030_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
from violation_pipeline import read,sha,ref,validate_registration,transform_trainer

def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
assert read(C/'CONSUMER_REVIEW.json')['passed'] and read(C/'CACHE_SAVED_REVIEW.json')['passed'];O.mkdir();(O/'archive').mkdir();(O/'frozen').mkdir()
inputs=[C/n for n in ('CACHE_PLAN.json','CONSUMER_PLAN.json','CACHE_SAVED_REVIEW.json','CONSUMER_REVIEW.json')]+[B/'runs/parameter_history_cycle89_review_20261030_v1/REVIEW.json']
for m in ('impedance','admittance','vmc'):
 (O/m).mkdir();(O/'archive'/m).mkdir();(O/'frozen'/m).mkdir();parent=P/m/'REGISTRATION.json';p=read(parent);b=read(I/(m+'_BINDING.json'));cp=B/'runs/parameter_history_cycle89_archive_20261030_v1'/m/'cycle_00089.pt';saved=read(C/(m+'_CACHE_SAVED_REVIEW.json'))['snapshot'];assert sha(cp)==b['checkpoint_sha256'] and sha(saved['path'])==saved['sha256']
 p['violation_critic_amendment']=dict(binding=b,parent_registration=ref(parent),parent_checkpoint=ref(cp),snapshot={k:saved[k] for k in ('path','sha256')},scope='migration_preparation_only',first_cycle=90,online_launch=False,physics_steps=0,formal_updates=0);validate_registration(p);put(O/m/'REGISTRATION.json',p)
 src=P/m/'trainer_registered.py';s=transform_trainer(src.read_text());ast.parse(s);(O/m/'trainer_prepared.py').write_text(s);(D/(m+'_trainer.diff')).write_text(''.join(difflib.unified_diff(src.read_text().splitlines(True),s.splitlines(True),fromfile=str(src),tofile='prepared52')))
 inputs += [parent,cp,Path(saved['path']),src,O/m/'REGISTRATION.json',O/m/'trainer_prepared.py',I/(m+'_BINDING.json')]
for p in D.glob('*.py'):ast.parse(p.read_text())
plan=dict(time=time.time(),scope='migration metadata, native real-batch clone restore, actual evaluator check-only, full health diagnostic; no physical episodes or online90',methods=['impedance','admittance','vmc'],cpu=11,device='cuda:1',budget_seconds=1800,clone_updates=6,formal_updates=0,physics_steps=0,sources={p.name:sha(p) for p in D.glob('*.py')},inputs=[ref(p) for p in inputs],root=str(O),training90=False)
put(D/'PLAN.json',plan);print('Registered finite pipeline checks',sha(D/'PLAN.json'))
