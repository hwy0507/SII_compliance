# 600万回放容量准备（2026-10-31，尚未部署）

Goal active。前一轮属于verified wait：实际检查原训练/等待器/guard仍活跃；本轮完成新的容量候选及真实回放兼容性验证。原第96轮继续，未重启或覆盖其运行时。

主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮沿用sii-research-sync；开工真实查询并fetch/read main `e1f84ca15d10e3d28b4acadf61b335976a18d631` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无子agent。

## 容量与实现

完整96预计I/A/V为3976512/3980000/3981000条，现4m仅余23488/20000/19000，完整97最多新增41250时超限。候选6m保持append-only、拒绝覆盖，保留历史2m/4m容量标记，另加replay_capacity_third。只能从digest绑定的完整4m回放迁入，之后恢复要求三个标记一致。扩容超过4m后与覆盖式ring不同，不声称算法等价或性能提升；每个后续科学阶段仍需有限登记。

原52维violation_replay_class默认capacity4m，因此必须显式传capacity6000000；本次真实三路验证采用此路径。当前正式driver96与协议仍保持4m，候选源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census_capacity6m_preparation_20261031_v1/parameter_replay_capacity6m.py` 未接入正式训练。

按实际5/7/7动作维数，三路CPU回放加设备镜像预计增加5632000000字节（约5.24GiB）。准备前容器可用310.05GiB，swap0字节。这里只是存储估算，正式接入还需GPU运行检查。

## 实际验证

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census_capacity6m_preparation_20261031_v1/REVIEW.json`：三份真实完整95 checkpoint逐hash加载；全部保留行、RNG、原历史容量与52维架构标记精确。CPU CensusCache重建终端2845/2844/2844及全部32 mask分层计数准确，采样1/32/256/65536与原生回放的值和采样RNG一致，load后cache重建也通过。完整learner digest和checkpoint文件hash前后不变。没有创建或更新learner；未声称已完成6m learner/GPU原生更新检查。

独立合成3,999,998→4,000,002检验全部旧prefix保留、边界两步与原4m写入相同、全部cache字段一致、新增4个终端、恢复后65536样本及RNG一致。填充全部6m存储后写入最后有效槽位，额外add被拒且全部数据/size/cursor/RNG digest不变。21个缺失/错误标记、回卷、容量、size、schema、RNG、dtype、NaN、mask/done与shape异常在修改状态前被拒。

验证CPU54/nice15/900秒上限，实际原生进程已结束；零physics、零optimizer更新、未保存辅助权重。原实现依赖及新源码hash锁在PLAN.json，原active96锁定文件复核无变化。容量算术与未来接入要求另见CAPACITY_ARITHMETIC.json、DEPLOYMENT_REQUIREMENTS.json。

## 原任务与下一步

原101身份在准备中的起止两端仍为同一PID/start，steps增长{'impedance': 2358, 'admittance': 2346, 'vmc': 2254}，并非全程逐样本身份观察。末进度{'impedance': 3964942, 'admittance': 3968433, 'vmc': 3968990}。原3learner、90sampler、修正版archive、固定8533终端与全90比较消费者继续。GPU保存窗口73样本最低[74, 70, 68, 70]%、低于50次数[0, 0, 0, 0]；独立guard仍继续，含synthetic占用，不等于科学吞吐或每瞬时保证。

先验收完整96的回放/真实终端增长/原loss及图、全90与固定终端比较，再完成原94–96九组绑定和统计；A94→95的19.7689%必要条件失败及全部历史退化保持。然后依据完整96结果登记是否继续有限97：绑定真实96全部learner/Adam/RNG/replay与digest、CPU/GPU cache及原生65536重复更新恢复，接通三容量标记的checkpoint/startup/archive/fullreview，之后才允许部署。真实跨4m保留及新reward/action/history/bit检查仍待；本次95准备不是完整96接入证明。无自动97/98或Direct34。

Direct33原数值验收及冻结全30 Task/Strict0/0保持，旧28 memory-invariance缺口及恢复2已证保持；指定ESN仍缺，最终独立对比/联合收敛未完成。中断保全最新96 partial，不回退95；MuJoCo物理state未保存。

## 保存

小证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS_CAPACITY6M_PREPARATION_20261031/SMALL_EVIDENCE.tar.gz`，16成员，SHA256 `01678bf0aa60002207d4766f3c540cee142b8f656bb393d41c1d7a681226bcad`，逐成员字节核验通过。Git小证据 `docs/evidence/RL_CENSUS_CAPACITY6M_PREPARATION_20261031`。大checkpoint/replay/journals仅共享SSD；HDD配额满只原地更新254字节LATEST，不是HDD/arm1完整备份。实际发布核验收据将在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS_CAPACITY6M_PREPARATION_20261031/PUBLICATION.json`。
