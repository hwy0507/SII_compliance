from pathlib import Path
import ast,hashlib,json,time
D=Path(__file__).resolve().parent;B=D.parents[1];S=B/'runtime/census98_continuation_20261031_v1';R=B/'runs/parameter_census_cycle98_20261031_v1'
rd=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
lock=rd(S/'SOURCES.json')
for n,h in lock['files'].items():assert sha(S/n)==h;ast.parse((S/n).read_text())
source=(S/'census_native.py').read_text();tree=ast.parse(source);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CensusCache');add=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='add');code=ast.get_source_segment(source,add);assert code.index('super().add(**row)')<code.index('self.sync_terminals()')
methods={}
for m in ['impedance','admittance','vmc']:
 reg=rd(R/m/'REGISTRATION.json');p=R/m/'trainer_registered.py';assert sha(p)==reg['post_interruption_continuation']['patched_trainer_sha256'];s=p.read_text();a=s.index("replay.add(observations=previous['observation']");b=s.index('steps += 1',a);c=s.index('transition_log.write',b);d=s.index('metrics = learner.update(replay.sample(batch_size))',c);e=s.index('optimizer_log.write',d);assert a<b<c<d<e
 methods[m]=dict(trainer=str(p),sha256=sha(p),registered_source_exact=True,source_order='add including cache synchronization -> increment step -> journal -> learner.update -> same-step optimizer log')
result=dict(passed=True,time=time.time(),locked_runtime_sources=len(lock['files']),methods=methods,runtime_sources_sha256=sha(S/'SOURCES.json'),scope='Registered source lock and AST/source order support inclusive done count audit; actual terminal growth pending.')
with (D/'SOURCE_ORDER_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('Source lock and inclusive population order passed')
