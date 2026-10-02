"""Publish only completed office transfer media to the existing LAN demo site."""
import html,json
from pathlib import Path
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
WEB=Path('/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/primitive_baselines_20261002/office')
def main():
    WEB.mkdir(parents=True,exist_ok=True);(WEB/'media').mkdir(exist_ok=True);cards=[];rows=[]
    for folder in sorted((ROOT/'office_bridge/transfer01').glob('*')):
        p=folder/'rollout.json';manifest=folder/'media/manifest.json'
        if not p.exists() or not manifest.exists():continue
        s=json.loads(p.read_text());execution=json.loads((folder/'EXECUTION.json').read_text())
        if execution['status']!='complete':continue
        media=json.loads(manifest.read_text())
        if media['input_sha256']['.mjb']!=s['model_sha256']:raise ValueError('Media model mismatch')
        links={}
        for key,target in [('full',folder/'media'),('ball',folder/'clip_ball/media'),('rod',folder/'clip_rod/media')]:
            if not (target/'manifest.json').exists():continue
            link=WEB/'media'/(folder.name+'_'+key)
            if not link.exists():link.symlink_to(target,target_is_directory=True)
            elif link.resolve()!=target.resolve():raise ValueError('Media target changed')
            links[key]='media/'+link.name+'/replay_threeview.mp4'
        m=s['metrics'];events=s['stats']['events'];checkpoint=Path(execution['checkpoint']).name if execution.get('checkpoint') else 'fixed'
        title=folder.name.replace('_',' ')+' · '+checkpoint
        metric=f'RMSE {m["position_rmse_3d_m"]*1000:.2f} mm · 峰矩 {m["generalized_actuator_torque_peak_nm"]:.2f} Nm · 峰速 {m["linear_speed_peak_mps"]:.3f} m/s'
        state=f'task={s["task_success"]} · strict={s["strict_success"]} · 末阶段 {s["final_task_stage"]} · 最大外穿透 {s["stats"]["max_external_penetration_m"]*1000:.3f} mm'
        contact='；'.join(name+('：实际接触' if events.get(key,{}).get('duration_s',0)>0 else '：未记录接触') for name,key in [('球','ball'),('人手','person_hand'),('棍','rod')])
        controls=''.join('<button data-url="'+html.escape(url)+'">'+label+'</button>' for key,label in [('full','完整 1×'),('ball','球撞 0.25×'),('rod','棍推 1×')] if (url:=links.get(key)))
        cards.append('<article><h2>'+html.escape(title)+'</h2><video controls preload="metadata" src="'+links['full']+'"></video><div class="info"><p>'+html.escape(state)+'</p><p>'+html.escape(metric)+'</p><p>'+html.escape(contact)+'</p><div>'+controls+'</div></div></article>')
        rows.append(dict(id=folder.name,checkpoint=checkpoint,task=s['task_success'],strict=s['strict_success'],stage=s['final_task_stage'],metrics=m,model_sha256=s['model_sha256'],links=links))
    header='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>main v5 · baseline 迁移检查</title><style>
body{font:16px/1.6 system-ui,sans-serif;margin:0;background:#edf2f3;color:#18313c}main,header{max-width:1550px;margin:auto;padding:25px}h1{font-size:30px;margin-bottom:6px}p{color:#4b636d}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}article{background:white;border:1px solid #cbdadd;border-radius:12px;overflow:hidden}h2{font-size:19px;margin:14px 18px}.info{padding:0 18px 18px}video{width:100%;display:block;background:#101923;aspect-ratio:1920/560}button{font:inherit;padding:6px 13px;border:1px solid #9bb6bf;background:white;border-radius:6px;margin:4px;cursor:pointer}a{color:#1b657c}aside{padding:16px;border:1px solid #cbdadd;background:white;border-radius:10px;margin-top:22px}@media(max-width:1000px){.grid{grid-template-columns:1fr}}
</style><header><h1>main v5 · baseline 迁移检查</h1><p>固定 main 7cd5f4b · 同一归档 MJB · 55 秒综合接触场景 · 开发步长 0.1 ms</p><p>完整视频为三机位原速回放；球撞特写来自 200 Hz 状态，以 0.25 倍速播放。失败与未发生接触的情况均保留。</p><p><a href="../">四个视频特化场景</a> · 本页为单一综合条件的迁移检查，不能当作跨条件成功率或正式步长结果。</p></header><main><div class="grid">'''
    footer='''</div><aside><b>怎样看结果</b><p>Zero 表示没有额外学习柔顺动作，公共名义控制仍工作。任务成功要求抬起、松手并稳定放置；strict 另外检查物理约束。某一回合未碰到球，不能作为抗球撞成功样本。低 RMSE 也可能来自长时间停滞，请结合末阶段和完整视频阅读。</p><p>球、人手、棍采用固定世界时序，未知凸边从初态就存在。所有 baseline 共用物理模型、名义参考与执行器约束；阻抗使用自己的力矩控制律。视频叠加指标描述完整回合。</p></aside></main><script>document.querySelectorAll('button[data-url]').forEach(b=>b.onclick=()=>{const v=b.closest('article').querySelector('video');v.src=b.dataset.url;v.load();v.play()})</script></html>'''
    (WEB/'index.html').write_text(header+''.join(cards)+footer)
    (WEB/'results.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
    print(json.dumps(dict(url='http://192.168.31.70:8765/primitive_baselines_20261002/office/',completed_media=len(rows))))
if __name__=='__main__':main()
