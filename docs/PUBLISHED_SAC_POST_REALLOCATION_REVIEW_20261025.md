# SAC采样扩容后新增完整周期的只读复核

本轮新增复核SAC Direct cycle7和VMC cycle4，不重跑此前周期，也不新增仿真或学习更新。
两路critic loss、Q估计和终端误差继续增长，不能称健康收敛。保持已登记的完整周期资源交接，
不因这些SAC结果再次修改新fresh CHEQ的超参数。

| 指标 | Direct cycle7 | VMC cycle4 |
|---|---:|---:|
| 累计真实步数 | 344824 | 227259 |
| 累计梯度更新 | 643164 | 412500 |
| Task success /30 | 0 | 17 |
| Strict success /30 | 0 | 16 |
| Strict被动/短期/长期，各10 | 0/0/0 | 0/9/7 |
| 完整55秒回合数 | 29 | 30 |
| 周期reward均值 | -34.605262 | -4.569452 |
| 末1000次更新critic loss均值 | 1722495 | 10207173 |
| 采样Q均值 | 140242 | 160018 |
| replay终端Q绝对误差均值 | 11622 | 39222 |
| alpha | 15.7929 | 38.1704 |

Direct与已复核cycle5比较，loss216712→1722495、Q59261→140242、终端MAE3445→11622；
这是5→7的跨度，不伪称与未在本轮完整诊断的cycle6直接比较。VMC与cycle3比较，
loss3062208→10207173、Q82018→160018、终端MAE23290→39222；Strict从18降为16。

Direct全部30项失败停留在approach。被动0200在663个action/26.52秒因
`global_penetration_exceeded_2mm`提前结束，保留在分母，不能把整组写成30个55秒回合。
VMC的14项Strict失败中13项carry、一项retreat；后一项是短期0600，Task=true但Strict=false。
保存的actor interval独立归约外穿透峰值0.223470232mm，与rollout统计一致，超过原0.2mm；
接触对为球与fr3_link6。冻结代码的physical_valid/Strict判据一致，未放宽该gate。

核验范围：两组各30条件完整集合、60个terminal结果/时长/原MJB hash、fixture/dt/参考计划，
不可变checkpoint副本与诊断hash、reward分项重建、网络无变化；两张优化诊断图已目视复核。
只读进程已结束，0新增physics/optimizer updates。终端误差可因缺少剩余时间观测而非零，
判断依据是其量级和持续趋势并结合loss/任务表现；不能单凭MAE非零判定实现错误。
本轮不是全子步filter/执行器/舒适性重审，训练成功不等于固定策略acceptance。

不同周期和继续变化的policy不构成采样器数量的因果消融；图只覆盖新run日志段，
不是跨run拼接后的收敛曲线。没有选择最终Tref，没有生成ESN排名。

实际产物：集群主机rltest-1025--a6ed2ff39b3c-s5gnp35dxg，
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/sac_post_reallocation_cycle_review_v1/`。
其中REVIEW.json记录60个终端/模型收据hash，配套仓库JSON记录总结与产物hash；大型checkpoint和图留集群。

原新CHEQ三learner及Impedance原SAC1557140已重新核验活跃并推进，资源协调1956030与
审计1968149仍等待原依赖/完整周期，无重复派发。新的四路健康收敛、资源交接、GPU50%、
最终固定矩阵/SPT/指定ESN比较仍未完成。Goal保持active。

已fetch远端main a52dfba4486af8d263d5cd0a976c3102482ff249、
baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，无新增；未更改源码或冻结训练设置。
