# Direct20–22固定稳定性窗口登记

2026-10-27 UTC，服务器rltest-1025--a6ed2ff39b3c-2d5lfqki2m。上一轮完成参数33/Direct21接续、冻结32启动、健康审查和归档，属实际进展。本轮重新核对原PIDs均live、步数推进，未重复运行已完成实验；Goal active，无子agent。

## 新审计等待

服务器根B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。
新目录`B/runs/serl_cycles20_22_reward_stability_20261027_v1`，原waiter **3124904**。源自已执行的Direct稳定性审计器，改为19作配对baseline、20/21/22作末三轮固定窗口。保持原5%描述建议、近零保护1、分类配对bootstrap5000、原30条件/原全部41250条每轮optimizer日志。报告回报均值变化/斜率/组成敏感性区间、loss首末/均值/最大值、temperature、终端与32步TD误差，核对协议/source/checkpoint与完整review/hash；不以Task成功增加门槛，不自动判收敛或停训。

登记时19和20完整结果已知，21仍0个完成条件，22尚未启动。因此仅部分前瞻，不称20也是未知结果；PLAN封存已知19/20全部输入hash和当时21实际进度。bootstrap seed2026102740，等待10800秒（覆盖剩余21与未来完整22），不自动延长，不自动训练22。所有周期完整FINISHED/REVIEW后才生成REGISTRATION并分析。AST、准确cycle/window/30条件保留和--help通过；实际统计尚待，不能把登记当完成结果。原Direct17–19完成审计未重跑。

## 首个冻结条件已复核

仅读取原三路`parameter32_frozen_full30_20261026_v1/{method}/passive_corner_train_0000_REVIEW.json`，未重跑推理或仿真。每路1375动作/55秒，Task/Strict均false、全horizon、无人接触；comfort分母不存在，保持NA。原物理、filter、torque审查通过，filter/projection重放误差0、原生连续随机动作重放误差0、完整learner state不变。首条件失败保留，不提前终止/扩展90回合预算，不当冻结完整矩阵结果。

## 继续沿用的作业与后续

四正式：Direct21 **2826774**；参数33 I **2463296** / A **2463297** / V **2463300**。各startup已在上一轮通过，原归档和完整review继续。Direct22准备 **2851849** / CPU调度 **2851880**；参数34准备 **2501606** / 调度 **2501611**，均只完整父审查后check-only，不自动训练。参数33–35稳定性等待 **2585589** 保持。

冻结32原I **2466385** / A **2466386** / V **2466387**，根review **2466388** 继续。具体最新进度/PID start identity见`docs/evidence/RL_SERL20_22_STABILITY_REGISTRATION_20261027/LIVE_STATUS.json`，不是持续实时状态。原完整科学交接仍见[参数33/冻结32/Direct21](RL_PARAMETER33_FROZEN32_20261027.md)。不存在新的整体收敛或最终ESN/SPT比较结论。

GPU最近即时值57/84/82/83%，后三卡含冻结推理，不当连续窗口证明。上一轮固定65.572秒窗口均值55.60/74.8667/72.4333/68.2833%仍只属于原20/33/冻结32窗口；本轮未重采挑结果。继续优先及时接续真实训练，不制造空负载。

开工重新查询/fetch/read远端main **dbb1d76ed79177067c48ed49ff9f67f023c704aa**、baseline **f6e8f8c2711a93f0b5dfc88c608bd82647084d5d**，均未变。仓库sii-research-sync按已读流程执行。GitHub认证与指定ESN已向用户问过，不重复索取。新小证据/源码和补充归档收据随本次提交；完整此前归档仍为B/repository/RL_PARAMETER33_FROZEN32_20261027_005821/FULL_SMALL_EVIDENCE.tar.gz，SHA beb754dc3a246f03c409524367c23c9f5e1fcdeb428295eec803caa677d3b2b1。大checkpoint/replay/raw仍SSD，不称HDD/arm1全备份。
