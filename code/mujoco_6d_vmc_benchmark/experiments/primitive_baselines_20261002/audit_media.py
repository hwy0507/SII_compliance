"""Check encoded media metadata against saved replay timing manifests."""
import hashlib,json
from pathlib import Path
import imageio.v2 as imageio
ROOT=Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002")
def check(path, frames, fps):
    reader=imageio.get_reader(str(path))
    try:
        meta=reader.get_meta_data()
        first=reader.get_data(0)
    finally:reader.close()
    assert abs(meta["fps"]-fps)<1e-6,(str(path),meta)
    expected=frames/fps
    assert abs(meta["duration"]-expected)<=1/fps+.011,(str(path),expected,meta)
    assert first.ndim==3 and first.shape[2]==3
    return dict(path=str(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        expected_frames=frames,fps=meta["fps"],encoded_duration_s=meta["duration"],expected_duration_s=expected,
        first_frame_shape=list(first.shape),check="header timing and first decoded frame; not all-frame visual inspection")
def main():
    rows=[];native=[]
    manifests=sorted((ROOT/"final_reference01").glob("*/*/media/RENDER.json"))
    assert len(manifests)==52
    for p in manifests:
        m=json.loads(p.read_text());rows.append(check(p.parent/"full_1x.mp4",m["frame_count"],m["fps"]))
        assert m["physics_advanced"] is False and m["interpolation"] is False
        clip=m.get("native_impact_clip")
        if clip:
            assert clip["maximum_matching_pose_error"]<=1e-12 and clip["maximum_matching_time_error_s"]<=1e-8
            rows.append(check(p.parent/clip["file"],clip["frame_count"],clip["fps"]));native.append(clip)
    offices=sorted((ROOT/"office_bridge/transfer01").glob("*/media/manifest.json"))
    assert len(offices)==11
    for p in offices:
        m=json.loads(p.read_text());rows.append(check(p.parent/"replay_threeview.mp4",m["frame_count"],25))
        for q in sorted(p.parent.parent.glob("clip_*/TIMING_AUDIT.json")):
            c=json.loads(q.read_text())
            rows.append(check(q.parent/"media/replay_threeview.mp4",c["frames"],50))
    result=dict(primitive_full_videos=len(manifests),office_full_videos=len(offices),primitive_native_impact_clips=len(native),
        metadata_verified_files=len(rows),rows=rows,
        visual_scope="Selected contact sheets, trajectory figures and representative office frames are separately inspected. Header/first-frame checks do not mean every full video was watched.")
    (ROOT/"MEDIA_METADATA_AUDIT.json").write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in result.items() if k!="rows"}))
if __name__=="__main__":main()
