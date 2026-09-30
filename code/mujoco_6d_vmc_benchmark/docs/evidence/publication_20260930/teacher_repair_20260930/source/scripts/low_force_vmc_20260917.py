"""Teacher-only fast virtual coupling with contact-normal approach cancellation.

The student learns the resulting action. This rule is NOT executed in either
student. A nominal velocity is task information, not obstacle geometry.
"""
import numpy as np
from contact_memory_vmc_20260916 import ContactMemoryVMC,ContactMemoryConfig


class LowForceVMC(ContactMemoryVMC):
    def __init__(self, config=ContactMemoryConfig(), force_target=1., normal_gain=.02):
        super().__init__(config)
        self.force_target=force_target;self.normal_gain=normal_gain
        self.fast_force=np.zeros(3);self.contact_level=0.

    def act(self, force, position_error, velocity, path_direction, dt=.01, nominal_velocity=None):
        force=np.asarray(force,dtype=float)
        action=super().act(force,position_error,velocity,path_direction,dt)
        self.fast_force+=(1.-np.exp(-dt/.010))*(force-self.fast_force)
        magnitude=np.linalg.norm(self.fast_force)
        level=np.clip((magnitude-.25)/.75,0.,1.)
        tau=.015 if level>self.contact_level else .20
        self.contact_level+=(1.-np.exp(-dt/tau))*(level-self.contact_level)
        if nominal_velocity is None:raise ValueError('Nominal velocity required')
        if magnitude>.05:
            n=self.fast_force/magnitude
            action[0]=max(action[0],.95*self.contact_level)
            scale=1.-.8*action[0]
            residual=.32*action[1:4]
            full=scale*np.asarray(nominal_velocity)+residual
            cancel=-min(0.,float(full@n))*n
            unload=min(.06,self.normal_gain*max(0.,magnitude-self.force_target))*n
            action[1:4]=np.clip((residual+self.contact_level*(cancel+unload))/.32,-1.,1.)
        return action
