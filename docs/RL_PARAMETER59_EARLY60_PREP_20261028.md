# 参数59早期诊断、全1764终端跟踪与60仅恢复准备

2026-10-28 09:49 UTC。Goal active，上一轮完成58审查并准确启动59，本轮原59经实际PID/start核验继续推进；没有重启科学任务。[完整58与原56–58结论](RL_PARAMETER58_COMPLETE_20261028.md)保持：I reward原5%通过，A/V未过，整体loss健康收敛尚未证明。Direct不启动34，Task/Strict0单列。用户要求科学完成也保活，GPUv5继续。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本轮实际查询/fetch/read main `5714588b9b0014698cc1a7af3665e143b7d4f648`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志，工作区起始干净，无新增科学协议变化；沿用sii-research-sync，无子agent。

## 第59轮固定前5000更新

`B/runs/parameter59_first5000_20261028_v1`保存原optimizer前5000完整字节。登记时训练及前缀已存在，是描述性检查，不冒称训练前预登记。audit适配前轮固定长度，review_saved独立逐标量复算、原source前缀逐字节/hash、连续steps及所有数值字段有限通过；loss.png已实际查看并记录PLOT_INSPECTION。原53–55、56–58和未来59–61窗口均不替换。

|方法|critic首1000→末1000|critic平均 / 最大|actor首1000→末1000|
|---|---|---|---|
|I|2.567929→2.436369|2.392588 / 17.075603|30.929136→30.873515|
|A|1.429878→1.347822|1.409231 / 8.830840|−10.292897→−10.318440|
|V|1.167645→1.198585|1.164147 / 15.572744|−13.830922→−13.857948|

I/A基线小幅下降且尖峰仍在；V仍高于58抬升前约.7的水平，不能称已恢复或收敛。全部正式训练/回放/优化器/奖励/门槛/物理配置不变。

## 全1764固定终端锚点与59等待

`B/runs/vmc59_terminal_anchor_followup_20261028_v1`。实际capture_anchor读取完整58归档VMC checkpoint SHA`0c3eb091982e7d72a40a8db94020a05ec620e53ca061a0b8648e5f0b53119670`，沿用已独立审查58 CPU前向的Q，0新网络前向/优化/物理。完整1764×57特征、indices/reward/mask/q/分母精确；独立review_anchor逐数组和标量通过。固定全1764 masked SSE为8649.38257363018，包含58新增30，不能与此前旧1734的2441.892212混称。

`anchor58.npz` SHA`55d2476e60f106cf1c08701140c8dc03e88047a2043cb40fbbc0ea81b42be383`。登记在59运行期间、完整结束前；新waiter387806/start37657716，CPU53/7200秒，绑定原59三learner和archive。计划SHA`0aa22f3140f93183bc4e87e609f2c5a96b06b35db63bec30efd92d811eed1646`。原wait.py字节完全相同，track/review适配完整58→59、旧1764/预期1794，critic特征维57保持；语法/源hash/实际身份通过。

保留历史focus2050526、2299142、2046571，新增58 short0600失败2423133和short0200成功2423122，全部1764行仍纳入。将比较旧/新全部masked SSE及旧/当前分母，并复现59 health，独立保存算术后实际检查follow59.png。仅展示改为两行标题与tight裁边，避免旧图标题裁切，训练及计算公式不变。

**实际59终端对照尚未执行**，不能将锚点捕获/静态检查当作结果通过。无新零误差停止门、不作minibatch梯度因果或状态完全混叠声明。

## 第60轮仅恢复准备

`B/runtime/prepare_parameter60_20261028_v1`，waiter294526/start37642076，CPU53/固定14400秒。绑定原59 LAUNCH hash、learner与monitor身份，等完整59 archive/review/health通过且原learner退出后，只运行check-only恢复检查。**没有自动60训练，实际60恢复尚未发生**。

prepare/launch/startup从59适配，父58→59、新59→60及补零checkpoint路径逆变换和AST/hash核验，wait_prepare字节不变。launch保留原历史`reward_window56_58`证据要求（不是误改为56–59），要求DECISION60绑定完整59审查/图和实际恢复检查。实际无DECISION60调用退出非0、明确FileNotFoundError，未创建60 run，拒绝收据保留。完整59后再评估是否续训，不因观察等待超时重启原任务。

## 原训练、冻结评测与GPU

09:49实测59 I/A/V为2440136/2440779/2441875steps，各30sampler；三learner4084699/4084701/4084703 start37574080，archive4084708/start37574081，完整loss4089956/start37575729，原59–61窗口4067967/start37570184均原身份live。59真实startup已在前轮通过，完整59尚待。

冻结55原三evaluator1869175/76/77与root1869178，start均36428775，完整25/25/24条件继续，完整结果尚待。保持原90回合/seed/4m全state恢复计划，禁止重复启动；41的2m与55的4m区别继续单列。

GPU实际v5运行`/tmp/sii_gpu_util_guard_20261028_v5`；supervisor3256866/start37410686，workers3256867/68 start37410690、3256869/start37410691、3256870/start37410693均核验live，STOP不存在。GPU80/71/95/93%包含合成保活，不是纯训练吞吐；科学结束后继续。旧v4已退出，旧STOP有意保留。v5不是跨重启服务；先前实际停顿/恢复及60采样证据见[GPU交接](RL_GPU_GUARD_V5_20261028.md)，不保证未来所有瞬时均≥50%。

## 保存与后续

小证据`docs/evidence/RL_PARAMETER59_EARLY60_PREP_20261028`，共享SSD包`B/repository/RL_PARAMETER59_EARLY60_PREP_20261028_094937/SMALL_EVIDENCE.tar.gz`，43成员/1291465字节，SHA`a8f3aca9c15cedf8e35a4bd6f74c3fcc2e1566f6aedf398fdd287029226f6848`，全部成员逐字节和Python AST核验，含三个完整5000原前缀、锚点、源/计划/启动/拒绝及live身份。收据[保存记录](RL_PARAMETER59_EARLY60_PREP_SAVE_20261028.json)。大科学产物仍原共享SSD，非HDD/arm1全备份；现有HDD LATEST入口指本文。

继续原59与冻结55。完整59结束后读完整loss/health/全1764终端对照与60check-only；手动运行完整loss59的review_saved.py并查看实际图，再决定有限60。原59–61窗口不可提前宣称通过；整体goal仍active。

收尾再次fetch/read main `490785f3858a444031c6379b0384fdad539a2603`，新增非RL绘图兼容和拟合进度。AGENTS顶部并行新增冲突按双方原字节前缀加共同历史解决，其他文件自动合并；未改冻结训练源码。
