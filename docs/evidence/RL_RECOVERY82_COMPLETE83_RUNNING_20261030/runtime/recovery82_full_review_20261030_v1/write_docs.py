from pathlib import Path
import json,datetime,os
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY82_COMPLETE83_RUNNING_20261030'
def read(p):return json.loads(p.read_text())
s=read(D/'SAVE_SNAPSHOT.json');a=read(R/'docs'/(TAG+'_SAVE.json'));steps={m:r['steps'] for m,r in s['cycle83'].items()};g=s['guard'];stamp=datetime.datetime.fromtimestamp(s['time'],datetime.timezone.utc).isoformat()
O=B/'runs/parameter82_frozen_full30_20261030_v1';frozen=read(D/'FROZEN82_OBSERVATIONS.jsonl') if False else [json.loads(l) for l in (D/'FROZEN82_OBSERVATIONS.jsonl').read_text().splitlines()][-1]['progress']
text=f'''# 完整82已审；有限83与冻结82全90评测运行中

{stamp}，Goal active。第82轮三路完整审查已完成，但尚无三路reward稳定及loss健康共同成立的证据。已明确登记一个有限第83轮并实际启动，startup和120秒观察通过，保存时steps为 `{steps}`。冻结第82轮全90评测也已实际启动；其完整结果、最终内存状态不变证明及55→82逐条件比较仍待完成。无自动84，无Direct34。

执行主机 `{s['host']}`；解释器 `{B}/env/bin/python`。checkpoint/replay/raw与小证据均在共享SSD `{B}`，不是HDD或arm1完整备份。开工实际查询、fetch并阅读main `034889ab336719db28a3ceb55555b2bd833572d5` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；保留另一主机非RL工作。按仓库sii-research-sync保存发布，无子agent；实际提交、成功push及发布后远端SHA见SSD本轮目录PUBLICATION.json，未核对之前不宣称发布成功。

|第82轮方法|steps|reward均值|Task/Strict（各30）|critic首→末1000|critic最大|
|---|---:|---:|---|---|---:|
|阻抗|3400198|−2.3890678941943313|18/17|2.520469→2.379630|45.268295|
|导纳|3402500|−13.677125448499165|11/11|1.673723→1.246200|20.430441|
|VMC|3403500|−2.805261616881281|17/17|0.789073→0.810406|26.374348|

三路各30完整55s回合、各41250新增，无安全中止；所有旧回放字段精确保持，冻结reward重建误差0，网络/optimizer数值有限。完整loss与独立保存算术、健康诊断、180标签/90配对及两额外focus共182保存rollout检查、V/A完整终端跟踪均完成，loss/health/两terminal实际图已查看并写收据。上述回放/reward核验不等于独立重建全部物理子步。

阻抗与VMC标签不变；导纳Task15→11、Strict13→11：short0200、long0200、long0300从Task/Strict成功变失败；short0600 Task成功变失败、Strict仍失败；short0000 Strict改善，相关穿透0.231342→0.138090mm。导纳physical_valid由28→30，但任务退化仍成立。阻抗actor23.204442→22.397885持续下降，导纳−8.593291→−8.785487先降后平，VMC−12.504310→−12.318483上漂。有限尖峰保留，不凭尖峰自行增加健康失败门槛，也不把较低loss当行为改善。

固定alpha诊断采样Q超全局上界比例I0%、A0.05371094%、V0.18554687%；终端mask内MAE0.284903/0.297351/0.176954，mask外3.410413/2.461932/1.813333。mask外是对应critic未参与训练的行；这是诊断，不设置终端零误差门。

完整82 checkpoint位于 `runs/parameter_partial75_recovery_cycle82_archive_20261029_v1/<method>/cycle_00082.pt`，SHA256：

- I：`e5ecda2add46cef31c43d1fc1c4eaf127c25927ada73da16de3cf40c06726c76`
- A：`cfde4b502b22e85eb08f2187bc868763ff4ddf0724bea981e88d759974d6c02b`
- V：`4d21592f534f9f1ee475561d8fbfb914d86a488027691be28022939119a10ae8`

固定旧2424终端的masked SSE：V6075.664681→4120.688079，A13177.624979→3101.081649，原/新回放分母均保留。总体下降同时存在个别退化：V原focus2423122从2.967658→2896.964431，A原focus2752093从4.787523→9.374596。完整82新增30终端逐episode映射、标量贡献复核通过：V贡献0.001403962468；A0.314634929551，其中long0300占90.966709%、long0671占8.043365%。这定位末checkpoint误差集中样本，不能解释历史在线minibatch或策略退化因果。

原76–78仍I近零不可判、A5%失败、V描述性reward通过但loss健康未证；原79–81 I描述性5%通过、A/V失败。新增 `runs/recovery76_81_bootstrap_scalar_review_20261030_v1` 重建每方法每窗口5000个分层draw，验证integers与原choice等价，使用math.fsum和排序插值独立核对区间端点误差≤1e−10。六份压缩draw/value证据保存。共用NumPy RNG实现，不是独立训练seed、不是冻结策略推断；不改历史原结论或79真实短回合。原74–76因partial75不完整仍不可判。原82–84 PLAN SHA `ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c` 保持，原等待器与新标量bootstrap补充等待器继续；只有82完成，83在途、84未启动，不能提前报告窗口结果或延长原deadline。

第83轮决定在 `runtime/recovery83_completion_preparation_20261030_v1/DECISION83.json`，明确绑定完整82解释、原窗口、实际四张图和三路精确恢复。旧partial75、容量23/47标记、4m append-only、terminal128、batch65536、UTD1及LR/reward/masks/physics/filter/gates保持；每方法仅一轮30条件×最多55s/41250新增。全learner/replay/next65536准确恢复及原拒绝检查通过，实际startup通过，三路训练和全loss/health/标签/终端后续已部署；V/A完整82锚点2454保存算术通过，完整83预计2484。120秒7样本观察保存回读通过，全部原身份保持。完成观察不停止科学进程。

冻结82预登记在完整82 checkpoint和全审查前写入，已知部分进度，未按全82结果选模型；PRE_REGISTRATION SHA `baf37d1715635e1d5352deea7434b33e36e666c4c0d3036f43f404b685935b76`。复用原55的30条件、动作seed2026102638与核心依赖；新evaluator物理/动作循环逐字相同，新增恢复metadata校验每方法12个负例共36通过。三路真实完整learner/4m replay与外部RNG check-only通过，实际启动时再检查通过；无优化更新及正式回放写入。CPU0/1/2、GPU0、每进程torch1，预检查无重复、内存/显存足够且与83CPU13–51分开。最大90回合/123750动作/99000000物理子步，55s、dt5e−5、actor0.04s，失败/中止全部纳入。

冻结评测路径 `runs/parameter82_frozen_full30_20261030_v1`，源码 `runtime/parameter82_frozen_full30_20261030_v1`。实际4样本/60秒观察核验三evaluator、physics实际CPU affinity、rootreview、比较等待器及原83/window/guard身份，动作持续增加。观察末进度 `{ {m:(r['completed_conditions'],r['condition'],r['actions']) for m,r in frozen.items()} }`，不是已完成回合数。55→82逐条件比较等待器位于该run的 `comparison55_82`，保留90对、成功/失败/安全/实际人体接触分母及NA，仅描述比较；原review登记+21600s截止，不自动扩预算。

启动helper初版误把loss数值REVIEW当带passed的成功收据，启动前KeyError；已改为读取实际SAVED_REVIEW/PAIRED_GATE_REVIEW，保留初稿与修复说明。拒绝发生在任何评测派发前，没有重复physics或科学重启。完整90结果、最终全内存learner/replay不变证明、实际结果图和配对结果尚待，不能把startup检查代替最终证明。开发训练条件和单动作seed不证明泛化、收敛或最终指定ESN比较。

Direct33数值阶段接受、冻结全30 Task/Strict0/0保持；原中断28回合最终内存不变证明缺失继续披露，不重跑28、不启动34。用户指定ESN仍缺，不能用另一主机非RL模型替代；最终公平比较未完成，Goal active。

本轮GPU连续保存{g['samples']}样本，最低{g['minimum']}%，低于50次数{g['below50']}，末值{g['last']}%。含合成占用，不能当科学吞吐；历史v6低谷和v7预热0保留。守护 `/tmp/sii_gpu_util_guard_20261030_v7` supervisor97370/start570509460，四worker97399–97402/start570509475核验存活；科学任务完成后仍保持运行，但不是重启自启服务。

共享SSD小证据 `{a['archive']}`，{a['members']}成员/{a['bytes']}字节，SHA256 `{a['sha256']}`；所有tar成员原字节和Python AST已核验。Git强制纳入ignored nested runs小证据；大checkpoint/replay/physics仍SSD。HDD既有LATEST只原位写入254字节入口，非HDD/arm1全备份。当前运行日志归档为快照，不冒称最终结果。

下次接续按顺序检查：

1. 先核guard原PID/start及最近样本年龄、四卡利用率；科学结束仍保载。
2. 核原83 LAUNCH/PID/start、进度及所有FAILURE/FINISHED；不重复启动。完整后审reward/replay/loss/health/全标签/终端和实际图，再决定有限84；原82–84窗口不改。
3. 核冻结82三evaluator/rootreview/comparison原身份；收齐90结果和全内存最终不变证明，查看结果图，逐条件核55→82。如运行中断，保留部分结果与缺失证明，不能用startup证明冒充完整。
4. 继续原82–84数值窗口及其标量bootstrap补充；保留75/79/Direct33的历史限制、指定ESN和最终范围。同步Git前再次fetch/read，保存另一主机工作；不把本轮进展写成Goal完成。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 完整82已审；83续训与冻结82全90实际运行

- [交接](docs/{TAG}.md)。82各30×55/41250/noabort、旧replay/reward0误差、完整loss/health/182保存标签/两终端与四实际图已审；I/A/V reward−2.389068/−13.677125/−2.805262，Task/Strict18/17、11/11、17/17。导纳loss降而Task15→11；新30终端误差long0300占90.97%，不作因果或收敛声明。
- 原76–81全部5000bootstrap抽样/标量区间独立复核通过，不改原结论；明确有限83决定/三路精确恢复/实际startup及120秒观察通过，steps{steps}，全后续已部署。冻结82预登记后全state/RNG检查与36负例通过、全90评测已实际启动及60秒观察通过，结果/最终不变证明/55→82比较待；启动前helper字段错误修正保留，无重复科学。无自动84/Direct34，Goal active。
- GPU{g['samples']}样本min{g['minimum']}%、低于50{g['below50']}，科研结束仍合成保载；SSD{a['members']}成员/SHA{a['sha256'][:8]}逐字核验，非HDD/arm1全备份。main034889ab/baselinef6e8f8c已fetch/read，发布以SSD PUBLICATION收据为准，保留非RL，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';old=p.read_text();line,rest=old.split('\n',1);p.write_text(line+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();size=p.stat().st_size;assert size==254 and len(data)<=size;data=data+b' '*(size-len(data)-1)+b'\n' if len(data)<size else data
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254
print('Wrote detailed recovery, AGENTS/log/HANDOFF/primary and254-byte HDD pointer')
