"""Make office replay clips from saved 200 Hz poses; no physics steps."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
import numpy as np
RENDERER=Path('/home/arm1/sii_shared/SII_compliance/source/7cd5f4b7ac0a3056df76ac62bc690ded0724b104/code/mujoco_6d_vmc_benchmark/tools/render_office_threeview_20260929.py')
def main():
    p=argparse.ArgumentParser();p.add_argument('--prefix',type=Path,required=True);p.add_argument('--label',required=True);a=p.parse_args();src=a.prefix
    record=json.loads(src.with_suffix('.json').read_text());trace_path=src.parent/(src.name+'_apparatus_trace.npz')
    with np.load(trace_path) as z:trace={k:z[k] for k in z.files}
    for name,start,end,stride,speed in [('ball',1.9,2.7,1,'0.25x'),('rod',12.5,23.4,4,'1x')]:
        folder=src.parent/('clip_'+name);prefix=folder/'trajectory';selected=(trace['time']>=start)&(trace['time']<=end)
        if not selected.any():
            (src.parent/('clip_'+name+'_UNAVAILABLE.json')).write_text(json.dumps(dict(reason='No saved states in requested window',requested_s=[start,end],last_saved_s=float(trace['time'][-1])),indent=2));continue
        folder.mkdir(exist_ok=False)
        np.savez_compressed(prefix.with_suffix('.npz'),**{k:v[selected] for k,v in trace.items()})
        info=dict(record,summary_scope='Metrics/task fields describe original full run, not this replay window.',clip=dict(source=str(trace_path),source_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),range_s=[start,end],playback=speed,physics_rerun=False,original_summary=str(src.with_suffix('.json'))))
        prefix.with_suffix('.json').write_text(json.dumps(info,indent=2));os.link(src.with_suffix('.mjb'),prefix.with_suffix('.mjb'))
        command=[sys.executable,str(RENDERER),'--rollout',str(prefix),'--output',str(folder/'media'),'--label',a.label+' | '+name+' '+speed+' | full-run metrics','--stride',str(stride),'--fps','50','--gif-stride','5','--contact-closeup']
        with (folder/'render.log').open('w') as log:subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT)
        manifest=json.loads((folder/'media/manifest.json').read_text());rawtimes=trace['time'][selected]
        chosen=sorted(set(list(range(0,len(rawtimes),stride))+[len(rawtimes)-1]));times=rawtimes[chosen]
        factor=.25 if name=='ball' else 1.;skew=float(np.max(abs((times-times[0])-np.arange(len(times))/50*factor)))
        assert len(times)==manifest['frame_count'] and skew<=factor/50+1e-7
        timing=dict(clip=name,frames=manifest['frame_count'],video_duration_s=manifest['video_duration_s'],physical_first_last_s=[float(times[0]),float(times[-1])],physical_span_s=float(times[-1]-times[0]),speed=speed,max_physical_sampling_skew_s=skew,endpoint_note='Renderer includes the last saved state; final interval/hold may differ by at most one video frame.')
        (folder/'TIMING_AUDIT.json').write_text(json.dumps(timing,indent=2));print(json.dumps(timing),flush=True)
if __name__=='__main__':main()
