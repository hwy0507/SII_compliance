"""Read-only temporal comparison of the audited 26-configuration/208-rollout cohort.

No simulation, model selection, or changes to running campaigns. Curves retain
failures and stop at the actual last sample. Physics-substep peaks are preserved.
"""
import argparse
import csv
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np

BIN_S = .02
WINDOW_S = .20


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def trailing_rms(squared_integrals, durations, window_samples, right=None):
    """Right-aligned, duration-weighted; initial windows use available past only."""
    total = np.r_[0., np.cumsum(squared_integrals)]
    elapsed = np.r_[0., np.cumsum(durations)]
    if right is None:
        right = np.arange(1, len(durations)+1)
    left = np.maximum(0, right-window_samples)
    return np.sqrt(np.maximum(0., total[right]-total[left])/(elapsed[right]-elapsed[left]))


def extract(row, cohort):
    path = Path(row['run'])/'rollout_metrics/substep_metrics.npz'
    metric = row['metrics']
    assert sha(path) == metric['native_metrics_sha256'], str(path)
    assert sha(Path(row['run'])/'AUDIT.json') == row['audit_sha256']
    with np.load(path, allow_pickle=False) as data:
        time = data['time']; dt = data['dt']; duration = float(dt.sum())
        assert len(time) > 0 and np.all(np.diff(time) > 0)
        assert np.isfinite(time).all() and np.all(dt > 0)
        np.testing.assert_allclose(dt, .00005, rtol=0, atol=1e-12)
        np.testing.assert_allclose(time, np.cumsum(dt), rtol=0, atol=1e-7)
        stride = round(BIN_S/float(dt[0]))
        starts = np.arange(0, len(time), stride)
        stops = np.minimum(starts+stride, len(time))
        durations = np.add.reduceat(dt, starts)
        error = data['error'].astype(float)
        error2 = np.einsum('ij,ij->i', error, error)
        integrals = np.add.reduceat(error2*dt, starts)
        rolling = trailing_rms(error2*dt, dt, round(WINDOW_S/float(dt[0])), stops)
        full_rmse = float(1000*np.sqrt(np.sum(error2*dt)/duration))
        del error, error2
        torque = np.max(np.abs(data['qfrc_actuator'].astype(float)), axis=1)
        full_torque = float(torque.max())
        torque_peaks = np.maximum.reduceat(torque, starts)
        del torque
        twist = data['twist'][:, :3].astype(float)
        speed = np.linalg.norm(twist, axis=1)
        full_speed = float(speed.max())
        speed_peaks = np.maximum.reduceat(speed, starts)
        del twist, speed
        for actual, key in [(full_rmse, 'rmse_mm'), (full_torque, 'peak_torque_nm'),
                            (full_speed, 'peak_speed_mps')]:
            np.testing.assert_allclose(actual, metric[key], rtol=2e-7, atol=1e-7)
        curves = dict(t=time[stops-1].copy(), interval_rms_mm=1000*np.sqrt(integrals/durations),
                      rolling_rmse_mm=1000*rolling,
                      cumulative_rmse_mm=1000*np.sqrt(np.cumsum(integrals)/np.cumsum(durations)),
                      torque_peak_nm=torque_peaks, speed_peak_mps=speed_peaks)
        np.testing.assert_allclose(curves['cumulative_rmse_mm'][-1], full_rmse, rtol=1e-9)
    assert all(np.isfinite(v).all() for v in curves.values())
    model = row['method']+'__'+cohort
    return dict(id=model, method=row['method'], cohort=cohort, condition=row['condition'],
                task=metric['task_success'], strict=metric['strict_success'],
                full_horizon=metric['full_horizon'], final_stage=metric['final_stage'],
                abort_reason=metric['abort_reason'], duration_s=duration,
                curves={k: v.tolist() for k, v in curves.items()},
                event_windows={k: v['window_s'] for k, v in metric['contact'].items()},
                actual_contact={k: {n: v.get(n) for n in ('first_contact_s', 'last_contact_s', 'contact_duration_s')}
                                for k, v in metric['contact'].items()},
                source=dict(run=row['run'], raw=str(path), raw_sha256=metric['native_metrics_sha256'],
                            audit_sha256=row['audit_sha256'], metric_sha256=row['metric_sha256']),
                checks=dict(rmse_mm=full_rmse, peak_torque_nm=full_torque, peak_speed_mps=full_speed))


def labels(models):
    nice = {'esn': 'ESN', 'ordinary_rnn': 'Ordinary RNN', 'ordinary_mlp': 'Ordinary MLP',
            'matched_rnn': 'Matched RNN', 'matched_mlp': 'Matched MLP',
            'memoryless': 'Memoryless', 'enhanced_teacher': 'Enhanced teacher (reference)',
            'nominal_zero': 'Nominal zero'}
    return {m: nice.get(m.rsplit('__', 1)[0], m.rsplit('__', 1)[0])+
            (' [new]' if m.endswith('__new') else ' [original]') for m in models}


def groups(models):
    anchor = 'esn__new'
    return {
        'new_students': [m for m in models if m.endswith('__new')],
        'original_students_references': [anchor]+[m for m in models if m.endswith('__original') and
            m.split('__')[0] in ['esn','ordinary_rnn','ordinary_mlp','matched_rnn','matched_mlp',
                                  'memoryless','enhanced_teacher','nominal_zero']],
        'classical': [anchor]+[m for m in models if m.startswith(('vmc_', 'admittance_', 'impedance_'))],
        'rl': [anchor]+[m for m in models if m.startswith(('direct_', 'parameter_'))]}


def figures(rows, out, models):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42})
    palette = list(plt.get_cmap('tab20').colors)+list(plt.get_cmap('Dark2').colors)
    colors = {m: matplotlib.colors.to_hex(palette[i]) for i, m in enumerate(models)}
    colors['esn__new'] = '#171717'
    names = labels(models); grouping = groups(models)
    conditions = sorted({r['condition'] for r in rows})
    keys = ['rolling_rmse_mm', 'torque_peak_nm', 'speed_peak_mps']
    units = ['Trailing 0.20 s RMSE (mm)', 'Max |joint torque| (N m)\n20 ms peak envelope',
             'EE linear speed (m/s)\n20 ms peak envelope']
    pdf_path = out/'all_conditions_all_methods.pdf'
    with PdfPages(pdf_path) as pdf:
        for condition in conditions:
            byid = {r['id']: r for r in rows if r['condition'] == condition}
            base = byid['esn__new']
            for group, members in grouping.items():
                fig, axes = plt.subplots(3, 1, figsize=(13.5, 10), sharex=True)
                for m in members:
                    r = byid[m]; c = r['curves']
                    legend = names[m]+f"  T:{int(r['task'])} S:{int(r['strict'])}"
                    if not r['full_horizon']: legend += f" STOP {r['duration_s']:.2f}s"
                    if m == 'matched_rnn__new': legend += ' (= parent ESN)'
                    for i, (ax, key) in enumerate(zip(axes, keys)):
                        ax.plot(c['t'], c[key], label=legend, color=colors[m],
                                lw=2.1 if m == 'esn__new' else 1.1,
                                ls='--' if m == 'matched_rnn__new' else '-', alpha=.85)
                        if not r['full_horizon']:
                            ax.plot(c['t'][-1], c[key][-1], 'x', color=colors[m], ms=7)
                for ax, unit in zip(axes, units):
                    for event, shade in [('human', '#dcebf4'), ('rod', '#f6e8cf')]:
                        a, b = base['event_windows'][event]
                        ax.axvspan(a, b, color=shade, alpha=.5, zorder=0)
                    ax.axvline(base['event_windows']['ball'][0], color='#ba4a60', lw=.8, ls=':')
                    ax.set(xlim=(0,55), ylim=(0,None), ylabel=unit)
                    ax.grid(alpha=.18)
                axes[-1].set_xlabel('Simulation time (s); no time warping, no fill after abort')
                handles, legend = axes[0].get_legend_handles_labels()
                fig.legend(handles, legend, loc='upper left', bbox_to_anchor=(.06,.93),
                           ncol=2, fontsize=8.5, frameon=False)
                fig.suptitle(condition+' | '+group.replace('_',' '), y=.98, fontsize=15)
                fig.text(.07,.942,'Ball launch: dotted line | Human / rod: shaded scheduled windows | T=Task, S=Strict',fontsize=9)
                fig.text(.07,.015,'All failures retained. Edge contact timing varies by method. Group axes auto-scale; compare tick values.',fontsize=8)
                fig.tight_layout(rect=(0,.035,1,.78))
                name=condition+'__'+group
                fig.savefig(out/(name+'.png'),dpi=145)
                pdf.savefig(fig)
                plt.close(fig)
                gc.collect()
    return colors, names, grouping


HTML = r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>全过程轨迹比较 · 26 配置 / 8 条件</title>
<style>body{font-family:system-ui,sans-serif;margin:24px;background:#f4f6f9;color:#172333}h1{font-size:24px}p{max-width:1100px;line-height:1.6}select,input,button{padding:7px;margin:4px;border:1px solid #b9c3d1;border-radius:5px}#choices{display:grid;grid-template-columns:repeat(3,minmax(220px,1fr));gap:5px;font-size:13px;margin:14px 0}label{cursor:pointer}svg{background:white;border-radius:8px;width:100%;height:300px;display:block;margin:14px 0}#note{font-size:13px}#hover{position:fixed;right:20px;bottom:15px;max-height:40vh;overflow:auto;white-space:pre;background:#142237;color:white;padding:12px;font:12px monospace;border-radius:6px;pointer-events:none}a{color:#2463ac}</style>
<h1>全过程轨迹比较：proposed ESN 与全部 baseline</h1>
<p>已审计的 26 配置 × 8 开发条件；原/新权重分开，不使用正在运行的新验收结果。默认第一编号条件，不按成败挑场景。所有曲线使用共同仿真时钟；早停后留空，低力或低速度不等于成功。</p>
<div>条件 <select id="condition"></select> 误差定义 <select id="metric"><option value="rolling_rmse_mm">过去 0.20 秒 RMSE</option><option value="cumulative_rmse_mm">从任务开始累计 RMSE</option><option value="interval_rms_mm">每 20 ms 位置误差 RMS</option></select>
时间范围 <input id="start" type="number" min="0" max="55" step="0.1" value="0" size="4"> 至 <input id="end" type="number" min="0" max="55" step="0.1" value="55" size="4"> 秒</div>
<div id="buttons"></div><div id="choices"></div><p id="note"></p><div id="plots"></div><div id="hover" hidden></div>
<p>误差以记录的末端位置 − 规划参考位置计算，三轴合成，不除以 3。窗口均按物理子步时长加权，起始不足 0.20 秒时使用已有历史。力矩为七关节实际 qfrc_actuator 绝对值最大值；速度为末端平动速度模。二者显示每 20 ms 物理子步最大值，保留峰值，不是低频抽样。</p>
<p>粉色虚线：球发射；蓝色/黄色背景：人手/棍的计划时段，非每个方法的实际接触时段。桌角接触时间随策略变化，不画统一桌角窗口。T/S 分别为该回合 Task/Strict。matched RNN [new] 选回父 ESN，曲线重合属实。Enhanced teacher 有额外机制，仅作参考。各图纵轴自动缩放，比较时注意刻度。</p>
<p><a href="all_conditions_all_methods.pdf">下载完整 32 页 PDF</a> · <a href="curves.csv.gz">下载全部数值 CSV.gz</a> · <a href="AUDIT.json">计算及来源核验</a></p>
<script id="data" type="application/json">__DATA__</script><script>
const D=JSON.parse(document.getElementById('data').textContent),ns='http://www.w3.org/2000/svg';
const selected=new Set(['esn__new','ordinary_rnn__new','ordinary_mlp__new']);
const cond=document.getElementById('condition'),metric=document.getElementById('metric');
[...new Set(D.rows.map(r=>r.condition))].sort().forEach(c=>cond.add(new Option(c,c)));
const titles={new_students:'新学生',original_students_references:'原学生与参考',classical:'经典控制器',rl:'RL baseline'};
Object.entries({...D.groups,all:D.models}).forEach(([g,ms])=>{let b=document.createElement('button');b.textContent=titles[g]||'全部26配置';b.onclick=()=>{selected.clear();ms.forEach(m=>selected.add(m));draw()};document.getElementById('buttons').append(b)});
function el(tag,attrs={},parent){let e=document.createElementNS(ns,tag);for(let [k,v]of Object.entries(attrs))e.setAttribute(k,v);if(parent)parent.append(e);return e}
function text(parent,x,y,s,attrs={}){let e=el('text',{x,y,'font-size':12,fill:'#43536b',...attrs},parent);e.textContent=s;return e}
function draw(){let rows=D.rows.filter(r=>r.condition===cond.value),byid=Object.fromEntries(rows.map(r=>[r.id,r]));document.getElementById('choices').replaceChildren();
D.models.forEach(m=>{let r=byid[m],l=document.createElement('label'),c=document.createElement('input');c.type='checkbox';c.checked=selected.has(m);c.onchange=()=>{c.checked?selected.add(m):selected.delete(m);draw()};l.append(c);l.append(document.createTextNode(D.labels[m]+` | T${+r.task}/S${+r.strict}`+(r.full_horizon?'':` STOP ${r.duration_s.toFixed(2)}s`)));l.style.color=D.colors[m];document.getElementById('choices').append(l)});
let a=Math.max(0,Number(document.getElementById('start').value)),b=Math.min(55,Number(document.getElementById('end').value));if(!(b>a))return;
document.getElementById('plots').replaceChildren();let active=rows.filter(r=>selected.has(r.id));
document.getElementById('note').textContent=`显示 ${active.length}/26 个配置；同一条件的真实时间对齐。悬停读取20ms分箱数值，可缩小时间范围检查瞬态。`;
let keys=[metric.value,'torque_peak_nm','speed_peak_mps'],names=[metric.options[metric.selectedIndex].text+' (mm)','实际关节力矩最大绝对值：20 ms 峰值 (N·m)','实际末端平动速度：20 ms 峰值 (m/s)'];
keys.forEach((key,ki)=>{const svg=el('svg',{viewBox:'0 0 1200 300'},document.getElementById('plots'));let ymax=0;
active.forEach(r=>r.curves.t.forEach((t,i)=>{if(t>=a&&t<=b)ymax=Math.max(ymax,r.curves[key][i])}));ymax=Math.max(ymax*1.08,.001);
const X=t=>75+(t-a)/(b-a)*1100,Y=v=>250-v/ymax*205;text(svg,75,23,names[ki],{'font-size':16});
for(let ev of ['human','rod']){let [s,e]=byid['esn__new'].event_windows[ev];s=Math.max(a,s);e=Math.min(b,e);if(e>s)el('rect',{x:X(s),y:40,width:X(e)-X(s),height:210,fill:ev==='human'?'#e4f0f8':'#fbefdd'},svg)}
let launch=byid['esn__new'].event_windows.ball[0];if(launch>=a&&launch<=b)el('line',{x1:X(launch),x2:X(launch),y1:40,y2:250,stroke:'#d25d77','stroke-dasharray':'3,4'},svg);
for(let j=0;j<=5;j++){let y=j*ymax/5;el('line',{x1:75,x2:1175,y1:Y(y),y2:Y(y),stroke:'#dde3eb'},svg);text(svg,65,Y(y)+4,y.toFixed(ki===2?3:1),{'text-anchor':'end'});let t=a+(b-a)*j/5;text(svg,X(t),273,t.toFixed(1),{'text-anchor':'middle'})}text(svg,1100,294,'Simulation time (s)');
active.forEach(r=>{let points=[];r.curves.t.forEach((t,i)=>{if(t>=a&&t<=b)points.push(X(t).toFixed(2)+','+Y(r.curves[key][i]).toFixed(2))});el('polyline',{points:points.join(' '),fill:'none',stroke:D.colors[r.id],'stroke-width':r.id==='esn__new'?2.5:1.3,'stroke-dasharray':r.id==='matched_rnn__new'?'7,4':'none'},svg)});
svg.onmousemove=e=>{let box=svg.getBoundingClientRect(),tx=a+((e.clientX-box.left)/box.width*1200-75)/1100*(b-a);if(tx<a||tx>b)return;let lines=[`t ≈ ${tx.toFixed(2)} s | ${names[ki]}`];active.forEach(r=>{let ts=r.curves.t;if(tx>ts.at(-1)){lines.push(D.labels[r.id]+': 已终止');return}let l=0,h=ts.length-1;while(l<h){let mid=(l+h)>>1;if(ts[mid]<tx)l=mid+1;else h=mid}lines.push(D.labels[r.id]+': '+r.curves[key][l].toFixed(4))});let h=document.getElementById('hover');h.textContent=lines.join('\n');h.hidden=false};svg.onmouseleave=()=>document.getElementById('hover').hidden=true;
})}
[cond,metric,document.getElementById('start'),document.getElementById('end')].forEach(e=>e.addEventListener('change',draw));draw();
</script></html>'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohort',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(exist_ok=False,parents=True)
    commands=__import__('sys').argv
    write(out/'execution.json',dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),
          command=commands,source_sha256=sha(__file__),simulation=False,server_compute=False))
    rows=[];sources=[]
    for prefix,cohort in [('STUDENT','new'),('BASELINE','original')]:
        report=args.cohort/(prefix+'_REPORT.json');audit=args.cohort/(prefix+'_FINAL_AUDIT.json')
        a=read(audit);assert a['status']=='passed' and sha(report)==a['report_sha256']
        sources.append(dict(report=str(report.resolve()),sha256=sha(report),audit_sha256=sha(audit)))
        shutil.copy2(audit,out/audit.name)
        for row in read(report)['rows']:
            rows.append(extract(row,cohort))
            print(f'Extracted {len(rows)}/208 {cohort} {row["method"]} {row["condition"]}',flush=True)
    assert len(rows)==208
    models=list(dict.fromkeys(r['id'] for r in rows));assert len(models)==26
    conditions=sorted({r['condition'] for r in rows});assert len(conditions)==8
    assert len({(r['id'],r['condition']) for r in rows})==208
    for condition in conditions:
        subset=[r for r in rows if r['condition']==condition]
        assert len(subset)==26
        for event in ['ball','human','rod']:
            # Ball/human/rod scheduled windows must coincide across methods.
            windows=[r['event_windows'][event] for r in subset]
            np.testing.assert_allclose(windows,np.broadcast_to(windows[0],(26,2)),atol=1e-8)
    write(out/'curve_data.json',dict(rows=rows))
    import gzip
    with gzip.open(out/'curves.csv.gz','wt',newline='') as f:
        writer=csv.writer(f);keys=list(rows[0]['curves'])
        writer.writerow(['method','cohort','condition','task','strict',*keys])
        for r in rows:
            for values in zip(*(r['curves'][k] for k in keys)):
                writer.writerow([r['method'],r['cohort'],r['condition'],int(r['task']),int(r['strict']),*values])
    colors,names,grouping=figures(rows,out,models)
    data=dict(rows=[{k:v for k,v in r.items() if k not in ['source','checks']} for r in rows],
              models=models,colors=colors,labels=names,groups=grouping)
    for r in data['rows']:
        r['curves']={k:np.round(v,6).tolist() for k,v in r['curves'].items()}
    (out/'index.html').write_text(HTML.replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)))
    write(out/'AUDIT.json',dict(status='passed',created_utc=datetime.now(timezone.utc).isoformat(),
        rows=208,models=26,conditions=conditions,sources=sources,
        raw_hash_and_episode_audit_checked=True,whole_episode_three_metrics_recomputed=True,
        cumulative_endpoint_equals_report_rmse=True,bin_peak_preservation=True,
        rolling_window_s=WINDOW_S,bin_s=BIN_S,early_stops=sum(not r['full_horizon'] for r in rows),
        no_padding_or_extrapolation=True,first_condition_selection='lexical ID, not performance',
        source_sha256=sha(__file__),limitations=['Development cohort; training budgets/features differ.',
        'Torque and velocity are 20ms substep-peak envelopes, not instantaneous samples.',
        'Scheduled disturbance shading is not actual contact duration; edge timing is policy-dependent.',
        'Reference trajectory can depend on progress. Low error/effort in stalled runs does not establish compliance.'],
        source_rows=[{k:v for k,v in r.items() if k not in ['curves']} for r in rows]))
    shutil.copy2(__file__,out/Path(__file__).name)
    shutil.copy2(Path(__file__).with_name('archive_tool_campaign_20261002.py'),out/'archive_tool_campaign_20261002.py')
    write(out/'execution.json',dict(status='complete',ended_utc=datetime.now(timezone.utc).isoformat(),
          command=commands,source_sha256=sha(__file__),simulation=False,server_compute=False,rows=208))
    print('COMPLETE',out,flush=True)


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        import sys
        if '--out' in sys.argv:
            receipt=Path(sys.argv[sys.argv.index('--out')+1])/'execution.json'
            if receipt.exists():
                value=read(receipt)
                if value.get('status')=='running':
                    value.update(status='failed_preserved',error=repr(exc),ended_utc=datetime.now(timezone.utc).isoformat())
                    write(receipt,value)
        raise
