"""Offline static-map A* reference planning; no online obstacle input to actor."""
import heapq
import itertools
import numpy as np
import mujoco
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from office_task_v4_20260917 import PickPlaceTask, DT
from run_benchmark import so3_log

DESTINATION = np.array([.690, -.310, .545])
OFFSET = np.array([0., 0., .1029])
DOWN = np.diag([-1., 1., -1.])


def astar(start, goal, boxes, half, ignore=()):
    """26-connected payload-center grid, swept edges and deterministic ties."""
    start, goal = np.asarray(start), np.asarray(goal)
    step = .01
    origin = np.minimum(start, goal) - [.10, .10, .03]
    upper = np.maximum(start, goal) + [.10, .10, .10]
    dims = np.ceil((upper-origin)/step).astype(int)
    def free(p):
        return all(name in ignore or not np.all(np.abs(p-center) < extent+half+.002-1e-8)
                   for name, center, extent in boxes)
    def edge(a, b):
        return all(free(p) for p in np.linspace(a, b, max(2, int(np.ceil(np.linalg.norm(a-b)/.002))+1)))
    if not free(start) or not free(goal):
        raise ValueError('Planner endpoint intersects inflated static map')
    if edge(start, goal):
        return [start, goal], 0
    key = lambda p: tuple(np.rint((p-origin)/step).astype(int))
    position = lambda k: origin+np.array(k)*step
    s = key(start)
    if not edge(start, position(s)):
        raise ValueError('Start-to-grid connector is blocked')
    queue = [(float(np.linalg.norm(position(s)-goal)), 0., s)]
    cost, parent = {s: 0.}, {s: None}
    neighbors = [np.array(x) for x in itertools.product((-1, 0, 1), repeat=3) if any(x)]
    expanded = 0
    while queue and expanded < 40000:
        _, g, k = heapq.heappop(queue)
        if g > cost[k]+1e-12:
            continue
        p = position(k); expanded += 1
        if np.linalg.norm(p-goal) < .018 and edge(p, goal):
            path = [goal, p]
            while parent[k] is not None:
                k = parent[k]; path.append(position(k))
            path.append(start); path.reverse()
            return path, expanded
        for delta in neighbors:
            nxt = tuple(np.array(k)+delta)
            if np.any(np.array(nxt)<0) or np.any(np.array(nxt)>dims):
                continue
            q = position(nxt)
            ng = g+float(np.linalg.norm(q-p))
            if ng < cost.get(nxt, float('inf')) and edge(p,q):
                cost[nxt] = ng; parent[nxt] = k
                heapq.heappush(queue,(ng+float(np.linalg.norm(q-goal)),ng,nxt))
    raise ValueError('Static-map A* found no route within budget')


def densify(path, spacing=.01):
    out = [np.asarray(path[0])]
    for a,b in zip(path,path[1:]):
        out.extend(np.linspace(a,b,max(2,int(np.ceil(np.linalg.norm(b-a)/spacing))+1))[1:])
    return out


class PlannedCornerTask(PickPlaceTask):
    def __init__(self, base, routes):
        self.__dict__.update(base.__dict__)
        self.routes = routes
        self.cursors = {stage: 0 for stage in routes}
        for stage, route in routes.items():
            self.goals[stage] = route[0][0].copy()
        self.corner_release_ok = False

    def update(self, q, dq, pos, rot, twist, wrench):
        route = self.routes.get(self.index)
        if route:
            cursor = self.cursors[self.index]
            self.rotation = route[cursor][1].copy()
            if cursor < len(route)-1:
                if np.linalg.norm(pos-self.goals[self.index]) < .012 and np.linalg.norm(so3_log(self.rotation@rot.T)) < .12:
                    previous = self.goals[self.index].copy()
                    self.cursors[self.index] += 1
                    waypoint, rotation = route[cursor+1]
                    self.goals[self.index] = waypoint.copy()
                    self.rotation = rotation.copy()
                    delta = waypoint-previous
                    self.path_direction = delta/max(np.linalg.norm(delta),1e-8)
                self.ready = 0.
                return False
        if self.index == 5:
            # Known target + measured robot pose only. Physical payload support
            # and release are checked independently by the evaluator.
            error = pos-self.goals[5]
            ready = (np.linalg.norm(error[:2]) < .025 and abs(error[2]) < .012
                     and np.linalg.norm(so3_log(self.rotation@rot.T)) < .12
                     and np.linalg.norm(twist[:3]) < .025)
            self.ready = self.ready+DT if ready else 0.
            if self.ready >= .20-1e-9:
                self.previous_goal = self.goals[5].copy()
                self.index = 6; self.ready = 0.
                self.goals[6] = self.goals[5].copy()
                self.path_direction = self.direction()
                return True
            return False
        advanced = super().update(q,dq,pos,rot,twist,wrench)
        if advanced and self.index in self.routes:
            self.rotation = self.routes[self.index][0][1].copy()
        return advanced


def build_plan(env, base):
    m, d = env.model, env.data
    scratch = mujoco.MjData(m)
    scratch.qpos[:] = d.qpos
    hand = env._hand_id
    qseed = d.qpos[:7].copy()
    static = {i for i in range(m.ngeom) if m.geom_bodyid[i] == 0 and (m.geom_contype[i] or m.geom_conaffinity[i])}
    boxes = []
    for i in sorted(static):
        name = mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,i) or str(i)
        if name == 'office_floor':
            continue
        rot = d.geom_xmat[i].reshape(3,3)
        center = d.geom_xpos[i]+rot@m.geom_aabb[i,:3]
        boxes.append((name,center,abs(rot)@m.geom_aabb[i,3:]))
    robot = set(env._push_audit_robot_geom_ids)
    fingers = base.fingers
    def ik(pos, rotation, seed):
        scratch.qpos[:] = d.qpos
        scratch.qpos[fingers] = .025
        def residual(q):
            scratch.qpos[:7] = q
            mujoco.mj_forward(m,scratch)
            return np.r_[scratch.xpos[hand]-pos,.1*(scratch.xmat[hand].reshape(3,3)-rotation).ravel(),.00001*(q-seed)]
        sol = least_squares(residual,seed,bounds=(m.jnt_range[:7,0]+1e-5,m.jnt_range[:7,1]-1e-5),max_nfev=300)
        residual(sol.x)
        pe = float(np.linalg.norm(scratch.xpos[hand]-pos))
        re = float(np.linalg.norm(so3_log(rotation@scratch.xmat[hand].reshape(3,3).T)))
        collisions = []
        for c in scratch.contact:
            g1,g2 = int(c.geom1),int(c.geom2)
            if c.dist < -.00001 and ((g1 in robot and g2 in static) or (g2 in robot and g1 in static)):
                collisions.append([mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) for g in (g1,g2)])
        return sol.x, pe, re, collisions

    candidates=[]
    selected=None
    for tilt in (0,-5,-10,-15,-20,-25,-30,-35):
        payload_rotation = Rotation.from_euler('y',tilt,degrees=True).as_matrix()
        rotation = payload_rotation@DOWN
        half = abs(payload_rotation)@np.full(3,.025)
        payload = np.r_[DESTINATION[:2], .520+half[2]]
        release = payload-rotation@OFFSET
        approach = release+np.array([0.,0.,.025])
        results=[ik(p,rotation,qseed) for p in (release,approach)]
        valid=all(pe<.002 and re<.02 and not hits for _,pe,re,hits in results)
        candidates.append(dict(tilt_degrees=tilt,valid=valid,checks=[dict(position_error_m=pe,rotation_error_rad=re,collisions=hits) for _,pe,re,hits in results]))
        if valid:
            selected=(tilt,rotation,payload,half,release,approach); break
    if selected is None:
        raise ValueError(f'No reachable collision-free corner placement posture: {candidates}')
    tilt, rotation, payload, half, release, approach = selected
    lift_hand = base.goals[3].copy()
    lift_payload = lift_hand+DOWN@OFFSET
    # Raise until the rotated payload clears the tabletop by at least 5mm.
    lift_payload[2] = max(lift_payload[2],.520+half[2]+.005)
    lift_hand = lift_payload-DOWN@OFFSET
    carry_payload = approach+rotation@OFFSET
    path, expanded = astar(lift_payload,carry_payload,boxes,half)
    rotations=[Rotation.from_euler('y',a,degrees=True).as_matrix()@DOWN for a in np.linspace(0,tilt,int(abs(tilt)/5)+1)]
    carry=[(lift_payload-r@OFFSET,r) for r in rotations]
    carry += [(p-rotation@OFFSET,rotation) for p in densify(path)[1:]]
    # Only the intended support slab is exempt on final descent, which ends
    # at the analytic touching pose. Other obstacles remain collision checked.
    descent, _ = astar(carry_payload,payload,boxes,half,ignore=('office_v5_corner_top',))
    routes={3:[(lift_hand,DOWN)],4:carry,
            5:[(p-rotation@OFFSET,rotation) for p in densify(descent)],
            7:[(p,rotation) for p in densify([release,approach])]}
    checks=[]; seed=qseed
    for stage, route in routes.items():
        for pos,rot in route:
            seed,pe,re,hits=ik(pos,rot,seed)
            checks.append(dict(stage=stage,position_error_m=pe,rotation_error_rad=re,collisions=hits))
            if pe>.002 or re>.02 or hits:
                raise ValueError(f'Nominal waypoint IK/static collision check failed: {checks[-1]}')
    base.destination=DESTINATION.copy()
    task=PlannedCornerTask(base,routes)
    metadata=dict(planner='deterministic static-map A* with direct swept-edge shortcut and IK posture search',
                  grid_m=.01,edge_sample_m=.002,expanded=expanded,tilt_degrees=tilt,
                  destination=DESTINATION.tolist(),target_xy_radius_m=.025,
                  planned_release_hand=release.tolist(),planned_payload_touch=payload.tolist(),
                  candidates=candidates,waypoint_checks=checks,
                  routes={str(k):[dict(hand=p.tolist(),rotation=r.tolist()) for p,r in v] for k,v in routes.items()},
                  static_map_only=True,dynamic_obstacle_state_in_planner=False,
                  limitations='Payload swept-volume and robot waypoint static checks; not a continuous full-arm collision proof or dynamic-contact prediction')
    return task,metadata
