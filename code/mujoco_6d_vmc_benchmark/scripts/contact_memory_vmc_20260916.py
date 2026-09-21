"""Force-only virtual coupling with persistent tangential contact response.

This teacher is trained/evaluated on primitive contact scenes only. No obstacle
geometry, simulation object, scene identifier, contact oracle, or clock input.
"""
from dataclasses import dataclass
import numpy as np
from haptic_vmc_teacher_20260916 import HapticVMC,HapticVMCConfig


@dataclass(frozen=True)
class ContactMemoryConfig:
    stiffness: float = 110.
    damping: float = 32.
    force_on: float = .5
    tangent_speed: float = .065
    contact_tau: float = .12
    release_tau: float = .45
    memory_tau: float = 1.2


class ContactMemoryVMC:
    def __init__(self,config=ContactMemoryConfig()):
        self.config=config
        self.base=HapticVMC(HapticVMCConfig(stiffness=config.stiffness,damping=config.damping,force_deadband=.5))
        self.contact=0.;self.normal=np.zeros(3);self.tangent=np.zeros(3)
        self.slide=0.;self.filtered_force=np.zeros(3)
        self.engaged=False

    def act(self,force,position_error,velocity,path_direction,dt=.04):
        c=self.config
        force=np.asarray(force);error=np.asarray(position_error);path=np.asarray(path_direction)
        self.filtered_force+=(1.-np.exp(-dt/.06))*(force-self.filtered_force)
        if c.tangent_speed==0.:
            return self.base.act(self.filtered_force,dt)
        magnitude=np.linalg.norm(self.filtered_force)
        loaded=float(np.clip((magnitude-c.force_on)/1.2,0,1))
        tau=c.contact_tau if loaded>self.contact else c.release_tau
        self.contact+=(1.-np.exp(-dt/tau))*(loaded-self.contact)
        unit=self.filtered_force/max(magnitude,1e-9)
        if magnitude>c.force_on:
            normal=self.normal+(1.-np.exp(-dt/.08))*(unit-self.normal)
            self.normal=normal/max(np.linalg.norm(normal),1e-9)
        path=path/max(np.linalg.norm(path),1e-9)
        goal_direction=error/max(np.linalg.norm(error),1e-9)
        path_opposing=max(0.,-float(np.dot(self.normal,path)))
        if self.contact>.2 and path_opposing>.2:self.engaged=True
        if np.linalg.norm(error)<.020:self.engaged=False
        intent=goal_direction if self.engaged else path
        surface_normal=self.normal.copy()
        # Horizontal task segments preserve height while exploring around
        # a vertical face; sensor moment components must not drive downward.
        if abs(path[2])<.25:
            surface_normal[2]=0.
            surface_normal/=max(np.linalg.norm(surface_normal),1e-9)
        opposing=max(0.,-float(np.dot(surface_normal,intent)))
        # React to opposing contact even if the object itself is movable;
        # waiting for a stall would teach the arm to push light objects away.
        distance_gate=float(np.clip((np.linalg.norm(error)-.020)/.05,0,1))
        desired_slide=self.contact*np.clip((opposing-.2)/.5,0,1)*distance_gate
        self.slide+=(1.-np.exp(-dt/(.15 if desired_slide>self.slide else c.memory_tau)))*(desired_slide-self.slide)
        if self.slide>.02:
            projected=intent-surface_normal*np.dot(intent,surface_normal)
            if abs(path[2])<.25:projected[2]=0.
            if np.linalg.norm(projected)<.25 or (np.linalg.norm(self.tangent)<.1 and opposing>.75):
                projected=np.cross(np.array([0.,0.,1.]),surface_normal)
                if projected[0]>0:projected=-projected
            if np.linalg.norm(projected)<.1:projected=np.array([1.,0.,0.])
            projected/=np.linalg.norm(projected)
            # Preserve the previous chosen side as the sensed normal rotates.
            if np.linalg.norm(self.tangent)>.1 and np.dot(projected,self.tangent)<0:projected=-projected
            tangent=self.tangent+(1.-np.exp(-dt/.15))*(projected-self.tangent)
            self.tangent=tangent/max(np.linalg.norm(tangent),1e-9)
        base=self.base.act(self.filtered_force,dt)
        # A virtual tangential drive supplements normal admittance. Return
        # authority decreases continuously as contact evidence accumulates.
        action=base.copy();action[0]=.85*self.slide
        residual=.32*base[1:4]*(1.-.65*self.slide)+c.tangent_speed*self.slide*self.tangent
        action[1:4]=np.clip(residual/.32,-1,1)
        return action
