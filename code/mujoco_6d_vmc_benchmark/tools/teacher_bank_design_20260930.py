"""Versioned source-domain design and small-budget constrained BO.

No frozen evaluation fixture is edited. Scene metadata never enters the actor.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
from scipy.special import ndtr
from scipy.stats import qmc

CATEGORIES = ('passive_corner', 'active_short', 'active_long')
SEED = 20260930
DT = .0001
DURATION = 55.
TRAIN_ANCHORS = (0,337,671)  # all three object types in every category
VALIDATION_ANCHORS = (0,1,11)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def design(reference):
    """3300 distinct physical fixtures; split before any teacher optimization."""
    with np.load(reference, allow_pickle=False) as data:
        times, positions = data['time'].copy(), data['hand'].copy()
    def nominal(t):
        return [float(np.interp(t, times, positions[:, j])) for j in range(3)]
    fixtures = []
    for ci, category in enumerate(CATEGORIES):
        for si, (split, count) in enumerate((('train', 1000), ('validation', 100))):
            points = qmc.LatinHypercube(d=16, seed=SEED + ci * 10 + si).random(count)
            for i, u in enumerate(points):
                start = float(2. + 10. * u[0])
                press = float(1. + 1.5 * u[1])
                yaw = float(-.6 + 1.2 * u[2])
                axis = [-np.sin(yaw), np.cos(yaw), 0.] if category == 'active_short' else [np.cos(yaw), np.sin(yaw), 0.]
                speed = float(1. + 1.2 * u[3])
                flight = .14
                aim = np.array(nominal(start + (flight if category == 'active_short' else press)))
                aim += np.array([0., .008 * (2*u[4]-1), .008 * (2*u[5]-1)])
                launch = aim - np.array(axis) * speed * flight + np.array([0, 0, .5 * 9.81 * flight**2])
                shape = ('sphere', 'ellipsoid', 'capsule')[i % 3]
                apparatus = 'person' if i % 2 == 0 else 'rod'
                values = dict(category=category, split=split, id=f'{category}_{split}_{i:04d}',
                    seed=SEED + ci*100000 + si*10000 + i,
                    start_s=start, press_s=press, hold_s=float(2.+6.*u[6]), retract_s=2.,
                    yaw_rad=yaw, axis=list(map(float, axis)), target_nominal_m=aim.tolist(),
                    launch_position_m=launch.tolist(), ball_speed_mps=speed,
                    ball_mass_kg=float(.08+.20*u[7]), ball_radius_m=float(.025+.02*u[8]),
                    object_shape=shape if category == 'active_short' else
                        ('hand' if apparatus == 'person' else ('rod' if i%4 == 1 else 'paddle')) if category == 'active_long' else
                        ('square_edge','wide_edge','thick_edge')[i%3],
                    apparatus=apparatus, stroke_m=float(.15+.08*u[9]),
                    drive_limit_n=float((45.+45.*u[10]) if apparatus=='person' else (8.+10.*u[10])),
                    rod_mass_kg=float(.35+.65*u[11]), rod_radius_m=float(.012+.010*u[12]),
                    payload_mass_kg=float(.06+.06*u[13]),
                    corner_offset_m=[float(.006*(2*u[4]-1)),float(.008*(2*u[5]-1)),float(.005*(2*u[6]-1))],
                    corner_right_x_m=float(.520+.001*(2*u[4]-1)),
                    corner_center_y_m=float(-.270+.002*(2*u[5]-1)),
                    corner_bottom_z_m=float(.633+.001*(2*u[6]-1)),
                    corner_placement_rule='raised hand-wing underside with outer south rigid connection; source-domain v7',
                    corner_yaw_rad=float(-.25+.5*u[14]), corner_friction=float(.15+.25*u[15]))
                active_keys=['category','payload_mass_kg']
                if category=='passive_corner':active_keys+=['corner_right_x_m','corner_center_y_m','corner_bottom_z_m','corner_placement_rule','corner_yaw_rad','corner_friction','object_shape']
                elif category=='active_short':active_keys+=['launch_position_m','axis','start_s','ball_speed_mps','ball_mass_kg','ball_radius_m','object_shape']
                else:active_keys+=['start_s','press_s','hold_s','retract_s','yaw_rad','axis','target_nominal_m','apparatus','stroke_m','drive_limit_n','object_shape']+(['rod_mass_kg','rod_radius_m'] if apparatus=='rod' else [])
                values['active_physical_parameters']={k:values[k] for k in active_keys}
                values['physical_config_sha256'] = digest(values['active_physical_parameters'])
                fixtures.append(values)
    return fixtures


def decode(x):
    """Seven bounded dimensions: grouped K, damping ratios, velocity readout, gain."""
    x = np.asarray(x, float)
    if x.shape != (7,) or not np.isfinite(x).all() or np.any(x<0) or np.any(x>1):
        raise ValueError('Seven unit-cube coordinates required')
    ks = np.exp(np.log(.5) + x[:3] * np.log(8.))
    ds = np.exp(np.log(.5) + x[3:5] * np.log(4.))
    scale = np.r_[ks[0],ks[0],ks[1],ks[2],ks[2],ks[2]]
    return dict(velocity_weight=float(.1+.65*x[5]), options=dict(
        stiffness_6d=(np.array([400,400,1200,10,8,12])*scale).tolist(),
        damping_6d=(np.array([28,28,55,2.8,2.4,3])*np.sqrt(scale)*np.r_[np.repeat(ds[0],3),np.repeat(ds[1],3)]).tolist(),
        offset_tracking_gain_6d=float(.8+1.4*x[6])))


def warm_points(seed, count=8, dimensions=7, vmc_reference=True):
    x = qmc.LatinHypercube(dimensions, seed=seed).random(count)
    x[0] = [2/3,2/3,2/3,.5,.5,(.25-.1)/.65,(1.6-.8)/1.4] if vmc_reference else np.full(dimensions,.5)
    return x.tolist()


def posterior(x, y, query):
    """Small exact GP; hyperparameters fit by marginal likelihood, no extra dependency."""
    x,y,query = np.asarray(x),np.asarray(y),np.asarray(query)
    center,scale=float(y.mean()),max(float(y.std()),.1)
    z=(y-center)/scale
    distance=np.sqrt(np.sum((x[:,None]-x[None,:])**2,axis=2))
    def kernel(r, length):
        v=np.sqrt(5.)*r/length
        return (1+v+v*v/3)*np.exp(-v)
    def nll(loglength):
        k=kernel(distance,np.exp(loglength[0]))+np.eye(len(x))*.01
        factor=cho_factor(k)
        return .5*z@cho_solve(factor,z)+np.log(np.diag(factor[0])).sum()
    fit=minimize(nll,[np.log(.6)],bounds=[(np.log(.08),np.log(3.))],method='L-BFGS-B')
    length=np.exp(fit.x[0]);factor=cho_factor(kernel(distance,length)+np.eye(len(x))*.01)
    cross=kernel(np.sqrt(np.sum((query[:,None]-x[None,:])**2,axis=2)),length)
    mean=center+scale*(cross@cho_solve(factor,z))
    variance=np.maximum(1.-np.sum(cross*cho_solve(factor,cross.T).T,axis=1),1e-10)
    return mean,scale*np.sqrt(variance)


def propose(history, seed):
    pool=qmc.LatinHypercube(len(history[0]['x']), seed=seed).random(512)
    x=[r['x'] for r in history]
    constraint=[r['constraint'] for r in history]
    mean,std=posterior(x,constraint,pool)
    feasible=[r for r in history if r['constraint']<=0]
    if len(feasible)<2:
        acquisition=-(mean-1.5*std)  # feasibility search, no failed trajectory promotion
    else:
        om,os=posterior([r['x'] for r in feasible],[r['score'] for r in feasible],pool)
        delta=min(r['score'] for r in feasible)-om
        z=delta/os
        ei=delta*ndtr(z)+os*np.exp(-z*z/2)/np.sqrt(2*np.pi)
        acquisition=ndtr(-mean/std)*(ei+.01*os)
    distance=np.min(np.linalg.norm(pool[:,None]-np.asarray(x)[None,:],axis=2),axis=1)
    acquisition[distance<1e-6]=-np.inf
    return pool[int(np.argmax(acquisition))].tolist()
