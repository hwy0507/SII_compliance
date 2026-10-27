# 参数回放4m容量准备（2026-10-27，尚未部署）

Goal active，正式训练仍为原参数45（417803/417804/417805）和Direct take27（3712293），冻结41原316550/316551/316552继续。本轮前一goal turn属于实质进展：完整44审查、正式45启动和Direct固定窗口登记；本轮新增容量候选及独立验证，不重跑已完成科学实验。

共享SSD B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；源码B/repository/SII_compliance。开工实际查询/fetch/read远端main06df65e6fb9b527473c2b276d3109c5cf8809013、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，未变化。沿用sii-research-sync，无子agent。

## 容量问题与明确边界

完整44 I/A/V1852430/1852250/1853250。每轮最多41250动作，若45–47均全程则完整47为1976180/1976000/1977000；48预算上限2017430/2017250/2018250超过现有2m。当前追加回放在满容量时拒绝覆盖，必须提前准备容量方案，不能删除旧数据或绕过保护。

独立候选扩展至4m，拟在准确完整47→48边界进入；正式45、46和固定43–45窗口保持2m。当前内存可用约836GiB、GPU每卡49140MiB；新CPU验证不创建GPU工作负载。容量扩展保留全部旧数据，超过旧2m边界后与覆盖式ring行为不同，不宣称算法等价或任务提升。

## 已完成的检查

`B/runs/parameter_capacity4m_preparation_20261027_v1`；原supervisor915470/worker915509执行600秒有界CPU54/nice15验证，已FINISHED通过，无物理、优化或权重保存。冻结源快照在B/runtime同名目录，小证据docs/evidence/RL_PARAMETER_CAPACITY4M_20261027。

- 三份真实完整44 checkpoint：全部回放字段、RNG和完整learner digest不变；4m恢复/再次恢复精确，保留原2m容量标记并增加独立followup标记。CPU device-cache与原采样的1/32/256/65536批和采样RNG均精确。每方法7个错误marker/旧父RNG/容量/回卷等负守卫拒绝且状态不变。
- 独立合成1,999,998→2,000,002边界：全部旧prefix、缓存镜像、恢复marker/下一65536与RNG一致；满4m拒绝写入，整个状态digest保持。合成数据未写入正式replay。
- 额外11个异常状态守卫：dtype、NaN、非二元mask、shape、数组缺失/额外键、非法RNG、负/浮点size、历史marker缺失、额外state字段，均在改变状态前拒绝。实际写入最后有效slot3,999,999后size/cursor=4m，再add被拒，首旧行/末行/RNG不变。
- 新有限4m driver的11个契约负守卫通过；仅准确parent47可首次进入，之后历史followup阶段不可改变。原训练器、物理采样、learner安装尾部与2m driver逐字节相同。AST/source hash通过。

最初用系统python运行静态契约检查因无numpy在执行fixture前失败；已记录STATIC_INTERPRETER_CORRECTION，并使用原B/env/bin/python完成。没有修改正式环境或训练。

## 实现与限制

新增 `parameter_replay_capacity4m_20261027.py`、`validate_parameter_replay_capacity4m_20261027.py`、`resume_cheq_capacity4m_pool30_20261027.py`。原helper/driver与当前runtime未改。

4m helper只允许digest绑定的未回卷2m父进入，恢复保留replay_capacity_extension原历史marker，并新增replay_capacity_followup；完整state schema、finite、mask与RNG校验在loader写入前完成。继续4m必须双marker完整且一致。

新driver保留原entry23容量证据/历史链与原算法、batch65536、UTD1、terminal128、I-min/A-V-mean/actor-min、30sampler CPU分配；新replay_capacity_followup_stage固定parent47、2m→4m、原entry23及准备证据，正式入口再绑定实际47的checkpoint/replay digest。现有本轮验证只有真实44回放、CPU缓存与driver静态契约，不是实际47全learner恢复、GPU缓存更新或正式跨界证明。

## 下一步

1. 四正式与冻结41继续，核实际PID/进度避免重复。原参数43–45 waiter2190600、46准备504393、Direct28准备154584、新Direct27–29 waiter336744保持；最新训练交接仍见RL_PARAMETER45_SERL27_29_20261027.md。
2. 完整45审查与43–45统计后接46；再接47。4m不进入原43–45窗口。
3. 准确47完成后需实际4m全state/next65536 check-only、新48协议、科学PRELAUNCH以及支持双marker的startup/fullreview/归档入口；这些尚未完成，不能直接用旧2m审查器或盲目启动48。DEPLOYMENT_REQUIREMENTS.json已记录边界与要求。
4. 48实际新数据跨2m时须独立检查旧行保留和新增reward，不能以本轮合成测试替代真实跨界。若后续稳定窗口跨扩容边界，要显式披露。
5. 所有reward稳定/loss健康、冻结验证和最终ESN/SPT比较仍未全部完成，不能标Goal complete。大checkpoint/raw在共享SSD，HDD仅LATEST指针；本轮小包另记，不称HDD/arm1全备份。
