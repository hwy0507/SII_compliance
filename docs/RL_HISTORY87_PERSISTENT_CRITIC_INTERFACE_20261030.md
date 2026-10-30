# 完整87历史critic持久化与原生接口验证

2026-10-30，Goal active。本轮实现并验证51维critic/replay持久化接口、严格父状态迁移和只读消费入口。正式训练父仍完整87；没有第88轮注册或训练，没有Direct34，没有把离线拟合权重用于正式训练。reward稳定和loss健康尚未达成，不能把软件验证写成收敛。

实际主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。实际开工与收尾query/fetch/read main `89b3025e1b4660e40ac3a7b42fa3fabd27489638` 和 baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新增远端改动。遵守仓库sii-research-sync，无子agent。

## 实现与约束

源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history87_critic_interface_20261030_v1/persisted_history_critic.py`；只读入口 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history87_critic_interface_20261030_v1/history_consumers.py`。绑定准确完整87的checkpoint、全learner/replay digest、sidecar SHA、方法/维度/行数。原clock replay50扩为51，索引50只加当前动作前已经完成区间的累计外穿透特征 `p/(p+0.0002)`；terminal next使用终端区间，未广播未来最终峰值。每个stream独立计数，缺区间、重复区间、穿透递减被拒绝，环境恢复时全部stream清零，旧replay历史保持。

在线及target全10个critic首层插入零列；Q Adam对应moment插入零列，旧权重/moment/counter/LR和actor/alpha/RNG原样保留。actor的51维入口只取原49维，物理canonical48不变；原clock索引49、CHEQ采样/mixing、两目标reducer、terminal128、有限上界公式保持。专门适配原本写死50维的投影输入，重新绑定foreach target参数引用。学习历史列之后critic不确定性和CHEQ mixing可能变化，这是有意的模型修订，不能称为始终相同策略。

replay保持4m append-only及23/47容量标记，全部旧字段和bootstrap masks逐字节保持；两个新增列来自前轮审完的87因果sidecar。旧checkpoint不能直接当51维load，必须走明确迁移入口；持久化marker不匹配拒绝。

## 完成验证

|方法|旧replay行数|在线/target初始Q最大误差|负例拒绝数|终端health行数|记录观测/terminal事件|
|---|---:|---|---:|---:|---|
|impedance|3606448|0.0/0.0|15|2605|1375+1|
|admittance|3608750|0.0/0.0|15|2604|1375+1|
|vmc|3609750|0.0/0.0|15|2604|1375+1|

主检查实际149.192秒：三方法所有旧learner状态逆迁移后精确同父；全部10,824,948旧行及新增特征正确，下一批65536旧字段/新增列和RNG精确；两stream原生动作/混合上下文/clock/RNG相同。所有原87checkpoint SHA保持。随机5/7维fixture共12次原生update（非正式checkpoint update），恢复后重复两次update全state精确，历史梯度非零、target引用和actor隔离通过。

独立保存/cache核验实际242.665秒：用不同实现逐字段去除新增零列，原agent/Adam/其他state全digest相同；完整learner+replay快照写盘回读、51列实际GPU cache、65536抽样及RNG、mask前缀不确定后的完整检查和重抽通过。仅在可丢弃内存replay各加1条合成行，验证旧前缀、Bernoulli RNG和GPU行同步，再恢复；保存快照没有这些合成行。

只读consumer验证实际178.432秒：固定I short0600、A short0900、V short0000的原87记录各1375观测+terminal，外部seed2026102633；逐步输入历史/clock，原生raw/mixed动作和上下文与零列前精确同值，完整learner/RNG/replay不变。全终端all5在线/target health预测精确同父，原投影公式逐位相同。这里重放的是既有观测，不是新物理轨迹、冻结评测成绩或held-out性能。

全部核验0新物理，0实际父checkpoint optimizer update。所有结果和源码均保存，没有测试失败记录。

## 下一步

继续准备独立、有限的history在线修订登记。仍需把新接口接入完整trainer恢复/registration/启动检查、周期归档及health/frozen evaluator的调用链，验证实际起步后才能启动正式88。当前trainer候选只在已确认事件位置增加一次consume_interval，去掉这一行后与原87trainer逐字相同；它不是可直接运行的正式88 driver。只读consumer模块通过记录重放，但旧冻结脚本的完整gate/review/dispatch尚未接入，不能直接改cycle数字启动。

正式父必须完整87；不回退诊断86，不晋升前轮离线clone。有限stage保持30×55s/每方法最多41250新transition、batch65536/UTD1/原LR/reward/masks/物理/gate/filter/dt，除单独登记的history模型信息外不改。完整87原85—87稳定性全失败、I/V末loss回升继续保留。Direct33数值接受但冻结30 Task/Strict0/0，中断28缺最终内存证明；指定ESN仍不可用，不用他主机替代、不重复追问。partial75、74—76不可判和79安全中止及所有历史失败窗口保持。

## 保存与GPU

全迁移快照目录 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/history87_interface_snapshots_20261030_v1`，每个文件明确标记 `interface_only_no_online_approval`，各SHA/字节在MANIFEST和保存收据。它们是未更新的迁移状态，原完整87仍正式训练父，不把它们列为训练88结果。大型产物仅共享SSD，非HDD/arm1全备份；HDD已有LATEST指针原位254字节更新。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_HISTORY87_PERSISTENT_CRITIC_INTERFACE_20261030/SMALL_EVIDENCE.tar.gz`，71成员/80387字节，SHA `b0be207810835ea94640423734a3dcf89984717b434cd8f3007087da93a1c4db`，逐tar成员/AST核验，另验Git index/commit；仅成功push后观测远端才在包外写PUBLICATION。

GPU本轮141样本最低 `[76, 76, 77, 76]`%、低于50次数 `[0, 0, 0, 0]`、末值 `[81, 79, 80, 79]`%。v7 supervisor97370和四worker原身份保持，用户要求科研结束后也保载；有合成负载，不冒充训练吞吐。历史v7预热0和v6 31/33/44低谷不删除，采样不保证采样间每瞬时；守护非重启服务。
