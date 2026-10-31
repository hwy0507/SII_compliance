# 条件终端估计器固定94–96统计准备

第94轮三路训练继续，仍未收敛。本轮没有训练派发、改训练参数或权重。实际主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。开工实际query/fetch/read main `03c71133282474ff3ca7a26cde44e1b109ccdea2`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，沿sii-research-sync保存；非RL工作保持。

## 固定窗口与口径

准备目录 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census94_96_reward_stability_20261031_v1`；PLAN精确引用原 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census94_online_20261031_v1/STABILITY_WINDOW_INTENT.json`。固定94、95、96三轮，5%相邻及首末相对均值变化，近零保护1，5000次按三类各10条件的配对分层bootstrap，seed2026102861；保留真实中止与实际回合长度。意向登记时点准确为94启动后、首完整回合返回前，本轮源码准备更晚，未冒充启动前登记。95/96仍需单独完整科学审查与有限登记。

原90–92 audit/review_saved程序在只改变窗口、输出键名、原抽样loss字段和新增严格绑定检查后复用。94 agent_train/q_loss是条件估计器，所以本统计的loss均值/最大/图与独立算术统一读取agent_train/original_sampled_q_loss；不以条件估计的平滑替代原loss健康。保留旧55科学参数anchor、历史23/47容量标记、history/rawbit/census版本一致性。

## 已实际完成的验证

统计kernel从sorted条件矩阵到相邻/首末变化、bootstrap、配对结果，除paired输出键名外与原90–92源码逐字一致。在实际旧90–92全部270回合数据上重算，原报告全部字段精确复现；另用math.fsum对每个bootstrap抽样独立计算均值及95%区间/斜率，全部通过。原I/A失败、V reward条件通过保持。**这是旧数据算术兼容性证据，不是94–96训练结果。**

三份真实94协议与原55科学配置/原census意向一致；33个错controller/cycle/parent/预算/自动派发/terminal权重/健康loss/物理步长/batch/actor LR的损坏协议均被拒绝。空九组完整输入拒绝，实际完整94 FINISHED缺失已核验。全部源码AST与SOURCE_LOCK检查通过，没有运行未来完整统计。

## 实际完整输入绑定尚待

未来全部94–96完成后，bind_inputs.py接受显式九组input map；每组必须绑定protocol、review、health、finished、episodes、optimizer、loss_plot、health_plot、loss_review、plot_inspection、checkpoint的真实路径和SHA256。保护覆盖三路×三轮全30条件、真实model/reward/Task/Strict/abort/长度/连续更新、原抽样与条件loss双列、真实两图查看收据、完整checkpoint边界及census/架构/52维回放/容量、正式父链与原有限科学决定。

任何一组缺失或版本变化即拒绝；仅完整且通过实际checkpoint检查才写REGISTRATION和BINDING_REVIEW，随后才能运行audit.py与review_saved.py，实际结果图仍须查看。**目前REGISTRATION.json、REVIEW.json均不存在，九组完整绑定未完成，无95/96训练登记或排队。**本轮仅准备并验证统计与绑定源码，不能称未来输入已核验。条件bootstrap反映条件组成敏感性，不是独立训练seed区间；5%与有限loss不能单独宣布联合健康收敛或解锁最终测试。

## 当前训练与下一步

原101身份连续600.436s/61样本保持，三路增长{'impedance': 5405, 'admittance': 5405, 'vmc': 5409}；保存steps{'impedance': 3878736, 'admittance': 3882242, 'vmc': 3883535}、完整条件{'impedance': 0, 'admittance': 0, 'vmc': 0}。原三训练/90sampler/archive和两个只读等待器1895688/2051280继续，完整94尚待。

完整94后仍需原全回放/action/reward审查、health与原抽样/条件/actor实际图、全8353旧93终端比较、全90训练条件比较，以及 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census94_comparison_20261031_v1/check_terminal_population.py --complete` 的真实新终端增长核验。首次5000无新terminal不替代此检查；health4096未投影固定min-pair仍是诊断。按完整结果独立决定下一有限95，无自动95/Direct34。

全部历史失败与90–92失败/92→93波动、Direct33原数值验收和冻结0/0/旧28证据限制、指定ESN缺失保持；Goal active。若中断，保存最新94 partial权重/Adam/RNG/replay/journal再登记census-aware恢复，不回退93或重跑整个94，MuJoCo物理state未保存。

## GPU和交接

独立guard `/tmp/sii_gpu_util_guard_20261031_recovery_v1` 保留，科学结束继续，不创建STOP，不是系统重启服务。窗口126样本/638.713s，最低[74, 70, 70, 68]%、低于50[0, 0, 0, 0]、末值[78, 70, 71, 95]%；含synthetic guard，不等于科学吞吐或每瞬时保证，旧主机切换0%记录保留。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS94_STABILITY_PREP_20261031/SMALL_EVIDENCE.tar.gz`，40成员/63585字节，SHA256 `7e2ae349f32956568b00d2af6c3dc9d44fb5ba63e41a032a536976df8dbedfb4`，逐成员/AST/JSON核验；原diff上下文空格保留。提交字节和远端收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS94_STABILITY_PREP_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，仅原LATEST254字节原地更新，大checkpoint/replay/raw仍共享SSD，不是HDD/arm1全备份。
