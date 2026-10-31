# 600万容量GPU恢复与原生更新验证（2026-10-31）

Goal active。上一轮属于progress：完整CPU回放迁移与容量边界准备已完成；本轮补齐GPU缓存和实际学习更新兼容性。原第96轮三路训练继续，未重启、未派发97。

主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，Python `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。使用仓库sii-research-sync，实际query/fetch/read main `8b39c19760d2e69db66999c7ec05962a37e45335`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。没有子agent。

## 实际检查与结果

源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census_capacity6m_gpu_20261031_v1/check_gpu.py`，独立输出 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census_capacity6m_gpu_20261031_v1`。固定CPU54/nice15/GPU0、900秒上限、三方法各3次隔离更新；运行前GPU0空余47950MiB，实际UUID `GPU-1a6fd25d-dba5-d072-8c61-1f47157e8d44`。原GPU1/2/3正式训练与四卡guard继续。

使用真实完整95三份已hash绑定checkpoint，恢复原census learner及完整4m回放，同时建立6m候选；保留2m/4m历史容量和双架构标记，显式传6m给默认4m的52维wrapper。比较全部保留行的GPU镜像与CPU原件；8533终端的values、indices和32种mask分层一致，不只比较抽样子集。

每方法从同一原learner/Adam/RNG和回放RNG出发，分别在old4m、new6m、new6m_repeat上调用原生65536批次的learner.update。三次批次值与采样RNG相同，全部metrics（含original_sampled_q_loss与条件估计loss）和更新后完整状态digest精确相同，gradient_steps每次恰加1。随后全部learner/Adam/RNG与两种回放RNG恢复原始状态，原checkpoint文件hash和原内存state digest不变。

总计9次临时optimizer更新，0正式更新、0physics、0权重保存。三方法峰值PyTorch已分配显存字节为{'impedance': 6336192000, 'admittance': 7729972736, 'vmc': 7777995264}；不包含guard、CUDA上下文等其他进程，不能当整卡总显存。实际检查进程已结束，GPU0显存已释放，guard继续。

该结果证明同一完整95数据上的容量变更不会改变所测采样和原生更新，不是新数据跨4m后的算法等价、完整96恢复、训练改善或收敛结论。前轮CPU迁移、21负例、合成跨4m、满6m拒绝证据仍见[容量准备](RL_CENSUS_CAPACITY6M_PREPARATION_20261031.md)。

## 正式任务与后续

原101身份在准备前后两端PID/start一致，新增steps{'impedance': 1908, 'admittance': 1908, 'vmc': 2002}，不是全程连续身份观察。保存进度{'impedance': 3968520, 'admittance': 3972012, 'vmc': 3972734}；原三96 learner、90sampler、修正版archive、固定8533终端与全90比较消费者仍运行。GPU43样本最低[74, 69, 70, 68]%、低于50次数[0, 0, 0, 0]；含synthetic guard与本轮临时GPU检查，不等于正式训练吞吐或每瞬时保证。

先完成全96回放/action/reward/原loss及图、真实新terminal、全90比较与固定终端评估，再绑定原94–96九组输入并执行原统计。A94→95的19.7689%稳定必要条件失败及所有历史失败保持。之后按完整96结果决定有限97，绑定真实96全部状态、适配三容量标记的协议/checkpoint/startup/fullreview、进行准确父状态恢复检查，才可接入候选容量；没有自动97/98。当前96仍是4m，原physics/MJB/Task/Strict/actor49/critic52/reward/LR/batch65536/UTD1保持。

Direct33原数值验收、冻结30条件Task/Strict0/0、旧28memory-invariance缺口与恢复2已证保持。指定ESN缺失、最终独立比较与联合收敛未完成。中断须保全最新96 partial，不回退95；MuJoCo物理state未保存。

## 归档

证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS_CAPACITY6M_GPU_20261031/SMALL_EVIDENCE.tar.gz`，12成员，SHA256 `56c1cc5c5a406edf75d4aff6888aaeac9e70c46600cbc88e0edd2021e1bd356c`，全部tar成员与原文件字节核验。小证据在 `docs/evidence/RL_CENSUS_CAPACITY6M_GPU_20261031`；依赖前轮6m准备及原95/96大型SSD产物。HDD仅原254字节LATEST指针，不是完整备份。发布核验收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS_CAPACITY6M_GPU_20261031/PUBLICATION.json`。
