# 参数39完整审查、固定VMC跟踪与正式40续接

2026-10-27 UTC；Goal active，无子agent。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。正式参数40从准确完整39全状态接续一个有限原设置周期，Direct24原进程3403962继续。未改变物理/MJB/gates/filter、canonical48、原30条件、dt5e-5、reward或learner设置，没有辅助权重推广。

## 完整39结果

原39三learner3314522/3314523/3314524、archive3314528、review3314529均已完成。完整REVIEW/FINISHED、health/图和独立保存算术通过。旧replay全字段/history/2m marker精确保留，新reward逐条重算误差0，网络/优化器finite，诊断前后state不变。保留全部30分母和真实早停。

|方法|完整steps / updates|新增transition|Task / Strict（30）|reward|末1000 q_loss|terminal MAE / in-bag|
|---|---:|---:|---:|---:|---:|---:|
|阻抗|1646180 / 1641181|40430|17 / 17|−2.501147897|2.611422197|.791698 / .234733|
|导纳|1646000 / 1641001|41250|15 / 14|−8.694325077|2.036092655|.858953 / .396187|
|VMC|1647000 / 1642001|41250|17 / 16|−4.599549845|.921421590|.619772 / .288947|

阻抗29全55秒+1原早停；A/V各30全程无abort。阻抗末段loss与温度升高；导纳loss先降后升；VMC末1000从38的1.613083降到.921422，但整轮均值从.759219升到1.219339。三路原生正温度和有限loss，不宣称整体健康收敛。完整39SHA：I `60d9b0dfc4140f4057c75dbed07789edb3c2515942d8c751b7682af8d4aadcaa`，A `2784acd5d2f72bbebb9a0d87e69dbc3e94322753cf14b8addc3bb81a61e2f106`，V `66be5ac5d61a6435c2a72fb1318d81445fe233643d9fac975d3bf6c693e41f1e`。

38→39保存配对：I均值−.163290，long0000成功→早停贡献−1.958393、short0600 Strict恢复贡献+1.805769，不能用近似抵消掩盖失败；A均值+5.029007，由4条件恢复、1条件失败等共同构成；V均值−.023292，Task/Strict无切换。是保存算术，不是在线loss或探索/学习的因果分解。此前36–38原5%检查I通过、A/V不通过的结果不改写；39–41固定窗口仍等待完整40/41。

## 阻抗long0000早停保存审查

原条件 `active_long_train_0000` 在555动作、22.200000秒、444000物理子步触发 `global_penetration_exceeded_2mm`，处于retreat，Task/Strict失败。rollout与TERMINAL、episodes、MJB/登记hash和实际executed_evaluator原2mm门一致。保存全局穿透峰值99.575073mm，最差pair `office_v5_corner_top` / `target_object_geom`；外部机器人穿透峰值仅.075943897mm，最差pair人体thumb / hand_collision。

全局项含payload接触，不可误报成机器人外部穿透99.6mm；原gate失败保留，不调整阈值、不删样本、不重跑。这里只核保存聚合、实际源码与model绑定，没有重算原始子步或证明巨大payload穿透的物理原因。具体证据 `parameter_capacity_pool30_cycle39_review_20261026_v1/SAVED_ABORT_REVIEW.json`。

## 原固定1164 VMC跟踪39完成

原waiter4150741及一次CPU52前向640707均完成；不重复。完整39全部1194终端，原38固定1164 inputs/actions/rewards/masks全部精确；agent和forward RNG不变、0优化/物理/replay写入。原保存值独立复核和图通过。

- 同1164 masked SSE：7978.075799→2066.335246，下降74.099829%。
- focus index1603101（38 short0600）SSE：7060.132246→939.189601；并非仅挑该点，总体旧样本改善亦报告。
- 39全终端population项.242246276，其中旧1164项.183803620、新30项.058442655。
- 旧行按38旧分母项.188546213，低于38的.727682355，改善不只是回放分母增加。

这是冻结critic对固定终端输入的变化，不包含非终端TD或历史minibatch，不证明全部loss因果份额、任务泛化或最终收敛。run：B/runs/vmc39_terminal_anchor_followup_20261027_v1；原REVIEW/SAVED_VALUE_REVIEW/values/plot齐全。

## 正式40、下一阶段准备与算力

原40准备3416298在完整39后执行，三check-only全learner/replay/next65536/RNG和准确父SHA通过。结合完整loss图、保存早停、固定VMC跟踪作PRELAUNCH审查后，04:55:45 UTC正式40 I691539/A691540/V691541启动；startup691543、archive691544、review691545。run：B/runs/parameter_capacity_pool30_cycle40_20261026_v1。2m append回放与pair learner、历史capacity入口23保持，一个原设置有限周期；预期最大I1687430/A1687250/V1688250，实际以原安全早停后的完整结果为准。

新41仅恢复准备715346、原40 review释放CPU调度715347：7200秒等待，完整40退出且FINISHED/REVIEW后check-only，无自动训练。五脚本同时上下文替换、AST/准确父40→41、CPU39和历史entry23守卫通过，登记目录B/runs/parameter41_preparation_registration_20261027_v1；实际41恢复尚待。

原换轮观测549332已完成：每2秒记录旧进程退出区间与新launch时间，I约245–247秒、A243–245秒、V251–253秒。包含完整审查/诊断/恢复，不称为全卡空闲总时间。40启动后另见共享存储等待：原三参数进程Dsl/cxiWaitEventWait，随后Direct亦同wait，SSD目录查询短暂阻塞；原进程保持并恢复真实更新。确切起止未连续采样，不能虚构时长或根因。记录B/runs/parameter39_to40_transition_20261027_v1。

新固定纯24/40 GPU observer724787已完成：原40实际startup通过后60样本/69.303144秒，四卡平均53.5%/60.3%/58.0333%/63.6167%，逐样本GPU恰四正式PID且身份不变，原PROFILE和保存算术/source核验通过。无额外GPU工作、不重采择优，不保证每瞬时或窗口外达标。原纯24/39窗口已完成且不重跑。Direct24首次1,001,000边界原3403965继续，25恢复3448092/调度3448355、Direct24–26原1470790、参数39–41原3482651均沿用原登记。

## 同步与归档

已读远端main e305c70640e30bee5ea2ec76299a5c2c64e73be6及baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。新增远端非RL92–94/108日志已逐字节并入，非本机RL或指定ESN最终完成。前轮VMC38/冻结32科学提交74e035c、合并95f0777、归档收据0c81030；HTTPS push因缺username失败，不索要凭据或虚构远端发布。

新大型产物保留SSD；HDD配额满，仅已有LATEST指针更新为核验过的SSD交接。非HDD/arm1全checkpoint备份。实际40 startup已通过：I/A新增1000至1647180/1647000，V新增2000至1649000；全旧1646180/1646000/1647000 replay字段/history/optimizer设置/2m marker、30模型和30sampler集合、动作/clock/新reward0误差通过。原startup691543结束，不重跑。Direct24 validated driver/helper SHA仍与已验证版本完全一致。GPU结果见上文；当前存活见小证据FINAL_LIVE_STATUS，归档收据另记。

收尾再次真实ls-remote/fetch/read：main推进至 `7d69ac57974888d32f98d208f0097e7ec8f64426`，baseline保持 `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；仅非RL95–97/108日志新增，保留全部原记录，不冒充本机训练或最终评估完成。

## Direct24首次跨原百万容量边界已通过

原3403965边界监控已结束，不重跑。指定阈值1,001,000，实际保存1,001,040 steps / 7,968,328 critic更新；完整父977,040旧raw/derived行、history/optimizer设置/clock保持，新增24,000中23,070成熟+930 pending，所有新32步目标和reward重算精确。2m marker/cursor=size=1,001,040，无原1m环绕覆盖；30模型/30sampler、canonical48/动作映射通过。保存RNG克隆的下一65,536抽样中64,017来自父旧行、13来自超过1m的成熟行，pending未参与抽样；它是只读抽样域验证，不是实际新learner更新日志。

边界检查点SHA `d643a76d3f4c198f7200b4ef31a2ff08d458ca2b34a1b17ac13d755e1b025baf`，本轮另核原结果算术和不可变检查点hash。原REVIEW.time为监控启动时刻，并非跨界完成时刻；不据此虚构发生时间。路径B/runs/serl_capacity_batch65536_cycle24_20261027_v1/capacity_boundary；完整24仍在运行，不能把跨界审查当整轮完成。
