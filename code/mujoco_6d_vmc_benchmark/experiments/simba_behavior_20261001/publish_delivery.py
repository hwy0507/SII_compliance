"""Publish frozen campaign evidence without selecting models or thresholds."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import markdown

ORDER = ['office_task', 'metric', 'esn', 'hybrid', 'zero']
LABELS = ['RL task', 'RL metric', 'Pure ESN', '75% VMC + 25% ESN', 'Zero residual']
COLORS = ['#3578b5', '#dc8540', '#40885b', '#8055aa', '#667580']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--campaign', type=Path, required=True)
    p.add_argument('--document', type=Path, required=True)
    p.add_argument('--web-root', type=Path, required=True)
    a = p.parse_args()
    report = a.campaign/'report'
    s = json.loads((report/'SUMMARY.json').read_text())
    audit = json.loads((report/'RAW_METRICS_AUDIT.json').read_text())
    if s['status'] != 'complete' or s['audits']['errors'] or not audit['all54_present'] or not audit['all_observed_pass']:
        raise ValueError('Publication requires a complete audited matrix')
    training = []
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for run in s['runs']:
        if run['group'] not in ('office_task', 'metric'):
            continue
        records = [json.loads(x) for x in (a.campaign/run['id']/'episode_summaries.jsonl').read_text().splitlines()]
        post = [x for x in records if x['step']-x['steps_in_episode'] >= 5000]
        reached = [any(int(k)>=2 for k in x['metrics']['stages']) for x in post]
        training.append(dict(run=run['id'], ended_after_warmup=len(post), reached_grasp_stage=sum(reached),
            task_physical_success=sum(x['training_success'] for x in post),
            aborts=sum(x['abort_reason'] is not None for x in post),
            final_stage_counts=dict(Counter(x['final_stage'] for x in post)),
            warmup_or_crossing_excluded=len(records)-len(post)))
        ax = axes[ORDER.index(run['group'])]
        y = [np.mean(reached[max(0,i-9):i+1]) for i in range(len(reached))]
        ax.plot([x['step']/1000 for x in post], y, label=str(run['training_seed']))
    for ax, title in zip(axes, LABELS[:2]):
        ax.set(title=title+' | no post-warmup placement success', xlabel='Training transitions (thousands)',
               ylabel='Reached grasp stage, last <=10 ended episodes', ylim=(-.03,1.03))
        ax.legend(title='Training seed'); ax.grid(alpha=.2)
    for ext in ('png','pdf'): fig.savefig(report/('training_coverage.'+ext), dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13,4), constrained_layout=True)
    for ax, key, label in zip(axes, ('rmse_cm','peak_torque_nm','peak_velocity_mps'),
                             ('Position RMSE (cm)','Actual peak torque (Nm)','Peak linear speed (m/s)')):
        for i, group in enumerate(ORDER):
            episodes = [e for r in s['runs'] if r['group']==group for e in r['episodes']]
            xs = np.linspace(i-.2,i+.2,len(episodes))
            for x,e in zip(xs,episodes):
                ax.scatter(x,e[key],color=COLORS[i],marker='o' if e['full55'] else 'x',s=24,
                           facecolors=COLORS[i] if e['physical_valid'] else 'none')
        ax.set_xticks(range(5),LABELS,rotation=28,ha='right');ax.set_ylabel(label);ax.grid(axis='y',alpha=.2)
    fig.suptitle('All 54 rollouts; x = early abort, hollow = physically invalid. No mixed-horizon ranking.')
    for ext in ('png','pdf'): fig.savefig(report/('rollout_metrics.'+ext), dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 4, figsize=(14,4), constrained_layout=True)
    states = ['passed','failed','unknown','not_exposed']
    state_colors = ['#40916c','#cf625a','#dda94a','#b7bfc9']
    for ax, obstacle in zip(axes,['ball','person_hand','rod','office_v5_pillar']):
        for i,g in enumerate(s['groups']):
            c=g['counts']['event_status_by_obstacle'].get(obstacle,{})
            left=0
            for state,color in zip(states,state_colors):
                frac=c.get(state,0)/g['observed_episodes']
                ax.barh(i,frac,left=left,color=color,label=state if i==0 else None)
                if frac>.14: ax.text(left+frac/2,i,str(c.get(state,0)),ha='center',va='center',fontsize=8)
                left+=frac
        ax.set_yticks(range(5),LABELS if ax is axes[0] else ['']*5)
        ax.invert_yaxis();ax.set_title(obstacle);ax.set_xlim(0,1);ax.set_xlabel('Fraction of all protocol cases')
    axes[-1].legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=2,fontsize=8)
    for ext in ('png','pdf'): fig.savefig(report/('contact_outcomes.'+ext),dpi=160)
    plt.close(fig)
    stages={}
    for run in s['runs']:
        stages[run['id']]=dict(Counter(json.loads(Path(e['raw_result']).read_text())['final_task_stage'] for e in run['episodes']))
    evidence=dict(training=training, evaluation_stage_counts=stages,
        source_summary_sha256=hashlib.sha256((report/'SUMMARY.json').read_bytes()).hexdigest(),
        source_audit_sha256=hashlib.sha256((report/'RAW_METRICS_AUDIT.json').read_bytes()).hexdigest(),
        plotting_scope='all54 incl aborted/invalid; training stage reach is not physical grasp success')
    (report/'DELIVERY_EVIDENCE.json').write_text(json.dumps(evidence,indent=2)+'\n')
    shutil.copy2(a.document,report/'FINAL_REPORT.md')
    assets=a.web_root/'assets'/'simbav2_behavior_20261001'
    assets.mkdir(parents=True,exist_ok=True)
    for f in report.iterdir():
        if f.is_file() and f.suffix in ('.png','.pdf','.md','.json'): shutil.copy2(f,assets/f.name)
    videos=[]
    for name in ('office_task_seed61001','metric_seed61001','esn','hybrid','zero'):
        source=a.campaign/'media'/name
        if not (source/'manifest.json').exists():
            raise FileNotFoundError('Missing completed replay '+str(source))
        dest=assets/name;dest.mkdir(exist_ok=True)
        for f in source.iterdir():
            if f.is_file(): shutil.copy2(f,dest/f.name)
        videos.append(f'<article><h3>{name} · 同一 case 0</h3><video controls preload="metadata" src="assets/simbav2_behavior_20261001/{name}/replay.mp4"></video><p><a href="assets/simbav2_behavior_20261001/{name}/replay.gif">完整 GIF</a> · 原始状态重放，默认 2 倍速；画面 strict 是旧完整任务与覆盖联合判据。</p></article>')
    body=markdown.markdown(a.document.read_text(),extensions=['tables','fenced_code'])
    pics=''.join(f'<figure><img src="assets/simbav2_behavior_20261001/{name}.png"><figcaption>{caption}</figcaption></figure>' for name,caption in [
      ('training_coverage','训练阶段覆盖，排除 warmup 和跨边界回合；不是抓取成功率。'),
      ('rollout_metrics','保留全部失败；叉号为提前终止，空心为物理无效；不可按混合时长均值排名。'),
      ('contact_outcomes','逐类接触的通过、失败、未知和未曝光，分母为该组全部条件。')])
    html='<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SimbaV2 与 ESN：2026-10-01 审计报告</title><style>body{font:17px/1.7 system-ui;margin:36px auto;max-width:1160px;padding:0 24px;color:#203040;background:#fafbfc}table{border-collapse:collapse;display:block;overflow:auto}th,td{border:1px solid #cbd4dc;padding:8px}code{overflow-wrap:anywhere}pre{white-space:pre-wrap;background:#edf1f5;padding:14px}img,video{width:100%;height:auto}article{border-top:1px solid #b8c5d0;margin-top:28px}h1,h2,h3{line-height:1.3}a{color:#145a96}</style>'+body+'<h2>审计图表</h2>'+pics+'<h2>同条件完整录像</h2><p>固定选 case 0，RL 固定 seed 61001；不是按表现挑选最佳回合。视频来自归档 MJB 和状态数组，没有重新运行物理。</p>'+''.join(videos)+'</html>'
    page=a.web_root/'simbav2_behavior_20261001.html';page.write_text(html)
    print(json.dumps(dict(page=str(page),assets=str(assets),evidence=str(report/'DELIVERY_EVIDENCE.json'))))


if __name__=='__main__': main()
