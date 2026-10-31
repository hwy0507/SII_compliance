from pathlib import Path
import json
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle96_20261031_v1';rd=lambda p:json.loads(p.read_text())
Q=B/'runtime/census96_consumer_repair_20261031_v1'
ob=rd(Q/'ONLINE_OBSERVATION_REVIEW.json');s=rd(R/'startup_repaired/REVIEW.json');decision=rd(D/'SCIENTIFIC_DECISION.json');growth={m:ob['last_steps'][m]-ob['first_steps'][m] for m in ob['first_steps']};added={m:x['added_steps'] for m,x in s['methods'].items()}
entry=f'''## 2026-10-31 — 完整95精确接续：有限96实际训练，原94–96窗口与失败保留

- [交接](docs/RL_CENSUS96_ONLINE_20261031.md)。完整95 learner/Adam/RNG/全部回放精确恢复，每方法一轮≤41250/30×55s；实际trainer只改预算异常轮次文字，census与原科学设置不变，无辅助权重/自动97/Direct34。95原loss尖峰、A long0900失败和历史退化保持，尚未收敛。
- 111错误协议/父状态拒绝、6真实65536 batch隔离重复及完整state恢复、三CPU消费者、原94–96协议检查通过。startup新增{added}，全部旧回放/新52/action/reward0误差、30MJB/30sampler/容量23和47及架构marker通过；真实新终端增长仍待。
- {ob['identity_count']}身份（原训练/采样/guard与修正版archive）连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}，末{ob['last_steps']}；三正式/archive继续。A94→95 reward变化19.7689%已违反原5%必要条件，不移窗口；完整96/九组绑定/统计和loss健康待。4m可容纳96，完整97无法容纳，须另作容量决定。
- 原startup因检查脚本gamma误写.9996失败、observer随之退出；实际三checkpoint保持.9995。失败原件保留，独立修正只读消费者/替换等待archive并保持原截止，3learner/90sampler/5guard未重启。
- 中断须保全最新96 partial，不回退95。Direct33原数值/冻结全30 Task/Strict0/0、旧28 memory证明缺口、恢复2已证及指定ESN缺失保持；Goal active。
'''
(D/'ENTRY.md').write_text(entry)
report=f'''# 完整95全状态接续有限96（2026-10-31）

三路正式96已实际运行，从完整95归档继承全部权重、Adam、RNG、回放和cycle历史，每方法新增上限41250、30×55秒。Goal active；本轮完成不等于训练收敛，没有自动97或Direct34。

## 科学依据及原窗口

完整95三方法各41250新增/30完整55s/0中止，Task/Strict依次18/17、15/15、17/17，reward均值−2.406230444/−6.869399105/−2.863009951；原抽样loss均值1.017087107/1.028280842/.720578185、最大3.434057951/1.567340136/1.229327083。I反复尖峰和actor变化仍在，A大致持平略降、V晚段凸起后回落；不能从actor变化单独推断实现错误或稳定。

固定全8443个94终端、all5和原mask的masked SSE在95下降40.5176%/22.9213%/19.2540%，仍有1194/1463/1185条样本及部分critic退化。I旧90中止残差560.052→260.108仍大，79和93样本小幅退化；这是历史回放拟合，不是独立泛化。全90条件比较保留A short0000 Strict增益、short0200 Task/Strict恢复及long0900 Task/Strict丢失，I/V标签不变。原95所有证据及失败保持。

原94→95 reward相对变化I2.868972%、A19.768884%、V.472855%，A已违反5%稳定必要条件。继续完成原94–96窗口以核验完整三轮及I/V结果，不移动窗口、降低阈值或删去A失败。原意向在94启动后、首完整回合前登记；5%/nearzero1/bootstrap5000/seed2026102861及锁定统计源码保持。实际96三份协议已通过原binding_rules；这不是完整九组绑定或最终统计。

## 恢复与代码范围

完整95的三个checkpoint及原95源码、登记、完整科学/终端审查均hash绑定。新driver使用严格load_state_dict恢复；实际trainer相对95只改 `Finite95 new-transition budget exceeded` 为 `Finite96 new-transition budget exceeded`，训练/采样计算逐字保持。census_native.py及版本marker与95相同，top amendment仍引用原94来源。初始完整learner/replay digest相等，CensusCache从完整回放重建派生终端索引；没有使用辅助拟合权重。

固定physics/MJB/Task/Strict/canonical48/filter/执行器限制/dt5e−5，actor49、critic/replay52（clock49/history50/rawbit51）、原LR/reward/masks/terminal128/batch65536/UTD1保持。append-only4m回放与23/47容量标记保持。

|方法|完整95父steps|完整96预计steps|96后剩余容量|GPU|Learner CPU|Sampler CPU|
|---|---:|---:|---:|---:|---:|---|
|impedance|3935262|3976512|23488|1|13|14–25|
|admittance|3938750|3980000|20000|2|26|27–38|
|vmc|3939750|3981000|19000|3|39|40–51|

现有容量可容纳完整96，不能再容纳完整97；下一轮必须另作容量决定，不能覆盖旧数据或无界追加。

## 检查与真实运行

111个错误协议/父状态均被拒绝，包括错误cycle/seed/控制器/完整边界/更新数/预算、缺失或损坏census/双架构marker、51维回放、容量/cursor/父protocol来源错误。三方法各两次真实65536 batch隔离更新精确重复，全部learner/replay/RNG恢复，共6次隔离更新、0预检physics/正式更新。三个CPU消费者完整恢复，在随机推理后还原RNG且无梯度。

启动前确认无95/96重复driver，容器可用内存超过128GiB、swap0、每卡显存余量超过10000MiB，guard五个PID/start身份保持。正式启动后实际startup新增{added}，全部旧回放逐元素保持、新current/next52、clock/history/rawbit、raw与mixed动作映射、冻结reward journal重建误差0，30个MJB和每路30sampler/CPU集合、原优化器设置与双loss字段均通过。公共七维动作只核验shape/finite/bounds和I零桥接，不冒充A/V控制器内部动力学重演。

{ob['identity_count']}身份（原3learner、90sampler、5guard及替换后的archive）连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}，末值{ob['last_steps']}。三learner与archive继续。startup前缀尚无新终端，真实terminal_population增长需后续完整回合检查。

唯一启动记录 `{R}/LAUNCH.json` 含实际命令及PID/start；源 `{D}`。修正版归档器将等本轮结束后复制完整checkpoint并核验hash，执行完整replay/episode/reward、health和双loss审查；实际图检查及完整保存算术仍待，FINISHED不能替代健康或收敛判断。

## 原消费者失败与独立修复

原startup在检查finite_target_projection时失败：轮次字符串替换错误地将审查脚本中的gamma=.9995改成了.9996，原observer因startup退出而失败。实际三份checkpoint逐一加载均保持gamma=.9995；全部训练helper与95逐字相同，实际执行trainer只变更错误消息轮次。没有发生训练科学参数修改。

原startup/review源码与SOURCES锁保持不改；原startup的impedance快照、traceback和OBSERVATION_FAILURE均保留。`{Q}` 保存FAILURE_REVIEW、REPAIR_PLAN、SOURCE_LOCK和修正版startup/review/archive/observer。修正版startup输出 `{R}/startup_repaired`，检查预期gamma恢复原.9995。原archive尚在等待且无子进程/未开始归档时，仅按验证的PID/start终止该等待器并替换；原启动+14400秒截止保持。原3learner、90sampler和5guard均未重启，不重新训练或覆盖旧快照。修正后的99身份观察明确包括替换archive，不声称原archive身份连续。

新的完整审查由修正版review执行，其余原health/loss保持。完整96结果仍待；此次检查脚本失败不能删去，也不等于训练数值失败。复制适配时其余数值常量已审，冻结helper逐字一致，错误gamma仅位于两份只读审查器。

## 后续与中断恢复

继续核验完整96、所有新增终端、原loss全部曲线与真实图，然后绑定94/95/96全部九组输入运行原统计。`agent_train/q_loss`是条件终端估计，健康判断仍读取 `agent_train/original_sampled_q_loss`；health4096 TD为未投影固定min-pair诊断，不等于真实投影/I-min/A-V-mean目标。固定历史终端及全90条件比较须保留所有退步。原90–92失败继续保留；新窗口不覆盖旧失败。

Direct33原数值验收保持，但冻结33全30 Task/Strict0/0；旧28缺完整memory-invariance证明，恢复2已证；指定ESN仍缺，最终独立对比未完成。不替换指定ESN或提前宣称四方法完成。

若中断，先保存各train/checkpoint_latest.pt及全部journal；96已学习后不得回退95或重复整轮。当前driver仅接受完整95，partial续接要单独登记并保全权重/Adam/RNG/replay。MuJoCo物理state未保存，不声称回合连续。大型资产保留共享SSD，HDD配额满仅更新原254字节指针。

四GPU独立guard在科学任务结束后仍保持，不创建STOP；其占用不是科学吞吐证据，也不是系统重启服务。启动前草稿引用/负例轮次/health文件名已在源锁定前修正；锁定后实际暴露的gamma审查错误与退出另按上述失败记录保留。
'''
(D/'REPORT_BODY.md').write_text(report)
print('Report written from actual startup and observation evidence')
