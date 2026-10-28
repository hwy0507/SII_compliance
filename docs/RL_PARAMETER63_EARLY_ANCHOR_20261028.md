# 原63前5000、全1884终端锚点与64仅恢复准备

2026-10-28 14:09 UTC，Goal active。主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，仓库 `B/repository/SII_compliance`，Torch `B/env/bin/python`。完整62及准确63启动见[上一交接](RL_PARAMETER62_COMPLETE_20261028.md)。本轮开工main80553b71、收尾mainc9245390和baselinef6e8f8c实际fetch/read。

## 原63继续

`B/runs/parameter_capacity_pool30_cycle63_20261026_v1` 原三learner I3732463/A3732464/V3732465 start39114601持续live；14:09:22实际steps2608076/2608722/2609739，每路30sampler，尚0完整条件，未重启。原reward/物理/gate/LR/mask/终端128/batch65536/UTD1/I targetmin、A/V targetmean/actor min/4m append及全部历史状态保持。

archive3732466/start39114602、全63 loss3741519/start39117327和原62–64窗口1758711/start38725355均核验live。原62–64仅完整62，仍待63/64；原59–61失败、I近零保护及I56–58/V53–55历史通过保留，不换端点、不新增零终端误差门。Direct33原经验数值收敛、Task/Strict0/0，不启动34。

## 固定前5000已独立复核

`B/runs/parameter63_first5000_20261028_v1`：只适配周期路径/描述，逆变换和AST通过。登记在63训练和前缀已存在后，非事前。三个前5000逐字节/hash、所有数值有限/连续步数、独立标量算术以及实际loss.png均通过。

|方法|critic首→末1000|critic mean / max|actor首→末1000|
|---|---|---|---|
|I|2.602483042 → 2.513032758|2.457861737 / 21.359306335|26.712457047 → 26.741734392|
|A|1.289616407 → 1.263167381|1.276842228 / 3.097397089|−10.384853719 → −10.392982023|
|V|.957334392 → .915894084|.966679875 / 15.718063354|−14.229403233 → −14.310152966|

实际六图可读：I critic局部起伏/有限尖峰，actor较平略升；A critic小幅下降/波动、actor较平小下凹；V早期较大尖峰后逐渐稀疏、critic中后段略降，actor持续下降。只是固定前缀，不称完整63、reward稳定或整体收敛。

## 全1884固定终端与待完成63对照

`B/runs/vmc63_terminal_anchor_followup_20261028_v1` 已从完整62精确checkpoint提取全部1884×57终端输入。复用已验证完整62 CPU Q、0新网络前向/优化/物理；全部保存数组及独立标量SSE **6702.4155846360445**复核通过。`anchor62.npz` SHA256 `b2a17d447083b6681cb9814fdb34c939ded497403fdf0e0765b5f010cfbb4b92`。

实际对照waiter **17088/start39201010**，CPU53/7200秒，CUDA禁用，PLAN SHA `2647a98414164c3a7a1a1b5985957842d1bda138632869f9697eb7942fd08811`；绑定真实63 learners/archive/registration/source和锚点。完整63审查/原learner自然退出后才CPU前向，对照1884旧+30新=1914，五focus2050526/2299142/2046571/2423133/2423122保持。结果/独立保存复算/实际follow63.png审查尚待。

准备过程保留两次失败：初始周期文本替换误改日期，被日期断言拦下；随后误改ky26288目录，capture_anchor在读取checkpoint前FileNotFoundError退出，依赖review_anchor也拒绝缺失输入。源已分别保存在rejected_date_mapping/rejected_owner_mapping。修正为数字边界匹配并保护日期/不透明hash，逆变换/AST/日期/owner检查、真实锚点提取及独立复算通过；wait.py字节保持。另一次PLAN绑定过早、ANCHOR_SAVED_REVIEW尚未写出，真实调用拒绝且未建PLAN/进程；确认原review进程exit0后才实际启动上述唯一waiter。没有修改训练。OWNER_MAPPING_FAILURE是已解决的历史准备失败，不是WAIT_FAILURE；最终状态看PREPARATION_FINAL_REVIEW与真实PID。

## 全标签63及64仅恢复

`B/runtime/parameter_task_label_audit63_20261028_v1` audit_labels.py与原已验证工具字节一致，wait63.py仅周期/路径适配、逆变换/AST及实际diff审查通过。输出 `B/runs/parameter_task_label_audit63_20261028_v1`；waiter **53660/start39207399**，CPU53/7200秒、CUDA禁用，PLAN63 SHA `237f58fc5187e021b2c7ba0992bb174ffdcba76f7b38142a73486c4116afd5cb`。完成后读COMPLETE62_63.json/FINISHED63.json，独立核对90reward对/180rollout及Task-only变化，不修改原loss工具。

`B/runtime/prepare_parameter64_20261028_v1` 原63→64源适配含补零周期，逆变换/AST/实际diff通过，wait_prepare.py字节不变。缺DECISION64的真实启动调用已拒绝，未创建64训练。仅恢复waiter **53659/start39207398**，CPU53/14400秒，REGISTRATION SHA `46cfc6aa7d52734243d7f7059ca84742a28040c8602dc2b1bdb7ab589030d297`，绑定原63身份。只有完整63归档/审查/自然退出后才执行全state/replay/下一65536 check-only，不自动训练64。

后续DECISION64须保留launcher原reward_window56_58字段，同时绑定原59–61失败、完整63 loss/health/标签/终端及原62–64当时状态；全部具体结果需实际审查。当前不存在64科学决定。等待超时不能当作训练终止，不据此重启。

## GPU、同步与接续

v5实际 `/tmp/sii_gpu_util_guard_20261028_v5` 五进程3256866–3256870，start ticks37410686/37410690/37410690/37410691/37410693均核验live。14:09:22 GPU75/90/92/71%，含合成保活，不是纯科学吞吐/每瞬时保证。用户要求科学完成也继续guard；旧v4 STOP保持，当前guard不是跨重启服务。

远端c9245390非RL更新及报告已实际读取：另一主机原108在35条后按STOP边界结束、全失败保留；修复独立新三场景的动作尺度并运行教师/学生对照。已fast-forward完整保留，其冻结runtime与本机RL不同，不改本机RL配置或科学进程，不重复派发其任务。

[保存收据](RL_PARAMETER63_EARLY_ANCHOR_SAVE_20261028.json)、[清单](evidence/RL_PARAMETER63_EARLY_ANCHOR_20261028/MANIFEST.json)：82成员/1323410字节小包 `B/repository/RL_PARAMETER63_EARLY_ANCHOR_20261028_140922/SMALL_EVIDENCE.tar.gz`，SHA256 `261457f1696b3cc9dc117f07b2dee373a587a05eb82fd001a98e26f941ec955a`，逐成员字节及全部Python AST通过，包含已拒绝源与失败收据。大checkpoint/replay/raw留共享SSD；HDD配额满只更新已有LATEST，不是HDD/arm1完整备份。Goal active，无子agent。

接手继续原63，完成全loss/health/全标签/固定终端审查，再决定64；原62–64待完整报告。各等待器只观察/审计或恢复检查，不代替科学决定。
