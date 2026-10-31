from pathlib import Path
import json
D=Path(__file__).resolve().parent;B=D.parents[1];rd=lambda p:json.loads(p.read_text());o=rd(D/'OBSERVATION_REVIEW.json');c=rd(D/'PROCESS.json');binding=rd(D/'COMPLETE95_BINDING_REVIEW.json');assert binding['passed'];growth={m:o['last']['steps'][m]-o['first']['steps'][m] for m in o['first']['steps']};F=B/'runs/census96_fixed95_terminal_20261031_v1';w=rd(F/'LAUNCH.json');plan=rd(D/'WAIT_PLAN.json')
entry=f'''## 2026-10-31 — 第96轮继续；全90比较/终端计数与完整95窗口输入已核验

- [交接](docs/RL_CENSUS96_COMPARISON_20261031.md)。全95→96的90条件reward分项/Task/Strict/abort/原loss比较登记；真实完整95全90模型/标签/算术、缺完整96拒绝通过。唯一比较等待器{c['pid']}沿修正版archive原截止，完成后自动检查全部96终端计数/回放，零新增训练。
- first5000每步terminal_population与原8533分路总数+done累计精确，15损坏输入拒绝；无真实新终端，增长仍待。原30源码和实际trainer顺序通过，在线32分层tensor未记录，不声称已观测。
- 原固定94–96的完整95三组输入按原逐组AST逐句核验，真实三checkpoint加载、94父链精确；94旧refs重新hash，六组map被原全九组门拒绝。无最终REGISTRATION/统计，A94→95的19.7689%必要条件失败保持。
- 101身份连续{o['elapsed_s']:.3f}s/{o['samples']}样本保持，steps增长{growth}；原三训练、修正版archive和两个只读等待继续。完整96/loss健康/收敛待；4m不足完整97、原gamma消费者失败修复、全部历史失败、Direct原结论与指定ESN缺失保持，Goal active。
'''
(D/'ENTRY.md').write_text(entry)
body=f'''# 第96轮全90比较、终端计数与完整95窗口输入

第96轮原三路训练继续；本轮零新增科学训练派发，诊断零physics/optimizer更新。原learner/90sampler/guard没有重启，Goal active；完整96与reward平稳/原loss健康的联合验收仍待。

## 全部90个条件的比较准备

`{D}/COMPARISON_PLAN.json` 绑定完整95全部review/health/loss/真实图检查、三份96协议、原94–96意向及A早期失败、修正版archive来源。完整95的90条实际rollout成功标签、abort、stage、模型hash、冻结条件和reward分项算术/均值/总数已核验，Task/Strict为I18/17、A15/15、V17/17。96协议相对95只允许post_interruption_continuation变化，census amendment完全相同。

缺真实完整96的检查正确拒绝。唯一等待器PID{c['pid']}/start{c['start']}，绑定修正版archive PID{plan['original_monitor']['pid']}/start{plan['original_monitor']['proc_start_ticks']}，截止{plan['deadline']}沿原96启动+14400秒，不延长原截止。完整96 REVIEW/health/loss/FINISHED通过后：interpret96.py覆盖全部90个条件reward与分项、Task/Strict/abort和原抽样/条件估计/actor loss；changed_cases.py核验全部标签变化的原两轮rollout、穿透与模型hash；保存汇总独立复算后生成图。每消费者600秒上限，最终图仍需实际查看。

完整比较尚未运行，不是96结果。两轮估计器相同，原loss健康均读取original_sampled_q_loss；reward分项差值只是算术分解，不是因果证明或固定94–96稳定性结论。

## 终端计数与真实日志绑定

基准为完整95全部8533终端indices/masks（I2845/A2844/V2844），来自 `{F}/reference95`。真实96 first5000的每一步terminal_population与父总数加包含当前步的done累计相等，原日志前缀再次读取字节一致。三路此前缀没有新terminal，不能据此声称真实增长。

缺更新、错步、错计数、漏掉终端增长和错父总数共15损坏输入均被拒绝。核验30份原锁定源码及实际trainer，确认replay.add/cache同步在该步learner.update和optimizer日志之前；这是inclusive累计的代码依据，实际增长仍需done事件。

比较等待器在完整96全90分析后自动执行check_terminal_population.py --complete：全部optimizer行与transition配对，完整96 replay所有done、新done累计、全部旧终端indices/masks、每方法30新终端及32种mask分层存档计数逐项绑定。完整检查尚待原训练完成；在线逐分层tensor未记录，不能冒充已观察其内容。

## 原94–96窗口的完整95输入

复用锁定的binding_rules.py，从validate_registration内抽取原逐组检查AST并逐条确认完全相同，未改变外层九组门槛、窗口、阈值或统计kernel。真实完整95三个组分别绑定protocol/review/health/finished、全部30episodes/41250optimizer、loss与health两张实际图及检查、完整checkpoint，共每组11类来源。三个完整checkpoint均实际加载，census与架构/回放52/4m/counters/完整边界通过。

此前完整94三组检查仍保留；本轮重新hash其全部引用，与真实95父checkpoint/协议/steps链精确相连。`{D}/COMPLETE94_95_INPUT_MAP.json` 含六组；原全九组验证器仍明确拒绝“All nine complete input groups required”。尚缺完整96三组，无最终REGISTRATION、bootstrap或稳定性结果。源、原AST提取与结果见EXTRACTED95_GROUP_SOURCE/COMPLETE95_BINDING_REVIEW。

原94–96、5%/nearzero1/5000bootstrap/seed2026102861保持。意向原登记在94启动后首完整回合前，不补造启动前登记。A94→95 reward相对变化19.7689%已违反原5%必要条件；完整95输入通过不改变这项失败。最终仍须九组完整绑定及原统计，不将六组检查冒充全窗口通过。

## 运行证据与后续

101个身份（原3learner、90sampler、5guard，之前修正版archive，原固定8533终端等待器及本轮新增全90等待器）连续{o['elapsed_s']:.3f}s/{o['samples']}样本保持，steps增长{growth}。固定终端等待器PID{w['pid']}/start{w['start']}继续，覆盖全部8533旧终端、all5/original masks、≤94/new95及79/90/92中止和93放置失败；完整96终端比较尚未产生。

原startup/review误写gamma=.9996及其observer失败继续保留，正式训练始终gamma=.9995；独立修正只读消费者后，原训练未重启。本轮适配按Python token处理轮次，浮点常量不变、hash和原94–96窗口保护，修正版archive与cache计划哈希明确绑定。

下一步继续原96，核验真实新terminal增长、完整loss与实际图、全90与固定终端比较，完成原94–96九组绑定/统计。现有append-only4m可容纳96，但完成后I/A/V仅余23488/20000/19000，不能再装完整97；容量另作决定，不覆盖旧数据。无自动97/Direct34。

原physics/MJB/Task/Strict/canonical48/filter/执行器限制/dt5e−5、actor49/critic52、clock/history/rawbit、原LR/reward/masks/terminal128/batch65536/UTD1、census及23/47容量标记不变。中断保全最新96 partial权重/Adam/RNG/replay/journals，另登记续接，不回退95；MuJoCo物理state未保存。

Direct33原数值验收保持，冻结全30 Task/Strict0/0；旧28缺完整memory-invariance证明、恢复2已证，指定ESN缺失，最终独立对比仍待。原90–92以及后续全部失败和非优势结果保持。
'''
(D/'REPORT_BODY.md').write_text(body)
print('Report generated from comparison/population/window bindings and actual101-identity observation')
