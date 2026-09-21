"""Compute-efficient staged search for a unified 6-D VMC teacher bank.

The campaign deliberately avoids fake multi-seed repetitions.  Every fixture
changes at least one physical condition, while controller candidates are first
raced on one anchor fixture.  Only feasible/high-progress candidates advance
to the remaining fixtures.  All accepted traces use the same deployable
48-D proprioceptive observation and 7-D action contract.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_panel_push_20260920.py"
FROZEN_PRIMITIVE = ROOT / "outputs" / "four_scene_pareto_teacher_v1_20260918" / "frozen_runtime" / "scripts" / "run_primitive_teacher_v7_20260917.py"
OUT = ROOT / "outputs" / os.environ.get(
    "UNIFIED_6D_CAMPAIGN", "unified_6d_teacher_search_20260921"
)
WORKERS = int(os.environ.get("UNIFIED_6D_WORKERS", "16"))
INITIAL = int(os.environ.get("UNIFIED_6D_INITIAL", "16"))
REFINE_ROUNDS = int(os.environ.get("UNIFIED_6D_REFINE_ROUNDS", "2"))
SURVIVORS = int(os.environ.get("UNIFIED_6D_SURVIVORS", "6"))
SEED = 20260921


PANEL = {
    "slot_upper_y": 0.15,
    "half_y": 0.17,
    "back_inner_x": 0.50,
    "front_inner_x": 0.595,
    "slot_lower_y": -0.085,
    "layout": "raised_hand_rim",
    "pad_bottom_z": 0.55,
    "pad_top_z": 0.71,
    "pad_lower_y": -0.15,
    "pad_upper_y": -0.085,
    "pad_thickness": 0.015,
    "native_ccd": True,
}


FIXTURES = {
    "ball": [
        dict(id="b_anchor", seed=610, event_stage="approach", ball_mass=.20, ball_speed=1.60, ball_angle=0., ball_height_offset=0., payload_mass=.08),
        dict(id="b_left", seed=611, event_stage="approach", ball_mass=.16, ball_speed=1.85, ball_angle=-.20, ball_height_offset=.015, payload_mass=.10),
        dict(id="b_right", seed=612, event_stage="pregrasp", ball_mass=.24, ball_speed=1.45, ball_angle=.18, ball_height_offset=-.012, payload_mass=.07),
        dict(id="b_loaded", seed=613, event_stage="loaded_lift", ball_mass=.22, ball_speed=1.75, ball_angle=-.10, ball_height_offset=.008, payload_mass=.11),
        dict(id="b_fast", seed=614, event_stage="loaded_lift", ball_mass=.15, ball_speed=2.05, ball_angle=.12, ball_height_offset=-.008, payload_mass=.09),
    ],
    "push": [
        dict(id="p_anchor", seed=800, push_angle=-.15, rod_height_m=.600, push_force=12., push_stroke=.18, payload_mass=.100),
        dict(id="p_shallow", seed=801, push_angle=-.05, rod_height_m=.580, push_force=10., push_stroke=.16, payload_mass=.085),
        dict(id="p_positive", seed=802, push_angle=.10, rod_height_m=.585, push_force=14., push_stroke=.19, payload_mass=.115),
        dict(id="p_low", seed=803, push_angle=-.12, rod_height_m=.575, push_force=13., push_stroke=.20, payload_mass=.095),
        dict(id="p_high", seed=804, push_angle=.04, rod_height_m=.605, push_force=11., push_stroke=.17, payload_mass=.105),
    ],
    "corner": [
        dict(id="c_anchor", seed=25151394, yaw=-.21404075557919147, shift=-.02072100761135175, width=.06881908167606926, corner_height=.6408292867473049, corner_friction=.2906304537472604, payload_mass=.07771658244962452),
        dict(id="c_left", seed=74807681, yaw=-.25011662278442715, shift=-.021890493880648905, width=.06633002405853365, corner_height=.6342001215569271, corner_friction=.355461890181381, payload_mass=.1198918544358753),
        dict(id="c_right", seed=76484908, yaw=-.24174847161652083, shift=-.02097973765416675, width=.06893388604745361, corner_height=.6406208233192927, corner_friction=.41285644469875205, payload_mass=.09806184228473386),
        dict(id="c_wide", seed=95651413, yaw=-.27551366668815347, shift=-.02309451383281133, width=.07097952162696429, corner_height=.6354855291543051, corner_friction=.2985593827680244, payload_mass=.11237930750059502),
        dict(id="c_narrow", seed=13565478, yaw=-.06257634687178695, shift=-.02171192875131628, width=.061387506098253636, corner_height=.643831723243871, corner_friction=.34289770799696706, payload_mass=.1118183800728749),
    ],
    "table_corner": [
        dict(id="t_anchor", seed=810, yaw=0., shift=0., width=.050, corner_height=.70, corner_friction=.20, payload_mass=.080),
        dict(id="t_left", seed=811, yaw=-.10, shift=-.015, width=.058, corner_height=.695, corner_friction=.16, payload_mass=.070),
        dict(id="t_right", seed=812, yaw=.12, shift=.012, width=.047, corner_height=.705, corner_friction=.26, payload_mass=.095),
        dict(id="t_heavy", seed=813, yaw=-.05, shift=.018, width=.065, corner_height=.700, corner_friction=.32, payload_mass=.115),
        dict(id="t_tight", seed=814, yaw=.18, shift=-.020, width=.044, corner_height=.692, corner_friction=.12, payload_mass=.065),
    ],
}

requested_scenes = tuple(filter(None, os.environ.get(
    "UNIFIED_6D_SCENES", "ball,push,corner,table_corner"
).split(",")))
unknown_scenes = set(requested_scenes) - set(FIXTURES)
if unknown_scenes:
    raise ValueError(f"Unknown scenes: {sorted(unknown_scenes)}")
FIXTURES = {scene: FIXTURES[scene] for scene in requested_scenes}


BASES = {
    "ball": dict(k=[350., 350., 900., 8., 8., 12.], b=[32., 32., 48., 2.6, 2.6, 3.2], mass=[.5,.5,.8,.06,.06,.08], gain=1.1, tau=.025, yaw=0.),
    "push": dict(k=[600., 100., 1100., 16., 16., 20.], b=[30., 12., 48., 3.5, 3.5, 4.5], mass=[.5,.5,.8,.06,.06,.08], gain=.8, tau=.015, yaw=-.15),
    "corner": dict(k=[110., 110., 480., 6., 6., 10.], b=[28., 28., 42., 2.3, 2.3, 3.0], mass=[.5,.5,.8,.06,.06,.08], gain=.85, tau=.025, yaw=-.08),
    "table_corner": dict(k=[140., 140., 700., 6., 6., 10.], b=[32., 32., 58., 2.6, 2.6, 3.3], mass=[.55,.55,.85,.065,.065,.085],
        gain=1.45, tau=.022, yaw=0., deadband=[.30,.30,.80,.05,.05,.05], wrench=[25.,25.,35.,3.,3.,3.],
        vmax=[.10,.10,.14,.50,.50,.60], action_limit=[.20,.20,.24,.70,.70,.70]),
}


def digest(value) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def full_config(base):
    return {
        "stiffness_6d": list(base["k"]),
        "damping_6d": list(base["b"]),
        "mass_6d": list(base["mass"]),
        "wrench_limit_6d": list(base.get("wrench",[35., 35., 50., 3., 3., 3.])),
        "deadband_6d": list(base.get("deadband",[.2, .2, .2, .03, .03, .03])),
        "velocity_limit_6d": list(base.get("vmax",[.12, .12, .16, .55, .55, .65])),
        "offset_limit_6d": [.18, .18, .18, .35, .35, .35],
        "action_limit_6d": list(base.get("action_limit",[.16, .16, .20, .60, .60, .60])),
        "offset_tracking_gain_6d": float(base["gain"]),
        "filter_tau": float(base["tau"]),
        "axis_rotation_rpy": [0., 0., float(base["yaw"])],
    }


def initial_configs(scene, count):
    rng = np.random.default_rng(SEED + list(FIXTURES).index(scene) * 1000)
    base = full_config(BASES[scene])
    rows = [("base", base)]
    for i in range(1, count):
        cfg = copy.deepcopy(base)
        # Search meaningful positive VMC quantities in log space.  The broad
        # first round is still bounded to avoid obviously unstable episodes.
        cfg["stiffness_6d"] = (np.asarray(base["stiffness_6d"]) * np.exp(rng.uniform(-1.0, .75, 6))).tolist()
        cfg["damping_6d"] = (np.asarray(base["damping_6d"]) * np.exp(rng.uniform(-.55, .55, 6))).tolist()
        cfg["mass_6d"] = (np.asarray(base["mass_6d"]) * np.exp(rng.uniform(-.30, .30, 6))).tolist()
        gain_bounds=(.8,2.6) if scene=="table_corner" else (.35,1.8)
        cfg["offset_tracking_gain_6d"] = float(np.exp(rng.uniform(math.log(gain_bounds[0]), math.log(gain_bounds[1]))))
        cfg["filter_tau"] = float(np.exp(rng.uniform(math.log(.008), math.log(.065))))
        if scene=="table_corner":
            cfg["deadband_6d"]=(np.asarray(base["deadband_6d"])*np.exp(rng.uniform(-.35,.45,6))).tolist()
            cfg["wrench_limit_6d"]=(np.asarray(base["wrench_limit_6d"])*np.exp(rng.uniform(-.25,.25,6))).tolist()
        rotation_span=.55 if scene in ("corner","table_corner") else .12
        yaw_span=.65 if scene in ("corner","table_corner") else .30
        cfg["axis_rotation_rpy"] = [float(rng.uniform(-rotation_span,rotation_span)), float(rng.uniform(-rotation_span,rotation_span)), float(rng.uniform(-yaw_span,yaw_span))]
        rows.append((f"initial_{i:02d}", cfg))
    return rows


def mutate(scene, parents, round_index, count=16):
    rng = np.random.default_rng(SEED + 5000 + list(FIXTURES).index(scene) * 1000 + round_index)
    rows=[]
    for i in range(count):
        parent=copy.deepcopy(parents[i % len(parents)])
        parent["stiffness_6d"]=(np.asarray(parent["stiffness_6d"])*np.exp(rng.normal(0,.28,6))).tolist()
        parent["damping_6d"]=(np.asarray(parent["damping_6d"])*np.exp(rng.normal(0,.22,6))).tolist()
        parent["mass_6d"]=(np.asarray(parent["mass_6d"])*np.exp(rng.normal(0,.12,6))).tolist()
        gain_hi=3.0 if scene=="table_corner" else 2.2
        parent["offset_tracking_gain_6d"]=float(np.clip(parent["offset_tracking_gain_6d"]*np.exp(rng.normal(0,.20)),.25,gain_hi))
        parent["filter_tau"]=float(np.clip(parent["filter_tau"]*np.exp(rng.normal(0,.18)),.006,.08))
        if scene=="table_corner":
            parent["deadband_6d"]=(np.asarray(parent["deadband_6d"])*np.exp(rng.normal(0,.16,6))).tolist()
        r=np.asarray(parent["axis_rotation_rpy"])+rng.normal(0,[.04,.08,.08])
        # The held-payload table-corner contact needs a positive pitch to
        # couple the apron-normal wrench into tangential lift.  Do not erase
        # the useful +0.4..+1.0 rad region found by the broad race.
        rotation_lo=[-.3,.25,-.65] if scene=="table_corner" else [-.2,-.2,-.45]
        rotation_hi=[.3,1.05,.65] if scene=="table_corner" else [.2,.2,.45]
        parent["axis_rotation_rpy"]=np.clip(r,rotation_lo,rotation_hi).tolist()
        rows.append((f"refine_{round_index}_{i:02d}",parent))
    return rows


def fixture_args(scene, fixture):
    common=[
        "--scene",scene,"--menagerie","../mujoco_menagerie","--nominal-speed",".08",
        "--mixture","0","--seed",str(fixture["seed"]),"--stiffness","200","--damping","20",
        "--force-on",".5","--contact-tau",".12","--release-tau",".45","--memory-tau","1.2",
        "--teacher-force-source","estimated","--teacher-profile","memory","--dt",".0001",
    ]
    if scene == "ball":
        return common + ["--duration","20","--event-stage",fixture["event_stage"],"--event-delay",".30",
            "--ball-mass",str(fixture["ball_mass"]),"--ball-speed",str(fixture["ball_speed"]),
            "--ball-angle",str(fixture["ball_angle"]),"--ball-height-offset",str(fixture["ball_height_offset"]),
            "--payload-mass",str(fixture["payload_mass"])]
    if scene == "push":
        return common + ["--duration","24","--event-stage","approach","--event-delay","0",
            "--push-hold","1000000","--push-angle",str(fixture["push_angle"]),
            "--push-height",str(fixture["rod_height_m"]),"--push-force",str(fixture["push_force"]),
            "--push-target-x",".57","--push-stroke",str(fixture["push_stroke"]),
            "--push-press",".5","--push-retract","1","--payload-mass",str(fixture["payload_mass"])]
    stage="loaded_lift" if scene=="table_corner" else "approach"
    duration="60" if scene=="table_corner" else "50"
    return common + ["--duration",duration,"--event-stage",stage,"--event-delay",".20",
        "--yaw",str(fixture["yaw"]),"--shift",str(fixture["shift"]),"--width",str(fixture["width"]),
        "--corner-height",str(fixture["corner_height"]),"--corner-friction",str(fixture["corner_friction"]),
        "--payload-mass",str(fixture["payload_mass"])]


def run_case(scene, fixture, candidate, config):
    case=OUT/"cases"/scene/fixture["id"]/candidate
    case.mkdir(parents=True,exist_ok=True)
    dest=case/"rollout"; command_hash=digest(dict(scene=scene,fixture=fixture,config=config,contract="proprio48_action7_6d_v1"))
    command_file=case/"command.json"
    if dest.with_suffix(".json").exists() and command_file.exists():
        prior=json.load(open(command_file))
        if prior.get("command_hash")==command_hash:
            try:return measure(scene,fixture,candidate,config,dest,reused=True)
            except Exception:pass
    panel=copy.deepcopy(PANEL)
    if scene=="push":panel["rod_height_m"]=fixture["rod_height_m"]
    env=dict(os.environ,UNIFIED_6D_TEACHER="1",UNIFIED_TEACHER_SCENE=scene,
        PRIMITIVE_RUNNER_PATH=str(FROZEN_PRIMITIVE),
        CORE_VMC_CONFIG=json.dumps(config,separators=(",",":")),PANEL_CONFIG=json.dumps(panel,separators=(",",":")),
        PANELS_ENABLED="1" if scene=="push" else "0",SKIP_MODEL_ARCHIVE="1",MUJOCO_GL="egl",
        OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
    argv=[sys.executable,str(RUNNER),"--output",str(dest)]+fixture_args(scene,fixture)
    command_file.write_text(json.dumps(dict(command_hash=command_hash,argv=argv,
        environment={k:env[k] for k in ("UNIFIED_6D_TEACHER","UNIFIED_TEACHER_SCENE","PRIMITIVE_RUNNER_PATH","CORE_VMC_CONFIG","PANEL_CONFIG","PANELS_ENABLED")}),indent=2))
    started=time.monotonic()
    with dest.with_suffix(".log").open("w") as log:
        try:
            proc=subprocess.run(argv,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
        except subprocess.TimeoutExpired:
            return dict(scene=scene,fixture=fixture["id"],candidate=candidate,config_hash=digest(config),accepted=False,error="timeout",wall_s=time.monotonic()-started)
    if proc.returncode:
        return dict(scene=scene,fixture=fixture["id"],candidate=candidate,config_hash=digest(config),accepted=False,
            error=dest.with_suffix(".log").read_text()[-1800:],wall_s=time.monotonic()-started)
    row=measure(scene,fixture,candidate,config,dest,reused=False);row["wall_s"]=time.monotonic()-started;return row


def measure(scene,fixture,candidate,config,dest,reused=False):
    result=json.load(open(dest.with_suffix(".json")))
    with np.load(dest.with_suffix(".npz"),allow_pickle=False) as z:
        obs=np.asarray(z["observation"]);action=np.asarray(z["teacher_action"]);time_s=np.asarray(z["time"])
        if obs.ndim!=2 or obs.shape[1]!=48 or action.shape!=(len(obs),7):
            raise ValueError(f"contract mismatch {obs.shape} {action.shape}")
        if not np.isfinite(obs).all() or not np.isfinite(action).all():raise ValueError("non-finite trace")
        position=np.asarray(z["position"]);target=np.asarray(z["target"]);twist=np.asarray(z["twist"])
    contact=result.get("contact") or {}
    first=contact.get("first_s");mask=time_s>=(first if first is not None else 0.)
    trajectory_rmse=float(np.sqrt(np.mean(np.sum((position[mask]-target[mask])**2,axis=1))))
    speed=np.linalg.norm(twist[:,:3],axis=1)
    penetration=float(contact.get("all_external_max_penetration_m") or contact.get("max_penetration_m") or 0.)
    peak_force=float(contact.get("peak_body_resultant_n") or contact.get("all_external_peak_force_n") or contact.get("peak_force_n") or 0.)
    endpoint=float(result.get("endpoint_error_m") or 9.)
    torque=float(result.get("peak_torque_nm") or 999.)
    task=bool(result.get("success"));contact_ok=bool(result.get("real_contact"))
    physical=not bool(result.get("invalid_physics")) and not bool(result.get("upstream_contact")) and penetration<.0002
    accepted=task and contact_ok and physical and torque<65. and float(speed.max())<.35
    if scene=="push":accepted=accepted and bool(result.get("accepted_panel_demo"))
    # Feasibility dominates.  The continuous part is only used to rank rows
    # with the same hard status and never converts a failed task into teacher data.
    score=(trajectory_rmse/.08 + endpoint/.02 + peak_force/400. + torque/55. + float(np.percentile(speed,95))/.10 + penetration/.0002)
    progress=(float(result.get("final_stage",0))*5. + max(0.,float(result.get("lift_m",0.)))*20. - endpoint*10. - penetration*1000.)
    return dict(scene=scene,fixture=fixture["id"],fixture_hash=digest(fixture),candidate=candidate,config_hash=digest(config),config=config,
        accepted=accepted,task_success=task,real_contact=contact_ok,physical_valid=physical,score=float(score),progress=float(progress),
        trajectory_rmse_after_contact_m=trajectory_rmse,endpoint_error_m=endpoint,peak_force_n=peak_force,
        peak_torque_nm=torque,speed_peak_mps=float(speed.max()),speed_p95_mps=float(np.percentile(speed,95)),
        max_penetration_m=penetration,final_stage=int(result.get("final_stage",0)),lift_m=float(result.get("lift_m",0.)),
        trace=str(dest.with_suffix(".npz")),result=str(dest.with_suffix(".json")),samples=int(len(obs)),reused=reused)


def save_state(rows, configs, phase):
    payload=dict(version="unified_6d_teacher_search_20260921",phase=phase,updated_unix_s=time.time(),
        contract="48D deployable proprioception including 6D encoder-derived wrench -> 7D VMC action",
        workers=WORKERS,seed=SEED,fixtures=FIXTURES,rows=rows,
        configs={s:{name:cfg for name,cfg in values} for s,values in configs.items()})
    temp=OUT/"state.json.tmp";temp.write_text(json.dumps(payload,indent=2));temp.replace(OUT/"state.json")


def execute(jobs, rows, configs, phase):
    if not jobs:return
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures=[pool.submit(run_case,*job) for job in jobs]
        for future in as_completed(futures):
            row=future.result();rows.append(row);save_state(rows,configs,phase)
            print(json.dumps({k:row.get(k) for k in ("scene","fixture","candidate","accepted","task_success","physical_valid","score","progress","wall_s","error")}),flush=True)


def unique_configs(values):
    seen=set();out=[]
    for name,cfg in values:
        key=digest(cfg)
        if key in seen:continue
        seen.add(key);out.append((name,cfg))
    return out


def pareto(rows):
    keys=("trajectory_rmse_after_contact_m","endpoint_error_m","peak_force_n","peak_torque_nm","speed_p95_mps")
    front=[]
    for row in rows:
        x=np.asarray([row[k] for k in keys])
        if not any(np.all(np.asarray([other[k] for k in keys])<=x) and np.any(np.asarray([other[k] for k in keys])<x) for other in rows):front.append(row)
    return sorted(front,key=lambda r:r["score"])


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    configs={scene:initial_configs(scene,INITIAL) for scene in FIXTURES}
    protocol=dict(version="unified_6d_teacher_search_20260921",created_unix_s=time.time(),workers=WORKERS,
        no_fake_seed_repeats=True,staged_racing=True,initial_candidates=INITIAL,refine_rounds=REFINE_ROUNDS,survivors=SURVIVORS,
        controller="fixed-parameter SixDVirtualDynamics; no visual, geometry, clock, scene-id, or contact-identity policy input",
        primitive_runner=str(FROZEN_PRIMITIVE),primitive_runner_sha256=hashlib.sha256(FROZEN_PRIMITIVE.read_bytes()).hexdigest(),
        observation="48D proprioception: q7, qdot7, nominal twist6, pose error6, twist error6, joint load7, estimated wrench6, path direction3",
        action="slowdown1 + translational residual3 + angular residual3",fixtures=FIXTURES)
    (OUT/"protocol.json").write_text(json.dumps(protocol,indent=2))
    rows=[]
    # Stage A: broad anchor racing.
    jobs=[]
    for scene,values in configs.items():
        for name,cfg in values:jobs.append((scene,FIXTURES[scene][0],name,cfg))
    execute(jobs,rows,configs,"initial_anchor_racing")
    # Stage B: refine only scenes without enough feasible anchor teachers.
    for round_index in range(1,REFINE_ROUNDS+1):
        jobs=[]
        for scene in FIXTURES:
            anchor=FIXTURES[scene][0]["id"]
            current=[r for r in rows if r["scene"]==scene and r["fixture"]==anchor and not r.get("error")]
            accepted=[r for r in current if r["accepted"]]
            if len(accepted)>=SURVIVORS:continue
            parents=sorted(current,key=lambda r:(not r["accepted"],-r["progress"],r["score"]))[:4]
            if not parents:continue
            added=mutate(scene,[r["config"] for r in parents],round_index,INITIAL)
            existing={digest(c) for _,c in configs[scene]};added=[x for x in added if digest(x[1]) not in existing]
            configs[scene]=unique_configs(configs[scene]+added)
            jobs.extend((scene,FIXTURES[scene][0],name,cfg) for name,cfg in added)
        execute(jobs,rows,configs,f"refine_anchor_{round_index}")
    # Stage C: only feasible survivors reach the remaining physical fixtures.
    jobs=[];selected={}
    for scene in FIXTURES:
        anchor=FIXTURES[scene][0]["id"]
        feasible=sorted([r for r in rows if r["scene"]==scene and r["fixture"]==anchor and r["accepted"]],key=lambda r:r["score"])
        chosen=feasible[:SURVIVORS];selected[scene]=[r["candidate"] for r in chosen]
        for row in chosen:
            for fixture in FIXTURES[scene][1:]:jobs.append((scene,fixture,row["candidate"],row["config"]))
    execute(jobs,rows,configs,"survivor_fixture_evaluation")
    # Freeze only accepted physical traces; failures remain recorded.
    accepted=[r for r in rows if r.get("accepted")]
    fronts={}
    for scene in FIXTURES:
        scene_rows=[r for r in accepted if r["scene"]==scene]
        fronts[scene]=pareto(scene_rows) if scene_rows else []
    summary=dict(complete=True,rows=len(rows),accepted=len(accepted),selected_anchor_candidates=selected,
        per_scene={scene:dict(evaluated=sum(r["scene"]==scene for r in rows),accepted=sum(r.get("accepted",False) and r["scene"]==scene for r in rows),
            physical_fixtures=len({r["fixture_hash"] for r in accepted if r["scene"]==scene}),
            parameter_groups=len({r["config_hash"] for r in accepted if r["scene"]==scene}),
            pareto=[{k:r[k] for k in ("fixture","candidate","config_hash","score","trajectory_rmse_after_contact_m","endpoint_error_m","peak_force_n","peak_torque_nm","speed_p95_mps","trace","result")} for r in fronts[scene]]) for scene in FIXTURES},
        contract="proprio48_action7_6d_v1",student_training_started=False,office_data_used=False)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2));save_state(rows,configs,"complete")
    (OUT/"COMPLETE.json").write_text(json.dumps(dict(complete=True,summary_sha256=hashlib.sha256((OUT/"summary.json").read_bytes()).hexdigest()),indent=2))
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
