"""Offline hand STL/recorded-qpos clearance bounds; no MuJoCo dependency."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from teacher_bank_corner_trace_20260930 import rotation
from teacher_bank_design_20260930 import sha, write


def axis_rotation(axis, angle):
    v=np.asarray(axis,dtype=float);v/=np.linalg.norm(v)
    cross=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+np.sin(angle)*cross+(1-np.cos(angle))*(cross@cross)


def clip_xy(polygon, box):
    """Clip a 3D polygon against four vertical planes, preserving surface z."""
    for axis, boundary, sign in ((0,box[0],1),(0,box[1],-1),(1,box[2],1),(1,box[3],-1)):
        if not len(polygon):break
        clipped=[]
        for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
            da=sign*(a[axis]-boundary);db=sign*(b[axis]-boundary)
            if da>=0:clipped.append(a)
            if (da>=0)!=(db>=0):clipped.append(a+(b-a)*(da/(da-db)))
        polygon=np.asarray(clipped)
    return polygon


def analyze(folder, obstacle_box, exact_convex=False, include_grasp=False, checked_stages=None,
            body_name='hand', mesh_name='hand_c'):
    folder=Path(folder);root=ET.parse(folder/'rollout.xml').getroot();world=root.find('worldbody')
    addresses={};address=0
    for node in world.iter():
        if node.tag in ('joint','freejoint'):
            addresses[node.get('name')]=address
            kind=node.get('type','free' if node.tag=='freejoint' else 'hinge')
            address+=7 if kind=='free' else 4 if kind=='ball' else 1
    def find_path(node, path):
        if node.get('name')==body_name:return path+[node]
        for child in node.findall('body'):
            found=find_path(child,path+[node])
            if found:return found
        return None
    path=find_path(world,[])[1:]
    stl=Path(root.find(f".//asset/mesh[@name='{mesh_name}']").get('file'))
    if not stl.is_absolute():stl=Path(root.find('compiler').get('meshdir'))/stl
    raw=stl.read_bytes();n=int(np.frombuffer(raw,dtype='<u4',count=1,offset=80)[0])
    dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
    if len(raw)!=84+50*n:raise ValueError('Expected binary STL')
    triangles=np.frombuffer(raw,dtype=dtype,count=n,offset=84)['vertices'].astype(float)
    if exact_convex:
        from scipy.spatial import ConvexHull
        vertices=np.unique(triangles.reshape(-1,3),axis=0)
        hull=ConvexHull(vertices);triangles=vertices[hull.simplices]
    lows=[];highs=[];times=[];position_error=[];exact_lows=[];exact_times=[];exact_bounds=[]
    with np.load(folder/'rollout.npz',allow_pickle=False) as data:
        stages=tuple(checked_stages) if checked_stages is not None else (1,2) if include_grasp else (1,)
        for i in np.flatnonzero(np.isin(data['stage'],stages)):
            position=np.zeros(3);rot=np.eye(3)
            for body in path:
                pos=np.fromstring(body.get('pos','0 0 0'),sep=' ')
                local=rotation(np.fromstring(body.get('quat','1 0 0 0'),sep=' '))
                for joint in body.findall('joint'):
                    kind=joint.get('type','hinge');q=float(data['qpos'][i,addresses[joint.get('name')]])
                    axis=np.fromstring(joint.get('axis','0 0 1'),sep=' ')
                    if kind=='hinge':
                        turn=axis_rotation(axis,q)
                        pivot=np.fromstring(joint.get('pos','0 0 0'),sep=' ')
                        pos+=local@(pivot-turn@pivot);local=local@turn
                    elif kind=='slide':pos+=local@axis*q
                    else:raise ValueError('Unexpected hand-chain joint')
                position=position+rot@pos;rot=rot@local
            if body_name=='hand':position_error.append(float(np.linalg.norm(position-data['hand'][i])))
            points=triangles@rot.T+position
            low=points.min(axis=1);high=points.max(axis=1)
            relevant=(high[:,0]>=obstacle_box[0])&(low[:,0]<=obstacle_box[1])&(
                high[:,1]>=obstacle_box[2])&(low[:,1]<=obstacle_box[3])
            if np.any(relevant):
                lows.append(float(low[relevant,2].min()));highs.append(float(high[relevant,2].max()))
                times.append(float(data['time'][i]))
                if exact_convex:
                    clipped=[clip_xy(triangle,obstacle_box) for triangle in points[relevant]]
                    clipped=[polygon for polygon in clipped if len(polygon)]
                    if clipped:
                        bottom=min(float(polygon[:,2].min()) for polygon in clipped)
                        top=max(float(polygon[:,2].max()) for polygon in clipped)
                        exact_lows.append(bottom)
                        exact_times.append(float(data['time'][i]))
                        exact_bounds.append([float(data['time'][i]),int(data['stage'][i]),bottom,top])
        if position_error and max(position_error)>1e-4:raise ValueError('Offline FK does not match recorded hand')
        result=dict(folder=str(folder),input_sha256={name:sha(folder/name) for name in ('rollout.xml','rollout.npz')},
            mesh_sha256=sha(stl),body_name=body_name,mesh_name=mesh_name,hand_mesh_local_min=triangles.min(axis=(0,1)).tolist(),
            hand_mesh_local_max=triangles.max(axis=(0,1)).tolist(),xy_box=list(obstacle_box),
            fk_vs_record_max_error_m=max(position_error) if position_error else None,align_saved_frames=int(np.sum(data['stage']==1)),
            checked_stages=stages,exact_convex=exact_convex,
            broad_phase_xy_overlapping_frames=len(times),
            minimum_triangle_aabb_lower_z_m=min(lows) if lows else None,
            minimum_lower_z_time_s=times[int(np.argmin(lows))] if lows else None,
            last_triangle_aabb_lower_z_m=lows[-1] if lows else None,
            last_hand=data['hand'][-1].tolist(),last_payload=data['object_position'][-1].tolist(),
            meaning='Triangle AABB conservative bound, not exact mesh collision or dynamic success.')
        if exact_convex:
            by_stage={}
            for stage in stages:
                rows=np.asarray([row for row in exact_bounds if row[1]==stage])
                if len(rows):
                    by_stage[str(stage)]=dict(minimum_lower_z_m=float(rows[:,2].min()),
                        maximum_upper_z_m=float(rows[:,3].max()),first_bound=rows[0].tolist(),last_bound=rows[-1].tolist())
            result.update(minimum_clipped_convex_lower_z_m=min(exact_lows) if exact_lows else None,
                          minimum_clipped_convex_time_s=exact_times[int(np.argmin(exact_lows))] if exact_lows else None,
                          clipped_convex_by_stage=by_stage,
                          convex_note='Exact XY clipping of offline scipy convex-hull facets, not a MuJoCo collision replay.')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--xy-box',default='.493,.519,-.199,-.178')
    parser.add_argument('--exact-convex',action='store_true')
    parser.add_argument('--include-grasp',action='store_true')
    parser.add_argument('--stages',default=None)
    parser.add_argument('--body-name',default='hand');parser.add_argument('--mesh-name',default='hand_c')
    args=parser.parse_args()
    if args.output.exists():raise RuntimeError('Preserve previous analysis')
    result=analyze(args.folder,[float(x) for x in args.xy_box.split(',')],args.exact_convex,args.include_grasp,
                   [int(x) for x in args.stages.split(',')] if args.stages else None,args.body_name,args.mesh_name);write(args.output,result)
    import json
    print(json.dumps(result,indent=2))
