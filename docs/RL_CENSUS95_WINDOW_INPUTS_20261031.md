# 固定94–96窗口的完整94输入核验

Goal active，原第95轮三路训练继续，尚未收敛。主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。开工实际query/fetch/read main `faae0cfedf3e397f6cd981e81d30b774b4f6d2aa`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，保留并行非RL工作；沿仓库sii-research-sync流程。

## 本轮实质进展

固定统计目录 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census94_96_reward_stability_20261031_v1` 的PLAN/SOURCE_LOCK/audit/review_saved/binding_rules/bind_inputs保持原字节。窗口94–96、相对5%、nearzero1、5000bootstrap、seed2026102861不变；原意向仍是94已启动且首完整回合结果前登记，未追溯改写。

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census95_window_inputs_20261031_v1/COMPLETE94_INPUT_MAP.json`绑定三方法真实完整94，每组11项：protocol、review、health、finished、episodes、optimizer、loss_plot、health_plot、loss_review、plot_inspection、checkpoint。check_complete94_inputs.py从锁定binding_rules的validate_registration抽取原内层逐组AST，全部语句ast.dump逐项精确，并以真实m/c=94执行；没有虚构95/96或修改全九组门槛。EXTRACTED_GROUP_SOURCE记录源码hash和抽取范围。

三组逐个实际加载完整94checkpoint，验证完整边界/协议hash、census marker、历史与violation架构、52维全回放、4m容量和计数；核验父链review、完整30回合和41250次原optimizer、步号连续、update_index0、原抽样loss有限非负、q_loss与条件估计相等、Task/Strict/abort和reward汇总、模型身份以及两实际图/原查看记录。三方法Task/Strict18/17、15/14、17/17保持；这表示输入完整性通过，不是loss健康或reward稳定通过。三个checkpoint及绑定文件在验证后hash仍一致。

随后将这三组真实输入交给原未改的全九组validate_registration，被 `All nine complete input groups required` 拒绝。完整95/96 FINISHED仍不存在，统计目录没有REGISTRATION或REVIEW，没有运行bootstrap或改变失败门槛。最终必须在三轮全九组真实完成并查看实际图后重新执行原完整binder。

## 当前训练和待办

原101身份连续180.155s/19样本保持，steps增长{'impedance': 1749, 'admittance': 1741, 'vmc': 1454}；保存总steps{'impedance': 3916991, 'admittance': 3920480, 'vmc': 3920688}，完成条件{'impedance': 0, 'admittance': 0, 'vmc': 0}。身份包括3learner、90sampler、archive、原固定8443终端和全90条件两个等待器以及5个GPU守护进程。本轮仅有限只读检查与观察，没有新增训练或比较等待器。

下一步等完整95原archive/review/health/loss完成，核对两原比较消费者结果，实际查看图并核验保存算术；运行 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census95_comparison_20261031_v1/check_terminal_population.py --complete` 检查全部95终端增长与回放done。之后依据完整95科学结果单独决定有限96，无自动96或Direct34。94–96统计仍须全部95/96真实输入，不能把目前的三组完整性检查当完整窗口绑定。96可容纳于4m；97需要单独容量决策，不覆盖旧回放。

第95轮前5000 I反复尖峰/actor上移、第94轮A short0200成功丢失、原90–92失败及所有历史退化保持。Direct33原数值验收与冻结30例Task/Strict0/0、旧28证据限制、指定ESN缺失不变。若中断，保留最新95 partial的完整权重/Adam/RNG/replay/journals，另登记census-aware部分恢复；不回退94重跑95，MuJoCo状态未保存。

## GPU与交接

原独立guard `/tmp/sii_gpu_util_guard_20261031_recovery_v1` 保留，科学结束仍运行，不创建STOP，不是重启服务。当前39样本/192.907s，最低[72, 66, 71, 71]%、低于50[0, 0, 0, 0]、末值[79, 74, 71, 90]%。synthetic负载与实际训练吞吐分列，不承诺每瞬时利用率；旧主机切换0%历史保留。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS95_WINDOW_INPUTS_20261031/SMALL_EVIDENCE.tar.gz`，30成员/35181字节、SHA256 `76fc669c0c05c1746efeab643221a490d842e0c4c5d329d4897807083eedfab6`，逐成员字节/AST/JSON已核验；52维大回放、checkpoint和原始日志仍在共享SSD，通过input map引用。发布提交/实际远端字节收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS95_WINDOW_INPUTS_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD原LATEST仅原地更新254字节指针，非HDD/arm1完整备份。
