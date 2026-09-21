"""Explicit numerical profiles validated against resultant contact force.

Native CCD at 1e-12 agrees with independent libccd and a halved timestep on
the first-contact resultant. Individual constraint-point forces can still
redistribute non-monotonically and remain diagnostic, not an external wrench.
"""
import os
import mujoco


def configure_push_numerics(model):
    profile=os.environ.get("PUSH_NUMERICS_PROFILE","legacy")
    if profile=="legacy":return
    if profile!="converged_v1":raise ValueError(f"Unknown push numerical profile: {profile}")
    model.opt.disableflags=int(model.opt.disableflags)&~int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)
    model.opt.ccd_iterations=max(int(model.opt.ccd_iterations),1000)
    model.opt.ccd_tolerance=min(float(model.opt.ccd_tolerance),1e-12)
    model.opt.timestep=min(float(model.opt.timestep),.00005)


def snapshot_numerics(model):
    return dict(mujoco_version=mujoco.__version__,requested_push_profile=os.environ.get("PUSH_NUMERICS_PROFILE","legacy"),
                native_ccd_enabled=not bool(int(model.opt.disableflags)&int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)),
                timestep_s=float(model.opt.timestep),ccd_iterations=int(model.opt.ccd_iterations),
                ccd_tolerance=float(model.opt.ccd_tolerance),constraint_solver=int(model.opt.solver),
                constraint_iterations=int(model.opt.iterations),constraint_tolerance=float(model.opt.tolerance))
