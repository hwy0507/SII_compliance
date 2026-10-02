"""Publish completed, explicitly labeled state replays on the existing local demo server."""
import argparse,html,json
from pathlib import Path
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
WEB=Path('/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/primitive_baselines_20261002')
SCENES={'ball':'球撞','push':'棍子（无挡板）','corner':'侧面桌角','table_corner':'桌角'}
IDS={'ball':'ball_013_000','push':'push_001_102','corner':'corner_013_repeat_1_901','table_corner':'table_corner_003_201'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,default=ROOT/'MEDIA_CATALOG.json');a=p.parse_args();catalog=json.loads(a.catalog.read_text());WEB.mkdir(parents=True,exist_ok=True);(WEB/'media').mkdir(exist_ok=True);items=[]
 for entry in catalog['entries']:
  parent=Path(entry['path'])
  for scene,zh in SCENES.items():
   ep=parent/(scene+'_reference');media=ep/'media'
   if not (media/'RENDER.json').exists():continue
   r=json.loads((ep/'result.json').read_text());key=entry['id']+'_'+scene;link=WEB/'media'/key
   if not link.exists():link.symlink_to(media,target_is_directory=True)
   elif link.resolve()!=media.resolve():raise ValueError('Existing media target differs: '+str(link))
   item=dict(id=key,scene=scene,scene_name=zh,label=entry['label'],group=entry.get('group','baseline'),url='media/'+key+'/full_1x.mp4',poster='media/'+key+'/poster.jpg',contact_url='media/'+key+'/contact_025x.mp4' if (media/'contact_025x.mp4').exists() else None,metrics={k:r[k] for k in ['task_success','physical_valid','contact_exposed','duration_s','rmse_m','peak_torque_nm','peak_speed_mps']})
   items.append(item)
 data=dict(status=catalog['status'],items=items,scenes=SCENES,references={s:'../assets/teacher_eight_20260918/'+k+'/rollout.mp4' for s,k in IDS.items()})
 (WEB/'gallery.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 page="""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>四场景 Baseline 实验</title>
<style>
:root{font:16px/1.6 system-ui,sans-serif;color:#18313c;background:#edf2f3}*{box-sizing:border-box}body{margin:0}header,main{max-width:1480px;margin:auto;padding:28px}header{padding-bottom:8px}h1{font-size:32px;margin:0 0 8px}p{margin:8px 0;color:#526871}nav{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}button{font:inherit;cursor:pointer;border:1px solid #b6c8cc;background:white;padding:7px 17px;border-radius:8px;color:#24414c}button.active{background:#1b5868;color:white;border-color:#1b5868}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}article{background:#fff;border:1px solid #d3dfe2;border-radius:12px;overflow:hidden}article h2{font-size:19px;margin:16px 18px 10px}video{display:block;width:100%;aspect-ratio:1280/544;background:#0c141c}.details{padding:12px 18px 18px}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin:12px 0}.metrics b{display:block;font-size:19px}.metrics span{font-size:13px;color:#617781}.tag{display:inline-block;border-radius:5px;padding:2px 7px;background:#ecf2f4;color:#536b76;margin:2px 5px 2px 0;font-size:13px}.pass{background:#e5f3e9;color:#256044}.fail{background:#f9e9e6;color:#943d33}.controls{display:flex;gap:8px;margin:10px 0}.controls button{padding:5px 10px;font-size:14px}details{margin:24px 0;background:#fff;padding:16px;border:1px solid #d3dfe2;border-radius:10px}summary{cursor:pointer;font-weight:600}.reference{max-width:900px;margin:12px auto}a{color:#1b657c}.status{font-weight:600;color:#846327}small{color:#647c85}@media(max-width:900px){.grid{grid-template-columns:1fr}header,main{padding:18px}}
</style><header><h1>四场景 Baseline 实验</h1><p>导纳 · 阻抗 · RL-SimbaV2 · zero 对照</p><p id="status" class="status"></p><nav id="nav"></nav><p>默认按实际仿真时间 1 倍速播放；碰撞片段为 0.25 倍慢放。每个视频保留失败过程。</p></header>
<main><div id="grid" class="grid"></div><details><summary>查看用户提供的原始演示</summary><p>用于确定四个特化场景的来源；原始演示的控制器和旧成功标签不作为本次 baseline 成绩。</p><video id="reference" class="reference" controls preload="metadata"></video></details>
<details><summary>结果如何理解</summary><p>zero 表示额外柔顺动作全零，名义控制器仍然工作。“指定接触”表示确实碰到本场景的球、棍或桌角。“穿透检查”只检查外部穿透和数值有效性，不能单独证明接触行为合理。</p><p>RMSE 是全回合位置误差；力矩与速度是全回合峰值。任务失败或提前终止也保留，跨时长结果须结合汇总报告阅读。页面上的四个原始条件用于直观展示，正式成绩另用固定保留测试条件。</p></details><small>2026-10-02 · 保存状态回放 · 最终环境与 WBC 改进属于另一项工作。</small></main>
<script>
fetch('gallery.json').then(r=>r.json()).then(data=>{
 const nav=document.getElementById('nav'),grid=document.getElementById('grid');
 document.getElementById('status').textContent=data.status;
 let selected='ball';
 function draw(){nav.innerHTML='';grid.innerHTML='';
 for(const [s,name] of Object.entries(data.scenes)){const b=document.createElement('button');b.textContent=name;b.className=s===selected?'active':'';b.onclick=()=>{selected=s;draw()};nav.append(b)}
 document.getElementById('reference').src=data.references[selected];
 for(const x of data.items.filter(i=>i.scene===selected)){
 const a=document.createElement('article'),h=document.createElement('h2');h.textContent=x.label;a.append(h);
 const v=document.createElement('video');v.controls=true;v.preload='metadata';v.src=x.url;v.poster=x.poster;a.append(v);
 const d=document.createElement('div');d.className='details';
 const states=[['任务完成',x.metrics.task_success],['指定接触',x.metrics.contact_exposed],['穿透检查',x.metrics.physical_valid]];
 for(const [name,yes] of states){const t=document.createElement('span');t.className='tag '+(yes?'pass':'fail');t.textContent=name+'：'+(yes?'是':'否');d.append(t)}
 const met=document.createElement('div');met.className='metrics';
 for(const [label,value] of [['RMSE / m',x.metrics.rmse_m.toFixed(4)],['峰值力矩 / Nm',x.metrics.peak_torque_nm.toFixed(2)],['峰值速度 / m/s',x.metrics.peak_speed_mps.toFixed(3)]]){const z=document.createElement('div'),b=document.createElement('b'),s=document.createElement('span');b.textContent=value;s.textContent=label;z.append(b,s);met.append(z)}d.append(met);
 const buttons=document.createElement('div');buttons.className='controls';
 for(const [title,url] of [['完整 1×',x.url],['碰撞 0.25×',x.contact_url]]){if(!url)continue;const b=document.createElement('button');b.textContent=title;b.onclick=()=>{v.src=url;v.load();v.play()};buttons.append(b)}d.append(buttons);a.append(d);grid.append(a);
 }
 if(!grid.children.length){const p=document.createElement('p');p.textContent='该场景的视频正在生成。';grid.append(p)}
 }
 draw();
});
</script></html>"""
 (WEB/'index.html').write_text(page);print(json.dumps(dict(url='http://192.168.31.70:8765/primitive_baselines_20261002/',completed_media=len(items))))
if __name__=='__main__':main()
