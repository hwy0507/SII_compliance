"""Pinned office v5 evaluation bridge; leaves the shared main source untouched.

The executed evaluator differs only by explicit policy callbacks. Both upstream
and patched source hashes are saved. This is a transfer evaluator, not training.
"""
import argparse, hashlib, json, os, sys, time
from pathlib import Path
from types import SimpleNamespace
import numpy as np

STUDY=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
MAIN_SHA='7cd5f4b7ac0a3056df76ac62bc690ded0724b104'
SOURCE=Path('/home/arm1/sii_shared/SII_compliance/source')/MAIN_SHA/'code/mujoco_6d_vmc_benchmark'
REFERENCE=Path('/home/arm1/sii_shared/SII_compliance/runs/main/tool_contact_review_20261002/evidence/tool_contact_20261002/v5_esn_full')
MODEL_SHA='b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1'
PARAMETER=STUDY/'parameter_rl/frozen_train02'
DIRECT=STUDY/'frozen_adapter02/primitive_baselines_20261002'
ASSETS=Path('/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_runtime_inputs_complete_20260930/menagerie')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False))

def build_evaluator():
    source=SOURCE/'scripts/validate_office_apparatus_v5_20260917.py'
    text=source.read_text()
    replacements=[
      ('def run(a):','def run(a, policy_factory=None):'),
      ('    abort_reason=None\n    for step_index', '    external_policy=policy_factory(env) if policy_factory else None\n    abort_reason=None\n    for step_index'),
      ('        interval_peak[:]=0.;interval_impulse[:]=0.\n        env.step(applied)',
       "        if external_policy is not None:\n            if esn or teacher or hybrid_teacher:raise ValueError('External policy must be exclusive')\n            applied=np.asarray(external_policy.act(observation.copy()),dtype=float)\n            if applied.shape!=(7,) or not np.isfinite(applied).all() or np.max(abs(applied))>1.000001:raise ValueError('Invalid external action7')\n            signal.update(applied_action=applied.copy(),baseline_action=applied.copy())\n        interval_peak[:]=0.;interval_impulse[:]=0.\n        env.step(applied)"),
      ("    result['metrics']=metrics.save(",
       "    if external_policy is not None:\n        result['controller']=external_policy.label\n        result['baseline_policy']=external_policy.finish(a.output.parent)\n    result['metrics']=metrics.save(")]
    for old,new in replacements:
        if text.count(old)!=1:raise RuntimeError('Pinned evaluator seam changed: '+old)
        text=text.replace(old,new)
    namespace=dict(__name__='office_baseline_evaluator',__file__=str(source))
    exec(compile(text,str(source)+'[baseline-policy-seam]','exec'),namespace)
    return namespace['run'],text,replacements

class Policy:
    def __init__(self,env,args):
        self.args=args;self.agent=None;self.controller=None;self.actions=[];self.obs=[]
        self.label=args.method+(' '+args.controller if args.controller else '')
        if args.method in ('direct_rl','parameter_rl'):
            if args.checkpoint is None:raise ValueError('RL requires checkpoint')
            state=json.loads((args.checkpoint/'official_agent_state.json').read_text());c=state['config'];utd=state['utd']
            kwargs=dict(seed=c['seed'],total_steps=int(c['learning_rate_decay_step'])//utd,utd=utd,gamma=c['gamma'],entropy_coef=c['temp_target_entropy_coef'],initial_temperature=c['temp_initial_value'])
            if args.method=='direct_rl':
                sys.path.insert(0,str(DIRECT))
                from train import OfficialOfficeAgent
                self.agent=OfficialOfficeAgent(**kwargs)
            else:
                sys.path.insert(0,str(PARAMETER))
                from official_parameter_agent import OfficialParameterAgent
                self.agent=OfficialParameterAgent(**kwargs,action_dimension=c['action_dimension'])
            self.agent.load(args.checkpoint);self.before=self.agent.diagnostics()
        if args.method in ('parameter_fixed','parameter_rl'):
            if not args.controller:raise ValueError('Choose parameter controller')
            sys.path.insert(0,str(PARAMETER))
            from controllers import ParameterController
            prior=json.loads((PARAMETER/'PRIORS.json').read_text())['methods'][args.controller]
            if self.agent and self.agent.config['action_dimension']!=prior['action_dimension']:raise ValueError('Wrong policy dimension')
            self.controller=ParameterController(env,args.controller,prior)
    def act(self,obs):
        self.obs.append(obs.copy())
        if self.controller:
            raw=self.agent.sample_action(obs,training=False) if self.agent else np.zeros(self.controller.prior['action_dimension'])
            action=self.controller.act(obs,raw)
        elif self.agent:action=self.agent.sample_action(obs,training=False)
        else:action=np.zeros(7)
        self.actions.append(np.asarray(action).copy());return action
    def finish(self,out):
        if self.agent and self.agent.diagnostics()!=self.before:raise RuntimeError('Evaluation changed normalizer')
        np.savez_compressed(out/'baseline_policy.npz',observation=np.asarray(self.obs),action=np.asarray(self.actions))
        detail=dict(label=self.label,steps=len(self.actions),normalizers_unchanged=True if self.agent else None,observation='exact evaluator canonical48',training=False)
        if self.controller:detail['parameters']=self.controller.save(out)
        return detail

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--method',choices=['nominal','zero_bridge','direct_rl','parameter_fixed','parameter_rl'],required=True)
    p.add_argument('--controller',choices=['admittance','impedance','vmc'])
    p.add_argument('--checkpoint',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--probe',type=float)
    args=p.parse_args()
    os.environ.setdefault('MUJOCO_MENAGERIE_PATH',str(ASSETS))
    os.environ.setdefault('MUJOCO_GL','egl')
    if any(os.environ.get(k)!='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']):raise RuntimeError('Set single-thread environment')
    import mujoco
    if mujoco.__version__!='3.11.0':raise RuntimeError('MuJoCo 3.11.0 required')
    args.output.mkdir(parents=True,exist_ok=False)
    original=json.loads((REFERENCE/'esn_combined_v4.json').read_text())
    if not original['full_task_horizon_completed']:raise ValueError('Full reference required')
    settings=dict(original['arguments'])
    settings.update(output=args.output/'rollout',esn_model=None,esn_mode='shadow',teacher='none',hybrid_vmc_blend=0.,render=False,impact_slowmo=False,physics_probe_s=args.probe)
    sys.path.insert(0,str(SOURCE/'scripts'))
    run,executed,replacements=build_evaluator()
    upstream={str(f.relative_to(SOURCE)):sha(f) for f in (SOURCE/'scripts').glob('*.py')}
    record=dict(status='running',started_epoch=time.time(),main_commit=MAIN_SHA,source_root=str(SOURCE),upstream_source_sha256=upstream,executed_evaluator_sha256=hashlib.sha256(executed.encode()).hexdigest(),bridge_sha256=sha(__file__),reference_summary_sha256=sha(REFERENCE/'esn_combined_v4.json'),method=args.method,controller=args.controller,checkpoint=str(args.checkpoint) if args.checkpoint else None,probe_s=args.probe,expected_model_sha256=MODEL_SHA,simulation_host='Spark',purpose='interface_diagnostic' if args.probe else 'frozen_primitive_policy_transfer_development',argv=sys.argv)
    if args.checkpoint:record['checkpoint_hashes']={str(f.relative_to(args.checkpoint)):sha(f) for f in args.checkpoint.rglob('*') if f.is_file() and f.name!='replay.npz'}
    dump(args.output/'EXECUTION.json',record)
    (args.output/'executed_evaluator.py.txt').write_text(executed)
    dump(args.output/'SOURCE_PATCH.json',replacements)
    original_save=mujoco.mj_saveModel
    def save(model,filename,buffer):
        result=original_save(model,filename,buffer)
        if sha(filename)!=MODEL_SHA:raise RuntimeError('Exact office model mismatch')
        return result
    mujoco.mj_saveModel=save
    try:
        run(SimpleNamespace(**settings),policy_factory=None if args.method=='nominal' else lambda env:Policy(env,args))
        if any(sha(SOURCE/name)!=h for name,h in upstream.items()):raise RuntimeError('Frozen source changed')
        result=json.loads((args.output/'rollout.json').read_text())
        record.update(status='complete',task_success=result['task_success'],strict_success=result['strict_success'],full_horizon=result['full_task_horizon_completed'],model_sha256=result['model_sha256'])
    except BaseException as exc:
        record.update(status='failed',error=repr(exc));raise
    finally:
        mujoco.mj_saveModel=original_save;record['ended_epoch']=time.time();dump(args.output/'EXECUTION.json',record)
if __name__=='__main__':main()
