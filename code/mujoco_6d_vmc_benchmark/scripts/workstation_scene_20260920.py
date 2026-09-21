"""Physical open picking fixture and a guided, force-limited pusher.

Visible solid components are ordinary MuJoCo collision geoms. The accepted
hand-rim faces remain unchanged. No fixture geometry is a controller input.
"""
import math
import xml.etree.ElementTree as ET
import numpy as np


def add_workstation(root, scene, panels):
    world=root.find('worldbody')
    def geom(parent,name,pos,size,color,kind='box',**extra):
        attr=dict(name=name,type=kind,pos=' '.join(map(str,pos)),size=' '.join(map(str,size)),
            rgba=' '.join(map(str,color)),contype='32',conaffinity='63',
            friction='.45 .01 .001',solref='.0015 1',solimp='.95 .995 .0002 .5 2',priority='3')
        attr.update(extra);return ET.SubElement(parent,'geom',attr)
    steel=[.36,.40,.44,1];blue=[.15,.35,.48,1];dark=[.12,.15,.17,1];orange=[.85,.46,.12,1]
    # Each local guard is mechanically attached to the work surface by a
    # narrow pedestal at its outer y edge, outside the open-finger envelope.
    for panel in panels:
        x,y,z=panel['position'];hx,hy,hz=panel['half_size'];bottom=z-hz
        yy=y-hy+.010
        geom(world,'ws_'+panel['name']+'_foot',[x,yy,.403],[.027,.019,.003],steel)
        geom(world,'ws_'+panel['name']+'_post',[x,yy,(.406+bottom)/2],[.006,.006,(bottom-.406)/2],steel)
        geom(world,'ws_'+panel['name']+'_bracket',[x,y,bottom-.004],[hx,hy,.004],blue)
    # Low locator edges. The existing desk surface is the tray bottom, so
    # there is no coincident second contact floor beneath the payload.
    for sign in (-1,1):
        geom(world,f'ws_tray_y_{sign}',[.55,sign*.090,.407],[.085,.004,.007],orange)
        geom(world,f'ws_tray_x_{sign}',[.55+sign*.085,0.,.407],[.004,.086,.007],orange)
    direction=np.array([math.sin(scene.push_angle),-math.cos(scene.push_angle),0.])
    lateral=np.array([-direction[1],direction[0],0.])
    target=np.array([scene.push_target_x,scene.push_target_y,scene.push_height])
    yaw=math.atan2(direction[1],direction[0]);quat=f'{math.cos(yaw/2)} 0 0 {math.sin(yaw/2)}'
    motor=target-direction*.55
    # A separate floor-mounted actuator stand remains outside the desk.
    geom(world,'ws_actuator_floor_base',[motor[0],motor[1],-.34],[.09,.07,.01],dark)
    top=scene.push_height-.045
    geom(world,'ws_actuator_column',[motor[0],motor[1],(top-.33)/2],[.018,.018,(top+.33)/2],steel)
    geom(world,'ws_motor_housing',motor,[.065,.048,.045],blue,quat=quat)
    for sign in (-1,1):
        pos=target-direction*.34+lateral*sign*.044
        pos[2]=scene.push_height-.082
        geom(world,f'ws_linear_rail_{sign}',pos,[.205,.006,.006],steel,quat=quat)
    # The rod body already has a real slide joint and force-limited actuator.
    # Its added carriage has physical mass and collision, not a visual proxy.
    slider=root.find(".//body[@name='push_rod_support']")
    p=-direction*.085
    geom(slider,'ws_moving_carriage',p+[0,0,-.055],[.025,.034,.017],dark,quat=quat,mass='.08')
    geom(slider,'ws_carriage_coupler',p+[0,0,-.020],[.012,.012,.022],steel,mass='.02')
    return root
