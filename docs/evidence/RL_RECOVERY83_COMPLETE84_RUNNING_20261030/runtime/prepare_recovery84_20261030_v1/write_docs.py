from pathlib import Path
import json,datetime,os
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY83_PREFIX84_PREPARATION_20261030'
def read(p):return json.loads(p.read_text())
s=read(D/'SAVE_SNAPSHOT.json');a=read(R/'docs'/(TAG+'_SAVE.json'));steps={m:r['steps'] for m,r in s['cycle83'].items()};g=s['guard'];stamp=datetime.datetime.fromtimestamp(s['time'],datetime.timezone.utc).isoformat();obs=read(D/'OBSERVATION_FINISHED.json');ids=len(read(D/'OBSERVATION_PLAN.json')['identities']);fr={m:(r['completed_conditions'],r['condition'],r['actions']) for m,r in s['frozen82'].items()}
report=f'''# 第83轮前缀审查、第84轮恢复准备与冻结82前两个条件

{stamp}。Goal active。原第83轮训练与冻结第82轮全90评测持续运行，未重启；当前steps `{steps}`。第84轮只部署恢复检查等待器，没有训练决定或训练派发；实际完整83恢复完成标志为 `{s['actual84_restore']}`。完整reward稳定、loss健康及指定ESN最终公平比较仍未完成。

主机 `{s['host']}`，解释器 `{B}/env/bin/python`，数据/runtime/checkpoint/raw在共享SSD `{B}`。开工实际ls-remote、fetch/read main `538b1f9cb929f10be9dcfcce29fd91c9010077de` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；当前main和baseline日志已阅读，另一主机非RL工作保持。按sii-research-sync执行，无子agent。最终commit/push/远端核验以SSD本轮 `PUBLICATION.json`为准。

固定前5000审查位于 `runs/parameter_recovery83_first5000_20261030_v1`。登记发生在训练开始且前缀可用后，长度保持原5000，不按结果挑片段。原optimizer前5000字节完全一致、step连续、全部数值有限，math.fsum独立算术与保存值一致，六栏实际图已查看并写收据。

|方法|critic首1000→末1000|critic均值|最大|actor首→末1000|
|---|---|---:|---:|---|
|阻抗|2.388605→2.287125|2.417989|28.474243|22.384735→22.325774|
|导纳|1.362929→1.279100|1.283102|16.106665|−8.781615→−8.812880|
|VMC|0.863753→0.855569|0.879467|9.449438|−12.322554→−12.312119|

阻抗反复有限尖峰，导纳较低基线伴稀疏尖峰，VMC中部平滑均值隆起并有尖峰；actor I/A轻微下降、V近乎平坦而略漂移。仅前缀，不证明完整83健康或收敛，也不把有限尖峰本身设成新失败门槛。完整82的导纳Task15→11/Strict13→11、旧终端误差局部退化及全部旧窗口结论仍保留。

第84轮恢复工具在 `runtime/prepare_recovery84_20261030_v1`，原 `resume_recovery82.py`适配为 `resume_recovery83.py`，仅当前/父轮次元数据前进；科学trainer与83逐字相同，五处元数据插入可逆回原75源码，AST数字检查保留82500负例与20261078构造seed。三方法协议/parent正fixture通过，每方法19个协议负例和8个边界负例通过；实际未完整83正确拒绝且没有创建84运行目录。恢复等待器PID391261/start572443230，等待完整83归档/replay/reward/health与原learner退出，最多4小时，只执行全learner/replay/next65536恢复检查，不启动训练。

未来84 startup/archive/fullreview与健康依赖准备，实际两个health模块导入通过；完整84 loss保留49–74及76–83历史，新增84、拒绝75、配对83→84路径检查通过。23/47容量marker、partial75恢复、4m append-only、terminal128、batch65536、UTD1、LR/reward/masks/physics/filter/gates不变。

`runtime/recovery84_completion_preparation_20261030_v1`准备明确decision84/launch84/deploy_loss84，要求完整83四图及所有审查、准确恢复、原76–78/79–81结果、精确82–84 PLAN、原bootstrap标量补充及冻结82预登记。继承DECISION83证据逐hash重核；缺完整83、缺DECISION84、缺LAUNCH84三项真实拒绝通过，无决定/训练。`runtime/recovery84_followups_20261030_v1/prepare.py`仅准备84全标签和终端锚点，缺LAUNCH84会在输出前拒绝；未来锚点2484→2514，当前未部署这些followup。

冻结82仍沿用原三evaluator、rootreview和55→82比较等待器。当前 `(完成条件数, 在途条件, 已记录动作数)`为 `{fr}`，不把在途动作当回合完成。额外只读审查位于 `runs/parameter82_frozen_first2_saved_audit_20261030_v1`，在可用后固定取原索引前2条件：passive_corner_train_0000/0100、全部三方法，不按结果筛选。共6回合/8250动作/6600000子步，每回合全55s、无中止，Task/Strict均失败、stage=carry，机器违规均false；原55同seed对应6回合也均Task/Strict失败。

|方法|0000 reward55→82|0100 reward55→82|
|---|---|---|
|阻抗|−30.976670→−30.992648|−31.347764→−31.333309|
|导纳|−31.761405→−31.772078|−31.657061→−31.620324|
|VMC|−30.812739→−30.999344|−31.088898→−31.099446|

额外审查逐hash核全部原physical/filter/torque引用，共每回合12个不同证据；从原telemetry独立按计数×dt重算时长/人体接触/舒适分母、逐关节峰矩与穿透、原机器gate，以及冻结reward函数配合math.fsum，最大reward差3.56e−15。六回合实际人体接触均0，舒适比例必须NA，不解释成100%或舒适优势。未重跑native动作或物理，原动作精确重放及每回合learner不变证明从已核hash收据继承；不能替代全90结束时的最终完整learner/replay不变证明。前2被动条件不能外推全30成功率，也不是最终指定ESN比较或SPT排名。

前缀生成器初稿有语法错误，发生在解析阶段，未产生任何文件/训练/审查执行；已修正记录。复制的parent_source_sha256最初沿用旧祖先，已保留PLAN_INITIAL并更正为实际82 audit源码，执行83 audit哈希与原始数据、数值结果均未改变。未来84 followup说明中的轮次文字也在部署前纠正，科学逻辑不变。

连续{obs['samples']}样本/{obs['elapsed']:.3f}秒，{ids}个原身份保持，训练步数单调、冻结评测继续、保存观测逐行回读。观察器已自然结束，不停止科学或守护、不因观察结束重新派发。原82–84窗口和标量bootstrap等待器继续，原PLAN SHA `ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c`，不改原deadline/5%/nearzero1/seed2026102855/5000bootstrap。76–78 I近零不可判/A失败/V仅reward通过，79–81 I描述通过/A,V失败，原75不完整及79安全中止全部保持。

GPU本次{g['samples']}采样最低{g['minimum']}%、低于50次数{g['below50']}、末值{g['last']}%。包含合成守护，不是纯科学吞吐，不保证采样之间每瞬间。guard原97370/start570509460和四worker核验；科研结束仍保载，尚非重启服务。历史低谷与预热0保留。

SSD小证据 `{a['archive']}`，{a['members']}成员/{a['bytes']}字节，SHA256 `{a['sha256']}`，所有tar成员和Python AST核验；Git强制纳入ignored nested runs。大checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份。HDD LATEST254字节原位更新；运行中日志为快照。

下次先核当前83/冻结82/各审查/84恢复等待器的原PID与start、FINISHED/FAILURE及GPU样本时效，不能仅看进度文件认定存活。完整83出现后审查loss、reward/replay、health、全标签/两终端和实际四图，再填写具体CONTINUATION_REASON并执行decision84/launch84；当前尚未形成84科学续训决定，不能跳过该审查。冻结82按原90预算继续，保留所有失败和最终不变证明要求。Direct33数值阶段已接受、冻结全30 Task/Strict0/0；原28最终内存不变证明缺失继续披露，不启动Direct34。指定ESN仍缺，不拿别的主机模型替代；Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-30 — 原83前5000已审；84恢复准备及冻结82前两条件核验

- [交接](docs/{TAG}.md)。83固定前5000原字节/独立算术/实际图通过，critic首→末I2.388605→2.287125、A1.362929→1.279100、V0.863753→0.855569，有限尖峰保留、非收敛。原83steps{steps}。
- 84科学trainer逐字同83、每路19协议+8边界拒绝及实际未完整83拒绝通过；仅恢复等待391261部署，准确恢复={s['actual84_restore']}。完整84审查/明确决定/helper准备、缺前置真实拒绝，无84训练/Direct34。冻结82原前2条件×3方法660万子步保存指标/reward/hash复核，均carry任务失败、与55同标签、无人体接触故舒适NA；完整90仍在途，Goal active。
- {obs['samples']}样本/{obs['elapsed']:.3f}秒共{ids}身份保持；GPU{g['samples']}样本min{g['minimum']}%、低于50{g['below50']}，科研完成仍合成保载。SSD{a['members']}成员/SHA{a['sha256'][:8]}核验，非HDD/arm1全备份；main538b1f9c/baselinef6e8f8c已fetch/read，发布见SSD收据，无子agent。

'''
for n in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/n;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254
print('Recovery report and logs written;254-byte pointer read back')
