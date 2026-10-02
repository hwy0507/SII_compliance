"""Frozen v6 scene evaluation; all changes are registered in PROTOCOL.json."""
import argparse,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import bridge_frozen as b
ROOT=Path('/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002')
PROTOCOL=json.loads((ROOT/'PROTOCOL.json').read_text())
ESN_SOURCE=Path('/home/arm1/sii_shared/SII_compliance/source/14820fac7141fa8779aa56b5ae0ba595ee2ee0a5/code/mujoco_6d_vmc_benchmark/scripts/office_vmc_memory_esn_20260927.py')
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False,default=lambda v:str(v) if isinstance(v,Path) else v.tolist())+'\n')

class ESNPolicy:
    def __init__(self,env,args):
        spec=importlib.util.spec_from_file_location('validation_esn_actor',ESN_SOURCE)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        self.model=mod.OfficeVMCMemoryESN(args.checkpoint);self.label=args.id
        self.obs=[];self.actions=[];self.states=[]
    def act(self,obs):
        self.obs.append(obs.copy());action=self.model.act(obs)
        self.actions.append(action.copy());self.states.append(self.model.state.copy());return action
    def finish(self,out):
        self.model.reset()
        for obs,expected,state in zip(self.obs,self.actions,self.states):
            assert np.array_equal(self.model.act(obs),expected)
            assert np.array_equal(self.model.state,state)
        np.savez_compressed(out/'baseline_policy.npz',observation=self.obs,action=self.actions,reservoir_state=self.states)
        return dict(label=self.label,steps=len(self.actions),training=False,observation='canonical48',action_dimension=7,action_and_state_replay_max_error=0,actor_source_sha256=b.sha(ESN_SOURCE))

def install_loader(output,clear,construct):
    import fr3_scene
    original=(b.SOURCE/'scripts/fr3_scene.py').read_text()
    needle='    model = mujoco.MjModel.from_xml_string(xml)'
    assert original.count(needle)==1
    edge_pos=PROTOCOL['edge_position_m'] if not clear else [.625,-.25,-3.]
    patch="""    import xml.etree.ElementTree as ET
    v6_root = ET.fromstring(xml)
    v6_edge = v6_root.find(".//geom[@name='office_v5_unexpected_edge']")
    assert v6_edge is not None
    v6_edge.set('pos', V6_POS)
    v6_edge.set('size', V6_SIZE)
    xml = ET.tostring(v6_root, encoding='unicode')
""".replace('V6_POS',repr(' '.join(map(str,edge_pos)))).replace('V6_SIZE',repr(' '.join(map(str,PROTOCOL['edge_half_size_m']))))
    replacement=patch+needle
    binary=ROOT/('construction_clear' if clear else 'construction')/'rollout.mjb'
    if not construct:
        assert binary.exists()
        replacement+="\n    model = mujoco.MjModel.from_binary_path("+repr(str(binary))+")"
    modified=original.replace(needle,replacement)
    exec(compile(modified,str(output/'executed_fr3_scene.py'),'exec'),fr3_scene.__dict__)
    (output/'executed_fr3_scene.py').write_text(modified)
    return dict(construct=construct,binary=str(binary),expected_sha256=None if construct else b.sha(binary),executed_constructor_sha256=hashlib.sha256(modified.encode()).hexdigest(),edge_position_m=edge_pos)

def main():
    p=argparse.ArgumentParser();p.add_argument('--id',required=True);p.add_argument('--construct',action='store_true');p.add_argument('--clear',action='store_true');p.add_argument('--probe',type=float);a=p.parse_args()
    if a.construct: case=PROTOCOL['cases'][0]
    else:case=next((x for x in PROTOCOL['cases'] if x['id']==a.id),PROTOCOL['cases'][0] if a.id=='clear_zero' else None)
    assert case is not None
    args=SimpleNamespace(**{k:case[k] for k in ['method','controller','checkpoint']},id=a.id)
    if args.checkpoint:args.checkpoint=Path(args.checkpoint)
    for rel,h in case['checkpoint_hashes'].items():
        path=args.checkpoint if args.checkpoint.is_file() else args.checkpoint/rel
        assert b.sha(path)==h
    out=ROOT/a.id;out.mkdir(exist_ok=False)
    os.environ.setdefault('MUJOCO_MENAGERIE_PATH',str(b.ASSETS));os.environ.setdefault('MUJOCO_GL','egl')
    assert all(os.environ.get(k)=='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
    import mujoco
    assert mujoco.__version__=='3.11.0'
    original=json.loads((b.REFERENCE/'esn_combined_v4.json').read_text())
    settings=dict(original['arguments'])
    config=dict(settings['tool_contact'])
    config.update(id='office-validation-v6',registration='PROTOCOL.json frozen before evaluation',ball_center_m=PROTOCOL['ball_center_m'],rod_center_m=PROTOCOL['rod_center_m'],rod_hold_s=PROTOCOL['rod_hold'],timing='ball2; person4-11; rod13-14.5, hold14.5-20.5, retract20.5-22.5',edge_position_m=PROTOCOL['edge_position_m'],edge_half_size_m=PROTOCOL['edge_half_size_m'])
    settings.update(output=out/'rollout',esn_model=None,esn_mode='shadow',teacher='none',hybrid_vmc_blend=0.,render=False,impact_slowmo=False,physics_probe_s=a.probe,ball_speed=PROTOCOL['ball_speed'],person_start=PROTOCOL['person_start'],rod_start=PROTOCOL['rod_start'],rod_hold=PROTOCOL['rod_hold'],interaction_schedule='legacy',tool_contact=config,events='settle' if a.clear else 'all')
    sys.path.insert(0,str(b.SOURCE/'scripts'))
    run,executed,replacements=b.build_evaluator()
    loader=install_loader(out,a.clear,a.construct)
    (out/'executed_evaluator.py').write_text(executed)
    record=dict(status='running',started_epoch=time.time(),argv=sys.argv,protocol_sha256=b.sha(ROOT/'PROTOCOL.json'),case=case,arguments=settings,loader=loader,python=sys.version,mujoco=mujoco.__version__,training=False,source_hashes={str(f):b.sha(f) for f in Path(__file__).parent.glob('*.py')},upstream_source_hashes={str(f.relative_to(b.SOURCE)):b.sha(f) for f in (b.SOURCE/'scripts').glob('*.py')})
    dump(out/'EXECUTION.json',record)
    save=mujoco.mj_saveModel
    def checked(model,filename,buffer):
        result=save(model,filename,buffer)
        if not a.construct:assert b.sha(filename)==loader['expected_sha256'], 'Model changed across policies'
        return result
    mujoco.mj_saveModel=checked
    try:
        factory=(lambda env:ESNPolicy(env,args)) if args.method=='esn' else (lambda env:b.Policy(env,args))
        run(SimpleNamespace(**settings),policy_factory=factory)
        s=json.loads((out/'rollout.json').read_text())
        record.update(status='complete',task=s['task_success'],strict=s['strict_success'],stage=s['final_task_stage'],full_horizon=s['full_task_horizon_completed'],model_sha256=s['model_sha256'])
    except BaseException as exc:
        record.update(status='failed',error=repr(exc));raise
    finally:
        mujoco.mj_saveModel=save;record['ended_epoch']=time.time();dump(out/'EXECUTION.json',record)
if __name__=='__main__':main()
