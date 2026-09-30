"""Persistent reference rod task inside a solid, slotted workstation guard.

The rear guard has a wrist/forearm access slot; its side wings stop the wider
hand. Every panel is a physical box with the same visual and collision shape.
Audit-only geometry/contact information never enters the VMC action API.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from dataclasses import replace
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.optimize import least_squares
from run_vmc_6d_constrained_push_20260918 import CoreTeacher


ROOT = Path(__file__).resolve().parents[1]
PANEL = json.loads(os.environ.get('PANEL_CONFIG', '{}'))
AUDIT = {}


def panel_geometry():
    """Dimensions are physical inner faces, rather than ambiguous centres."""
    back = float(PANEL.get('back_inner_x', .49))
    front = float(PANEL.get('front_inner_x', .61))
    half_y = float(PANEL.get('half_y', .25))
    bottom = .401
    top = float(PANEL.get('top_z', .91))
    slot_lo = float(PANEL.get('slot_lower_y', -.065))
    slot_hi = float(PANEL.get('slot_upper_y', .065))
    sill = float(PANEL.get('slot_bottom_z', .47))
    thickness = .025
    if not back < front or not -half_y < slot_lo < slot_hi < half_y:
        raise ValueError('Invalid panel configuration')
    boxes = []
    def box(name, lo, hi):
        lo, hi = np.asarray(lo), np.asarray(hi)
        if np.any(hi <= lo):
            raise ValueError(name)
        boxes.append(dict(name=name, position=((lo+hi)/2).tolist(),
                          half_size=((hi-lo)/2).tolist()))
    if PANEL.get('layout') == 'raised_hand_rim':
        # Opposed local plates cover the broad negative-y hand rim across
        # the rod-sliding height. The forearm keeps its central passage.
        # These are ordinary solid boxes, not collision masks or joint locks.
        lo=float(PANEL.get('pad_bottom_z',.55));hi=float(PANEL.get('pad_top_z',.71))
        ylo=float(PANEL.get('pad_lower_y',-.15));yhi=float(PANEL.get('pad_upper_y',-.085))
        thick=float(PANEL.get('pad_thickness',.015))
        box('push_back_guard',[back-thick,ylo,lo],[back,yhi,hi])
        box('push_front_guard',[front,ylo,lo],[front+thick,yhi,hi])
        return boxes
    if PANEL.get('layout') == 'compact_end_effector':
        # Local pads at gripper height. No tall forearm enclosure or slots;
        # the rod is above the pads and can enter without intersecting them.
        lo = float(PANEL.get('pad_bottom_z', .49))
        hi = float(PANEL.get('pad_top_z', .58))
        width = float(PANEL.get('pad_half_y', .12))
        thick = float(PANEL.get('pad_thickness', .015))
        box('push_back_guard', [back-thick, -width, lo], [back, width, hi])
        box('push_front_guard', [front, -width, lo], [front+thick, width, hi])
        return boxes
    # The oblique rod approaches from +y. Its drive must not be stopped by
    # the guard itself: provide a local inlet in the far edge of the panel.
    # The hand lane (y < .08) remains bounded over the entire task height.
    inlet_y = .08
    inlet_bottom, inlet_top = .62, .68
    box('push_front_guard', [front, -half_y, bottom], [front+thickness, inlet_y, top])
    box('push_front_guard_below_inlet', [front, inlet_y, bottom], [front+thickness, half_y, inlet_bottom])
    box('push_front_guard_above_inlet', [front, inlet_y, inlet_top], [front+thickness, half_y, top])
    box('push_back_guard_negative', [back-thickness, -half_y, bottom], [back, slot_lo, top])
    box('push_back_guard_positive', [back-thickness, slot_hi, bottom], [back, half_y, top])
    box('push_back_guard_sill', [back-thickness, slot_lo, bottom], [back, slot_hi, sill])
    return boxes


def main():
    source = Path(os.environ.get(
        'PRIMITIVE_RUNNER_PATH',
        str(Path(__file__).with_name('run_primitive_teacher_v7_20260917.py')),
    )).resolve()
    spec = importlib.util.spec_from_file_location('panel_primitive', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ContactMemoryVMC = CoreTeacher
    extend = module.extend_xml
    boxes = panel_geometry() if os.environ.get('PANELS_ENABLED', '1') == '1' else []
    unified = os.environ.get('UNIFIED_6D_TEACHER', '0') == '1'

    def extend_scene(xml, scene):
        root = ET.fromstring(extend(xml, scene))
        world = root.find('worldbody')
        active_boxes = boxes if getattr(scene, 'kind', None) == 'push' else []
        for b in active_boxes:
            ET.SubElement(world, 'geom', dict(name=b['name'], type='box',
                pos=' '.join(map(str,b['position'])), size=' '.join(map(str,b['half_size'])),
                rgba='.24 .43 .60 1', contype='32', conaffinity='63',
                friction='.35 .01 .001', solref='.0015 1', solimp='.95 .995 .0002 .5 2', priority='3'))
        if PANEL.get('workstation',False) and getattr(scene, 'kind', None) == 'push':
            from workstation_scene_20260920 import add_workstation
            add_workstation(root,scene,active_boxes)
        return ET.tostring(root, encoding='unicode')
    module.extend_xml = extend_scene

    base_env = module.PandaWBCVelocityResidualEnv
    class AuditEnv(base_env):
        @property
        def substep_observer(self):
            return getattr(self, '_panel_observer', None)

        @substep_observer.setter
        def substep_observer(self, callback):
            if callback is None:
                self._panel_observer = None
                return
            def observe(t):
                callback(t)
                m,d = self.model,self.data
                seen = set()
                force_sums={};magnitude_sums={}
                for i in range(d.ncon):
                    c = d.contact[i]
                    g1,g2 = int(c.geom1),int(c.geom2)
                    other = g2 if g1 in self._push_audit_robot_geom_ids else g1 if g2 in self._push_audit_robot_geom_ids else -1
                    if other not in self.audit_obstacles:
                        continue
                    name = self.audit_obstacles[other]
                    robot_g = g1 if other == g2 else g2
                    row = self.contact_stats[name]
                    f = np.zeros(6)
                    mujoco.mj_contactForce(m,d,i,f)
                    mag = float(np.linalg.norm(f[:3]))
                    world=c.frame.reshape(3,3).T@f[:3]
                    if g2==other:world=-world
                    force_sums[name]=force_sums.get(name,np.zeros(3))+world
                    magnitude_sums[name]=magnitude_sums.get(name,0.)+mag
                    self.interval_peaks[name] = max(self.interval_peaks.get(name,0.),mag)
                    row['peak_point_force_n'] = max(row['peak_point_force_n'],mag)
                    row['max_penetration_m'] = max(row['max_penetration_m'],-float(c.dist))
                    if mag > .05:
                        row['last_s'] = float(d.time)
                        if row['first_s'] is None: row['first_s'] = float(d.time)
                        row['bodies'].add(mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[robot_g])))
                        seen.add(name)
                for name in seen:
                    self.contact_stats[name]['duration_s'] += m.opt.timestep
                for name,force in force_sums.items():
                    row=self.contact_stats[name];norm=float(np.linalg.norm(force));total=magnitude_sums[name]
                    row['peak_resultant_force_n']=max(row['peak_resultant_force_n'],norm)
                    row['peak_sum_point_force_n']=max(row['peak_sum_point_force_n'],total)
                    row['resultant_impulse_ns']+=norm*m.opt.timestep
                    row['sum_point_impulse_ns']+=total*m.opt.timestep
            self._panel_observer = observe

        def step(self, action):
            before={k:v['duration_s'] for k,v in self.contact_stats.items()}
            self.interval_peaks={}
            result = super().step(action)
            d = self.data
            self.state_trace.append(np.r_[d.time, d.qpos.copy(), d.qvel.copy(), d.ctrl.copy()])
            self.contact_samples.append([float(d.time)]+[value for name in self.contact_stats
                for value in (self.contact_stats[name]['duration_s']-before[name],self.interval_peaks.get(name,0.))])
            if PANEL.get('workstation') and len(self.state_trace)%100==0:
                print(json.dumps(dict(sim_time_s=float(d.time),stage=int(self.reference.index),hand=d.xpos[self._hand_id].tolist())),flush=True)
            return result

        def close(self):
            if hasattr(self,'contact_stats'):
                AUDIT['contacts'] = {k:{**v,'bodies':sorted(v['bodies'])} for k,v in self.contact_stats.items()}
                AUDIT['trace'] = self.state_trace
                AUDIT['contact_samples']=self.contact_samples
                AUDIT['contact_names']=list(self.contact_stats)
                AUDIT['nq'],AUDIT['nv'],AUDIT['nu'] = self.model.nq,self.model.nv,self.model.nu
                d,m = self.data,self.model
                has_rod = self._push_rod_qpos >= 0 and self._push_rod_ctrl >= 0
                AUDIT['final_rod_position_m'] = float(d.qpos[self._push_rod_qpos]) if has_rod else None
                AUDIT['final_rod_command_m'] = float(d.ctrl[self._push_rod_ctrl]) if has_rod else None
                AUDIT['final_hand_position_m'] = d.xpos[self._hand_id].tolist()
                target_geoms={g for g in range(m.ngeom) if int(m.geom_bodyid[g])==self._target_body_id}
                fingers=set()
                for c in d.contact[:d.ncon]:
                    pair=[int(c.geom1),int(c.geom2)]
                    if any(g in target_geoms for g in pair):
                        other=pair[1] if pair[0] in target_geoms else pair[0]
                        body=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[other]))
                        if body in ('left_finger','right_finger'):fingers.add(body)
                AUDIT['final_bilateral_grasp']=len(fingers)==2
                if self._push_rod_geom_id >= 0:
                    flags=int(m.opt.disableflags)
                    try:
                        m.opt.disableflags=flags & ~int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)
                        AUDIT['final_rod_gap_m'] = min(float(mujoco.mj_geomDistance(m,d,self._push_rod_geom_id,g,.2,None)) for g in self._push_audit_robot_geom_ids if m.geom_contype[g])
                    finally:
                        m.opt.disableflags=flags
                else:
                    AUDIT['final_rod_gap_m'] = None
            super().close()
    module.PandaWBCVelocityResidualEnv = AuditEnv
    create = module.create_environment
    update = module.BlindTask.update

    def passage(self,qpos,qvel,position,rotation,twist):
        delta = position-self.goals[self.index]
        if os.environ.get('UNIFIED_TEACHER_SCENE') == 'push' and self.index == 0 and delta@self.path_direction > -.012 and np.linalg.norm(delta)<.12 and np.linalg.norm(twist[:3])<.18:
            self.previous_goal=self.goals[0].copy();self.index=1;self.ready=0
            self.path_direction=self.direction()
            return True
        return update(self,qpos,qvel,position,rotation,twist)
    module.BlindTask.update = passage

    def environment(args):
        if args.scene == 'push' and PANEL.get('end_effector_only', True):
            args.push_height=float(PANEL.get('rod_height_m', .600))
        env, task, scene = create(args)
        m,d = env.model,env.data
        if PANEL.get('native_ccd',False):
            m.opt.disableflags=int(m.opt.disableflags) & ~int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)
            mujoco.mj_forward(m,d)
        AUDIT['native_ccd_enabled']=not bool(int(m.opt.disableflags)&int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD))
        if args.scene == 'push':
            task.goals=task.goals[:4];task.names=task.names[:4]
            task.goals[3]=task.goals[3].copy();task.goals[3][2]=float(PANEL.get('lift_goal_z',.785))
            if 'lift_goal_x' in PANEL:task.goals[3][0]=float(PANEL['lift_goal_x'])
            command=env._wbc_command
            def scaled(*values,**kwargs):
                cmd=command(*values,**kwargs)
                return replace(cmd,joint_velocity_radps=cmd.joint_velocity_radps*.8,task_twist_world=cmd.task_twist_world*.8) if task.index>=3 else cmd
            env._wbc_command=scaled
        env.state_trace=[];env.contact_samples=[];env.interval_peaks={}
        env.audit_obstacles={g:(mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) or f'geom_{g}') for g in range(m.ngeom)
            if g not in env._push_audit_robot_geom_ids and (m.geom_contype[g] or m.geom_conaffinity[g])}
        env.contact_stats={name:dict(first_s=None,last_s=None,duration_s=0.,peak_point_force_n=0.,max_penetration_m=0.,bodies=set(),
            peak_resultant_force_n=0.,peak_sum_point_force_n=0.,resultant_impulse_ns=0.,sum_point_impulse_ns=0.) for name in env.audit_obstacles.values()}
        guards={g for g,n in env.audit_obstacles.items() if n.startswith(('push_front_guard','push_back_guard','ws_'))}
        overlaps=[]
        for i in range(d.ncon):
            c=d.contact[i]
            if (int(c.geom1) in guards or int(c.geom2) in guards) and c.dist < -1e-6:
                overlaps.append(dict(pair=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,int(g)) for g in (c.geom1,c.geom2)],depth=-float(c.dist)))
        AUDIT['initial_overlap']=overlaps
        AUDIT['physical_panels']=[dict(name=b['name'],position_m=m.geom_pos[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,b['name'])].tolist(),half_size_m=m.geom_size[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,b['name'])].tolist()) for b in boxes if mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,b['name']) >= 0]
        if overlaps:
            raise ValueError('Initial panel overlap: '+json.dumps(overlaps))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        cache_root=os.environ.get('VMC_MODEL_CACHE_DIR')
        if os.environ.get('SKIP_MODEL_ARCHIVE') == '1':
            pass
        elif cache_root:
            import fcntl
            cache_key=os.environ['VMC_MODEL_CACHE_KEY']
            if len(cache_key)!=64 or any(c not in '0123456789abcdef' for c in cache_key):
                raise ValueError('Expected a SHA-256 model cache key')
            cache=Path(cache_root);cache.mkdir(parents=True,exist_ok=True)
            cached=cache/(cache_key+'.mjb')
            with (cache/(cache_key+'.lock')).open('a+') as cache_lock:
                fcntl.flock(cache_lock,fcntl.LOCK_EX)
                if not cached.exists():
                    temp=cache/(cache_key+f'.{os.getpid()}.tmp')
                    mujoco.mj_saveModel(m,str(temp),None);os.replace(temp,cached)
            link=args.output.with_suffix(f'.mjb.{os.getpid()}.link')
            os.link(cached,link);os.replace(link,args.output.with_suffix('.mjb'))
        else:
            mujoco.mj_saveModel(m,str(args.output.with_suffix('.mjb')),None)
        # Offline counterfactual: test x translations of the reference grasp
        # pose, preserving orientation. This diagnostic is never executed by
        # the controller and never mutates its live simulation state.
        probe=mujoco.MjData(m);probe.qpos[:]=d.qpos
        seed=d.qpos[:7].copy();base=d.xpos[env._hand_id].copy();rot=d.xmat[env._hand_id].reshape(3,3).copy()
        rows=[]
        for dz in (0.,-.12,.12):
            for dx in (-.06,0.,.06):
                target=base+np.array([dx,0,dz])
                def residual(q):
                    probe.qpos[:7]=q;mujoco.mj_forward(m,probe)
                    return np.r_[probe.xpos[env._hand_id]-target,.08*(probe.xmat[env._hand_id].reshape(3,3)-rot).ravel(),.0001*(q-seed)]
                fit=least_squares(residual,seed,bounds=(m.jnt_range[:7,0],m.jnt_range[:7,1]),max_nfev=400)
                residual(fit.x);pairs=[]
                for i in range(probe.ncon):
                    c=probe.contact[i]
                    if (int(c.geom1) in guards or int(c.geom2) in guards) and c.dist<-.00001:
                        pairs.append(dict(pair=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,int(g)) for g in (c.geom1,c.geom2)],depth_m=-float(c.dist)))
                rows.append(dict(dx_m=dx,dz_m=dz,ik_error_m=float(np.linalg.norm(probe.xpos[env._hand_id]-target)),blocked=bool(pairs),pairs=pairs))
        AUDIT['offline_translation_probes']=rows
        if os.environ.get('PANEL_AUDIT_ONLY')=='1':
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.with_suffix('.geometry.json').write_text(json.dumps(AUDIT,indent=2))
            print(json.dumps(AUDIT),flush=True)
            raise SystemExit(0)
        return env,task,scene
    module.create_environment=environment
    text=source.read_text()
    substitutions={
        'teacher_force=teacher_force_sensor.copy() if a.teacher_force_source=="ideal" else wrench[:3]':'teacher_force=wrench.copy()',
        'from contact_transfer_student_20260916 import TransferStudent':'from current_student_policy_20260921 import load_current',
        'policy=TransferStudent.load(a.model)':'policy=load_current(a.model)',
        'expert=teacher.act(teacher_force,error[:3],twist[:3],task.path_direction,RL_DT)':'expert=teacher.act(teacher_force,error,twist,task.path_direction,RL_DT)',
        '"office_cup","office_pillar"))':'"office_cup","office_pillar","push_front_guard","push_back_guard","ws_"))',
        'close_cam.lookat[:]=[.55,-.01,.56];close_cam.distance=.78;close_cam.azimuth=140;close_cam.elevation=-12':'close_cam.lookat[:]=[.54,0.,.65];close_cam.distance=1.05;close_cam.azimuth=90;close_cam.elevation=-12',
    }
    if unified:
        substitutions.update({
            'observer.filtered,wrench[:3],task.path_direction]':'observer.filtered,wrench,task.path_direction]',
            'contract="contact45_v2"':'contract="proprio48_action7_6d_v1"',
            'estimated_force3,commanded_path_direction3':'estimated_wrench6,commanded_path_direction3',
        })
    for old,new in substitutions.items():
        if old in text:
            text=text.replace(old,new)
        elif old=='from contact_transfer_student_20260916 import TransferStudent' and 'from current_student_policy_20260921 import load_current' in text:
            pass
        elif old=='policy=TransferStudent.load(a.model)' and 'policy=load_current(a.model)' in text:
            pass
        else:
            raise RuntimeError('Runner contract changed: '+old)
    run_node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='run')
    exec(compile(ast.Module(body=[run_node],type_ignores=[]),str(source),'exec'),module.__dict__)
    run=module.run
    def audited_run(args):
        if args.teacher_force_source!='estimated' or args.teacher_profile!='memory':
            raise ValueError('Requires proprioceptive estimated-wrench input and the 6-D VMC profile')
        if not unified and args.scene!='push':
            raise ValueError('The legacy panel runner only supports push; set UNIFIED_6D_TEACHER=1 for audited primitive collection')
        os.environ['UNIFIED_TEACHER_SCENE']=args.scene
        run(args)
        trace=AUDIT.pop('trace')
        contact_samples=AUDIT.pop('contact_samples')
        np.savez_compressed(args.output.with_name('contact_samples.npz'),samples=np.asarray(contact_samples),names=np.asarray(AUDIT['contact_names']))
        np.savez_compressed(args.output.with_name('physics_states.npz'),state=np.asarray(trace),nq=AUDIT['nq'],nv=AUDIT['nv'],nu=AUDIT['nu'])
        result=json.loads(args.output.with_suffix('.json').read_text())
        result['panel_audit']=AUDIT
        if args.scene == 'push':
            rod=AUDIT['contacts']['push_rod_geom']
            result['accepted_panel_demo']=bool(result['success'] and rod['duration_s']>.3
                and rod['last_s'] is not None and args.duration-rod['last_s']>2.
                and AUDIT['final_rod_gap_m']>.002
                and max(c['max_penetration_m'] for n,c in AUDIT['contacts'].items() if n!='target_object_geom')<.0002
                and not (set(rod['bodies']) & {'fr3_link0','fr3_link1','fr3_link2','fr3_link3','fr3_link4'}))
        result['accepted_unified_teacher']=bool(result['success'] and result['real_contact']
            and not result['invalid_physics'] and not result.get('upstream_contact',False))
        result['controller_6d_config']=json.loads(os.environ.get('CORE_VMC_CONFIG','{}'))
        result['experiment_contract']=dict(reference='unified_6d_vmc_teacher_20260921' if unified else 'loaded_push_release_20260918',
            observation='48D proprioception including encoder-derived 6D wrench' if unified else 'legacy 45D observation',
            persistent_rod=args.push_hold>args.duration if args.scene=='push' else None,
            lift_goal_z_m=float(PANEL.get('lift_goal_z',.785)) if args.scene=='push' else None,
            lift_nominal_scale=.8 if args.scene=='push' else 1.,panel_config=PANEL if args.scene=='push' else {})
        result['source_sha256'][Path(__file__).name]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        result['source_sha256']['run_vmc_6d_constrained_push_20260918.py']=hashlib.sha256(Path(__file__).with_name('run_vmc_6d_constrained_push_20260918.py').read_bytes()).hexdigest()
        if PANEL.get('workstation',False):
            result['source_sha256']['workstation_scene_20260920.py']=hashlib.sha256(Path(__file__).with_name('workstation_scene_20260920.py').read_bytes()).hexdigest()
        args.output.with_suffix('.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(dict(success=result['success'],panel_audit=AUDIT)),flush=True)
    module.run=audited_run
    tree=ast.parse(source.read_text())
    exec(compile(ast.Module(body=tree.body[-1].body,type_ignores=[]),str(source),'exec'),module.__dict__)


if __name__=='__main__':main()
