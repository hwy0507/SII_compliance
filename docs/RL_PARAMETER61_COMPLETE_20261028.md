# 参数61完整、原59–61窗口与准确续训62

2026-10-28，Goal active。主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`；共享SSD `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，仓库 `B/repository/SII_compliance`，Torch `B/env/bin/python`。前轮[交接](RL_PARAMETER61_EARLY_ANCHOR_20261028.md)保留。开工实际fetch/read mainee219171、baselinef6e8f8c；收尾main476a83fe新增另一主机非RL108第二条件九模型全失败和19→20/108等待，已读并fast-forward完整保留，无RL协议改变。

## 完整61

`B/runs/parameter_capacity_pool30_cycle61_20261026_v1` 三learner均自然结束，每路30×55秒、41250新增、无abort。完整60全2511648/2512250/2513250 replay行字段/history/optimizer保持，新reward由冻结实现重算误差0，网络及优化器有限。完整审查 `B/runs/parameter_capacity_pool30_cycle61_review_20261026_v1`。

|方法|steps / updates|mean reward|Task / Strict|critic首→末1000|critic mean / max|
|---|---|---:|---|---|---|
|I|2552898 / 2547899|−2.430040556|18 / 17|2.360355904 → 2.732908394|2.150163644 / 43.151416779|
|A|2553500 / 2548501|−7.003038018|15 / 15|1.845287362 → 1.347509073|1.478417554 / 27.032014847|
|V|2554500 / 2549501|−2.811681988|17 / 17|.811884367 → .738938107|.821545861 / 23.409801483|

完整61归档 `B/runs/parameter_capacity_pool30_cycle61_archive_20261026_v1/{method}/cycle_00061.pt`：

- I SHA256 `0775a2d988728b6a93de829d4613436e908b6146eadbdda8e0f350b7b30798bd`。
- A SHA256 `18b7f17c562599f8863d031323c4aa2d1b3524b0e32b94fd21e43fe594c50a20`。
- V SHA256 `7a155281f6a99818b3b900c9f03117a98b804b680019709319e200acdcefbc59`。

全loss `B/runs/parameter61_loss_20261028_v1`：41250更新长度/连续step/所有数值字段有限、完整49–61历史和全部原配对来源通过，独立保存算术及实际六面板图已审。I约35000后burst，actor28.900657→27.676971持续下移；A早期尖峰收缩、critic改善、actor−10.324838→−10.529782末段较平；V critic较低且有有限尖峰，actor先降后在约25000后回升至−14.509599。有限尖峰本身不新增失败阈值，不能仅凭有限值宣布整体收敛。

## 全条件标签与物理门

`B/runs/parameter_task_label_audit_20261028_v1/COMPLETE60_61.json` 全90条件对/180保存rollout检查完成，独立与完整loss全reward及原gate变化/计数交叉核验。此轮无Task-only变化；原59→60已发现的Task-only恢复记录保留。

- I short0600 Task保持true，外穿透.187539648→.233733862mm跨原.2mm门，Strict true→false，单条件reward19.386645→−34.881051，整体mean−.628091→−2.430041。任务成功计数仍18，不隐去物理退化。
- A short0600 Task保持true，外穿透.235473678→.199147150mm恢复Strict；long0200 Task/Strict true→false，long0500 false→true，净Task仍15、Strict14→15。mean−8.555518→−7.003038。新恢复与退化均报告。
- V全部Task/Strict标签保持17/17，mean−2.855623→−2.811682。

原MJB/evaluator和.2mm门保持，无重仿真；保存物理统计复核不是独立子步再积分。Task/Strict变化用于解释reward，不增加任务成功或零终端误差收敛门。

## 原59–61固定窗口完整

`B/runs/parameter_capacity59_61_reward_stability_20261028_v1`，原训练前登记/seed2026102855/5000bootstrap/5%/nearzero1/anchor55全部保持。REVIEW、独立SAVED_ARITHMETIC_REVIEW及实际图完成。该工具以REVIEW.json为结果，没有FINISHED.json；先读实际源码，勿据缺少不存在的完成文件重启。

|方法|59 / 60 / 61 mean reward|相邻相对变化|首尾相对变化|原5%描述检查|
|---|---|---|---|---|
|I|−.596952576 / −.628091136 / −2.430040556|近零保护，NA|NA|未通过|
|A|−13.606294811 / −8.555517730 / −7.003038018|37.1209% / 18.1459%|48.5309%|未通过|
|V|−4.517594098 / −2.855623283 / −2.811681988|36.7888% / 1.5388%|37.7615%|未通过|

I绝对范围1.833087980；近零保护不能换分母以制造相对通过。V最后两轮变化小这一正向事实保留，但不能删除59替代预登记窗口。原I56–58/V53–55通过及后续平台变化均保留。59→61条件组成敏感性95% bootstrap delta：I[−5.454855,−.001601]、A[1.483115,13.290659]、V[−.087674,5.242006]；不是独立训练seed或冻结策略泛化区间。独立保存审查复算均值/计数/loss/相对量，未独立重跑bootstrap区间，报告范围如实限定。

## 健康诊断与全部1824固定终端

health实际JSON和training_diagnostics.png已审，右上长标题边缘裁切、精确定义以JSON为准；回报图是在线回合完成顺序。A/V训练targetmean与固定min-pair诊断TD不同，不能混称训练loss。

|方法|终端数|全终端MAE|in-bag MAE|固定pair未投影TD MAE|sample Q mean|
|---|---:|---:|---:|---:|---:|
|I|1855|.966630326|.385051215|.234870152|−27.103574530|
|A|1854|.664197567|.233807327|.214283532|10.588262778|
|V|1854|.485427229|.174608035|.130874867|14.399804805|

诊断网络状态不变，非零误差不是停止门。`B/runs/vmc61_terminal_anchor_followup_20261028_v1` 全部旧1824固定60终端输入/动作/reward/mask精确、权重及前向RNG不变、health61复现；0优化/物理/replay写入，独立保存值算术和实际follow61.png通过。

旧masked SSE4384.706013435→1068.426726214，下降75.63287657%；旧贡献.255591424572→.061219096679，按旧分母末值.062217695578；新30贡献.002295104659，全部.063514201338。原五focus全保留：2050526和2299142改善，2046571 1.043687→1.191591轻微退化；58失败2423133 181.353174→357.964253退化；58成功2423122 1497.642821→47.331503明显改善。不能称五focus均改善或推断在线梯度因果。散点近原点标签重叠，实际已看。

values SHA `7d57fb64ac41d2e347b9ba7b4c2cf9fb3bb978521c69edb853d6b3c34b94f4a0`；plot SHA `7b27f227a6c8be24d8a5ab697f276d8b218878f0cfa04af5dabe953f9d5b903d`。

## 一个有限62已启动

`B/runtime/prepare_parameter62_20261028_v1/DECISION62.json`绑定完整61/health/loss/全标签/终端/原59–61及原56–58、实际图与准确恢复。三路61完整state/replay/下一65536恢复均exit0；batch65536/UTD1/终端128/I targetmin、A/V targetmean/actor min/LR/reward/gates/物理/masks/4m append和历史23/47 marker全保持，无辅助权重或重置。

12:44:29 UTC，`B/runs/parameter_capacity_pool30_cycle62_20261026_v1` 启动：I1721611/A1721613/V1721615均start38718598；archive1721620/start38718599，startup1721623/start38718599。GPU1/2/3、CPU13–25/26–38/39–51，每路30sampler。不自动63。

62完整loss1758710/start38725354已绑定真实jobs，CPU54/7200秒，PLAN SHA `5135fa5294f98b4562100bf1354d9afac1aac2b48593fca7b272c9983b32ae57`，保留全49–61再追加62；源静态逆变换/AST通过。`B/runs/parameter62_loss_20261028_v1`。完成后独立review_saved和实际图必须执行，标签补充仍检查全Task变化。

未来62–64窗口1758711/start38725355已按原启动策略于62真实启动后运行，CPU54/14400秒。原PLAN SHA `44e0b484fb61c8c640e2e56bfe1ca36b08d96c2098c2c393104ebf9c3713dfc5`保持不变；其中waiter_launched=false是登记时状态，实际启动写独立LAUNCH.json，绑定原59–61结果与DECISION62。不得用未来窗口覆盖59–61失败，不自动训练/停止。

## 观察与GPU保活

12:21:11–12:35:46连续30观测中原learner身份保持直到A/V自然退出，实际FINISHED证明正常完成；只读观察器exit0，未重启训练。随后只读后处理观察器误等待reward窗口不存在的FINISHED文件，读源码确认真实REVIEW出口后，仅向已核验1605329/start38686357观察器发SIGTERM（exit143），科学进程未停止。记录 `B/runtime/parameter61_verified_wait_1221_20261028_v1/POSTPROCESS_OBSERVER_CORRECTION.json`。另一次临时只读poll替换误改日期导致FileNotFound，准确路径重查原62live，无科学操作。

GPUv5实际 `/tmp/sii_gpu_util_guard_20261028_v5`：supervisor3256866/start37410686，workers3256867/68 start37410690、3256869/start37410691、3256870/start37410693持续运行。61训练结束到62启动间实测79/71/71/71%，12:46原62推进时79/92/96/95%。含合成负载、非纯训练吞吐或每瞬时保证；历史0%异常保留。用户要求科学完成后也继续guard，旧v4 STOP保持；不是跨系统重启服务。

Direct33原经验数值收敛、Task/Strict0/0保持，不启动34；冻结55原90回合及41→55比较已完成，不重跑。整体goal尚未达到reward稳定与loss健康的完整证据要求，继续原62，随后审完整结果再决定63。

实际62 startup已通过：I/A新增1000、V新增2000；旧2552898/2553500/2554500全replay字段/history/optimizer、30sampler/30MJB/原marker保持，新reward重算0误差，见startup/REVIEW.json。启动前check-only与真实启动检查分别完成。当前VMC62终端对照、63仅恢复准备尚未创建，后续按需要登记；不能将poll中缺失目录解释成已有等待进程。

## 保存与后续接手

[完整本轮小证据收据](RL_PARAMETER61_COMPLETE_SAVE_20261028.json)、[清单](evidence/RL_PARAMETER61_COMPLETE_20261028/MANIFEST.json)：166成员/1749050字节，`B/repository/RL_PARAMETER61_COMPLETE_20261028_125200/SMALL_EVIDENCE.tar.gz`，SHA256 `7c06d043b133ecb7e7bcb5a354c9b455f94726ff85c2f809d14aa1d82bb99f24`，逐成员字节和全部Python AST通过。大checkpoint/replay/raw仍原共享SSD；HDD配额满只重写既有LATEST入口，不声称HDD或arm1全备份。

12:50实际62steps2557150/2557801/2558879，原learner/archive/全loss/62–64等待及五guard身份通过，GPU78/93/92/90%。接手先核验PID+start ticks和真实完成文件。下一步继续原62，准备其终端对照和63仅恢复检查（尚未创建），审完整62后再决定后续。不要重复派发62、不要因观察器截止重启，不以保活负载当科学吞吐。
