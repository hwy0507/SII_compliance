from pathlib import Path
import json,datetime,os
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY84_PREFIX_CRITIC83_20261030'
def read(p):return json.loads(p.read_text())
s=read(D/'SAVE_SNAPSHOT.json');a=read(R/'docs'/(TAG+'_SAVE.json'));g=s['guard'];steps={m:r['steps'] for m,r in s['cycle84'].items()};prefix=read(B/'runs/parameter_recovery84_first5000_20261030_v1/REVIEW.json')['methods'];pop=read(B/'runs/recovery82_83_old_terminal_population_20261030_v1/REVIEW.json')['methods'];obs=read(D/'OBSERVATION_FINISHED.json');stamp=datetime.datetime.fromtimestamp(s['time'],datetime.timezone.utc).isoformat()
pr=[];cr=[]
for m in ['impedance','admittance','vmc']:
 q=prefix[m]['metrics']['agent_train/q_loss'];ac=prefix[m]['metrics']['agent_train/actor_loss'];pr.append(f"|{m}|{q['first1000']:.6f}→{q['last1000']:.6f}|{q['maximum']:.6f}|{ac['first1000']:.6f}→{ac['last1000']:.6f}|")
for c in range(5):
 v=pop['vmc']['critics'][c];ad=pop['admittance']['critics'][c];cr.append(f"|{c}|{v['sse82']:.6f}→{v['sse83']:.6f}|{ad['sse82']:.6f}→{ad['sse83']:.6f}|")
fp={m:(v['completed_conditions'],v['condition'],v['actions']) for m,v in s['frozen82'].items()}
text=f'''# 第84轮前缀与第83轮旧终端critic退化定位

{stamp}，Goal active。原第84轮三路继续，保存steps `{steps}`，没有重启或改配置；冻结82全90评测、原82–84窗口及其标量bootstrap继续。上一轮[完整83交接](RL_RECOVERY83_COMPLETE84_RUNNING_20261030.md)的所有成功、失败与限制保留；本轮增加诊断与前瞻跟踪，不把前缀改善当作完整收敛，无85训练/Direct34。

主机 `{s['host']}`，解释器 `{B}/env/bin/python`。数据/runtime/checkpoint/raw在共享SSD `{B}`。开工实际ls-remote、fetch/read main `00dad983a9d1b29c99a81e8ff02341089684da15` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，保留另一主机非RL。按sii-research-sync执行，无子agent。最终发布成功以SSD本轮PUBLICATION.json为准。

固定前5000位于 `runs/parameter_recovery84_first5000_20261030_v1`。注册在训练启动且该前缀可用后，长度保持原5000，未依结果选区段。三路原日志字节完全一致、连续step、全部数值有限、math.fsum独立算术通过，实际六栏图已查看。

|方法|critic首1000→末1000|最大|actor首→末1000|
|---|---|---:|---|
{chr(10).join(pr)}

阻抗仍有反复有限尖峰且actor近乎平坦；导纳critic/actor略下降；VMC早期均值较高后回落、actor基本平坦。仅前缀，不证明完整84稳定或health通过，不取消83尖峰/Strict退化/VMC旧终端退化，也未设置新健康阈值。

`runs/recovery82_83_old_terminal_population_20261030_v1` 固定两方法全部2454旧终端、全部5critic。原anchor82与values83的index、完整57维features/actions、reward/mask、q_before及分母绑定通过；保存每行q82/q83/mask/SSE/差值，并按原2424/82新增30、终端reward正负、critic完整分解。注册时已知83结果，top10是事后描述排序，全部样本保留。独立标量重算、序列化原数组复核和实际两栏图通过，无新forward、physics、optimizer或replay写入。

|critic索引|VMC旧2454 masked SSE：82→83|导纳旧2454 masked SSE：82→83|
|---|---|---|
{chr(10).join(cr)}

VMC净增加18250.859074集中于critic3（第4个网络），该critic增加21783.632297、末误差约460.33倍，其余四个均改善；不能把ensemble总量变化理解成每个critic都变差。1834条SSE增、620条降，正增量21526.138613、负增量−3275.279539；最大的10条占所有正增量66.437%，不能据此删其余样本。mask内Q与终端reward异号数2→5，5个新异号均在critic3，描述性记录而非新合格门。

VMC在82之前的2424旧终端SSE4120.688079→22385.251703；82新增30却32.626507→18.921957。负终端reward组1106条误差增加15268.850324、正组1348条增加2982.008750。最大三条退化replay index3147999/319159/3189615均负终端reward；未取得其完整行为标签时，不把reward符号直接替代Task或Strict标签。所有旧2454在83全部41250更新之前已存在，但实际minibatch抽样未记录，不能声称每条得到充分抽样或确定梯度原因。

导纳873条增、1580条降、1条不变；2424更早旧终端3101.081649→2379.603018，82新增30从7308.686534降至152.135220。原82 `long0300` 的同一replay index3402499，SSE6648.777871→0.801993；原四个mask内Q由正变为接近−28.32657的负值，mask外critic1仍14.0437但该行不参与它的训练。这符合原82最后写入仅一次更新机会后的后续拟合改善，不证明收敛或解释策略行为因果，也不用于淡化VMC更老样本的真实退化。

两方法2454×57特征均无完全相等行：字典精确浮点值分组与独立NumPy unique一致。仅排除这批保存特征的精确重复冲突，不能排除近似混叠、表示不足或其他未观测冲突。SAVED_REVIEW中24540计数指两方法×2454行×5critic的配对，共49080个82/83单值；COUNT_CLARIFICATION保留字段解释，科学数据未改。

新增 `runs/recovery82_84_fixed_terminal_critic_followup_20261030_v1` 在84运行、完整84未知时登记，选择同一原2454旧终端、两方法所有5critic，比较82/83/84，不只挑critic3或成功样本。基于已审83anchor和未来84原终端values，不做额外神经forward/physics/训练。原84完整审查和两个终端审查成功且原进程退出后，才生成完整配对、每critic/SSE/异号计数与独立保存算术；原monitor注册+14400秒截止不延长。实际缺完整84拒绝已验证，源码AST/导入可执行，等待器身份已检查。当前只是已登记等待，完整84输出尚不存在；没有新增收敛门、没有自动85。

观察器11样本/{obs['elapsed']:.3f}秒，原17个身份保持、训练步数单调、保存观测逐行回读；自然结束，不停止科研、不因观察结束重派发。保存时还核新增critic等待器和四guard worker，共{len(s['identities'])}个身份。冻结82进度(完成条件,在途条件,动作)为 `{fp}`，完整90结果和最终全learner/replay内存不变证明仍待。原完整保存raw审计、55→82比较等待器继续；不把startup、前几个失败或进度文件当完整评测结论。

原82–84 PLAN SHA `ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c`、seed2026102855、5000bootstrap、nearzero1、5%与原截止保持。76–78 I近零不可判/A失败/V仅reward通过但loss未证；79–81 I描述通过/A,V失败；partial75/74–76不可判及79安全中止保持。4m append-only、23/47历史标记、terminal128、batch65536、UTD1、LR/reward/masks/physics/filter/gates不变。

Direct33数值阶段接受、冻结全30 Task/Strict0/0，原中断28最终内存不变证明缺失继续披露，不启动34。指定ESN仍缺，不用另一主机非RL模型替代；充分训练、完整冻结验证和最终公平比较仍未完成，Goal active。

GPU本轮{g['samples']}样本，最低{g['minimum']}%、低于50次数{g['below50']}、末值{g['last']}%；原v7和四worker身份核验。含合成补载，科学完成后继续运行；不是纯科学吞吐，不保证采样间每瞬时，历史低谷/预热0保留，也不是重启服务。

归档helper初稿误用不存在的train/INITIAL_STATE.json，在打包/收据前拒绝；已改为实际method/INITIAL_STATE_REVIEW.json，初稿/初始快照/部分拷贝保存于SSD，重新建立最终证据目录，无科学重启或数值改变。

共享SSD小证据 `{a['archive']}`，{a['members']}成员/{a['bytes']}字节，SHA256 `{a['sha256']}`；逐tar成员/AST核验。含本轮诊断输入小数组及原完整83归档收据；大checkpoint/raw/replay仍原共享SSD，非HDD/arm1全备份。Git强制纳入ignored nested runs；HDD LATEST仍254字节原位更新。运行进度均为快照。

下次先核84/冻结82/窗口/所有审查和guard的PID/start/FAILURE/FINISHED与样本时效。完整84后查看full reward/loss/health/两终端/全标签/实际图、原82–84窗口及标量复核、新固定2454逐critic跟踪；再作下一有限阶段的具体决定，不自动85或仅依首5000。冻结82按原90与原截止继续，最终证明/保存审计/配对未齐前不报最终结果。发布前fetch/read并保留另一主机工作。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 84前5000与83旧终端逐critic诊断

- [交接](docs/{TAG}.md)。84前5000原字节/连续step/独立算术/实际图通过，critic I2.949788→2.876221、A1.435059→1.349944、V1.098345→.901984，仅前缀非收敛；84steps{steps}。
- 全2454旧终端×两方法×5critic标量/原数组/图核验：V退化集中critic3，SSE47.424→21831.057，其余4改善；更早2424退化而82新增30改善。A原82long0300同一旧行6648.778→.802，实际抽样未知，不作因果。新84同2454/all5跟踪已登记等待、缺完整84真实拒绝通过；无自动85/Direct34，Goal active。
- 11样本/{obs['elapsed']:.3f}秒原17身份保持，最终含新等待器/worker共{len(s['identities'])}身份；GPU{g['samples']}样本min{g['minimum']}%、低于50{g['below50']}，科学完成仍合成保载。SSD{a['members']}成员/SHA{a['sha256'][:8]}核验、非HDD/arm1全备份；main00dad983/baselinef6e8f8c已fetch/read，发布见SSD收据，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');size=p.stat().st_size;assert size==254;data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert len(data)<=size
if len(data)<size:data+=b' '*(size-len(data)-1)+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254
print('Wrote detailed report, logs and254byte recovery pointer')
