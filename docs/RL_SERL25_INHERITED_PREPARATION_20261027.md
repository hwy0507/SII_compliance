# Direct24监控入口更正与25继承容量准备

2026-10-27 04:00 UTC。Goal active，无子agent。当前正式训练仍为Direct23和参数38；本轮没有新增训练、物理回合或重复辅助更新。

## 已修正未执行的Direct24启动器

`B/runtime/launch_serl_capacity24_20261027.py`原先误调用`setup_serl_batch23_monitors_20261026.py`，现已改为已登记的`setup_serl_capacity24_monitors_20261027.py`。正式24尚未启动，原23和24准备等待进程未变。

`B/runs/serl24_capacity_preparation_registration_20261027_v1`保存原启动器、`REGISTRATION.original_before_monitor_fix.json`和`MONITOR_PATH_CORRECTION.json`。当前REGISTRATION仅更新launcher hash并链接更正收据。原launcher SHA 14ea0797fe4c000eddb2f1a709bb2bed57f96111a3ce04252cfa464a5fe12fe7，新SHA c02ee9d84743ae32c7831b6204e0622125c8f1061c5ce19b5f3a91cc18d6f61f。

实际launcher AST目标、setup中24 run/archive/review路径、五个模板的AST与冻结manifest hash核对通过。已验证的capacity driver/helper、辅助验证REVIEW与全部当前训练文件不变；没有重跑已完成的replay-only或learner更新验证。

## 25仅完成未来入口准备

`B/runs/serl25_inherited_capacity_preparation_20261027_v1`保存REGISTRATION、STATIC_REVIEW和实际构建/检查脚本。三个新入口位于`B/runtime`：prepare_serl_capacity25_20261027.py、launch_serl_capacity25_20261027.py、setup_serl_capacity25_monitors_20261027.py；四个模板和MANIFEST在`B/runtime/serl_capacity25_monitor_templates_20261027_v1`。

25从准确完整24续一个有限原设置周期。准备入口要求完整24 REVIEW/FINISHED/DIAGNOSIS、父checkpoint/hash/完整boundary、旧2m replay marker、size/cursor/steps一致和下一41250容量余量。继承整个replay_capacity_stage，历史entry仍23；原batch历史12保持。driver/helper仍受已有准备证据精确hash约束。实际check-only调用原capacity driver进行全state/下一65536/RNG恢复核验，尚未执行。

startup与fullreview改为旧/新均2m，核对父REGISTRATION hash等于旧checkpoint protocol hash、历史capacity stage完全相同、当前父为24、历史entry为23、父与entry checkpoint引用hash。保留全部旧raw/derived/history、新reward/action/clock审查和`methods.direct.replay_capacity`字段，兼容已登记24–26固定窗口。fullhealth预期780终端。25不重跑24的首次跨1m边界审查。

验证覆盖七份脚本AST、launcher实际指向setup、setup输出路径与四模板hash、准确24父/25目标/原batch65536、780终端。对两模板抽出的实际容量guard分别执行1正例及12错误元数据负例：错父cycle、partial父、legacy1m、丢旧marker、旧cursor、错protocol hash、重标entry、错registration引用、错当前父、错checkpoint引用、丢新marker、新cursor。均正确拒绝。全部是明确标记的元数据fixture，不是完整24实际恢复证明；0优化/物理。

25尚无waiter或正式训练。待24真实LAUNCH/MONITORS身份可用后登记有界恢复等待/释放CPU调度；不能虚构父PID，不能直接自动训练25。正式25仍需阅读完整24科学结果、容量边界证据、实际check-only后写PRELAUNCH。

## 原任务保持运行

04:00:22 UTC快照：Direct23 965482steps/7683864critic更新、0完成/30运行；参数38 I/A/V为1585488/1584789/1585956steps，均0完成/30运行。冻结32完成24/25/25条件，原90回合继续。18个原训练/归档/审查/准备/稳定性进程全部存活，完整身份与进度见小证据FINAL_LIVE_STATUS.json。瞬时GPU65/0/82/82%，存在checkpoint/采样瞬时波动，不用快照或前轮平均宣称每时刻≥50%。本轮未新增GPU观测窗口或人为占用任务。

原Direct23 learner257351/archive257407/review257409；24仅恢复准备1003919与CPU调度1003920。原参数38 I1714249/A1714251/V1714253、archive1714320/review1714322；39仅准备1752770/CPU调度1752771。固定参数36–38 2889814、Direct24–26 1470790、冻结32 2466385/6/7及根2466388继续。启动/观察已完成的原进程不重启。

下一优先：实际完整23→24与完整38→39。读原REVIEW/health/图和必要稳定窗口后接续，记录真实换轮空档；不让本轮文档准备阻塞接续。完整24恢复、24首次跨1m边界、25实际恢复/部署、原固定窗口及冻结32全量审查仍待。整体健康收敛未达到。

## 位置与同步

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。小证据在B/repository/SII_compliance/docs/evidence/RL_SERL25_INHERITED_PREPARATION_20261027，含更正前后原件、25三入口/四模板、验证脚本/登记/检查结果和现场状态。原capacity准备证据及38结果沿用[前轮交接](RL_PARAMETER38_CAPACITY_WINDOW_20261027.md)和[容量准备](RL_SERL24_CAPACITY_PREPARATION_20261027.md)。

本轮真实ls-remote/fetch/read main=a3e9e0440506c60eea6c7bcfab9895846706e420、baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，未发现新远端更新。HDD配额满；新归档/HANDOFF在SSD，现有HDD LATEST仅更新指针。大checkpoint/replay/raw仍SSD，不宣称HDD/arm1全备份。提交、push与新归档收据另记。
