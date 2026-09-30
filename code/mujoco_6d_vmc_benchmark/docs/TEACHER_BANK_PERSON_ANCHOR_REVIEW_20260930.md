# v10 人手推碰：首轮三个控制器的独立连续接触复核

范围仅为训练搜索`active_long/c00/anchor0`，不是独立验证，不推广到其余999个训练环境。
原始回合均已核验归档到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v10/search/active_long/`，
根下分别为`vmc/c00/0`、`admittance/c00/0`、`impedance/c00/0`。

三者没有满足完整人推曝光筛选，但失败机制有区别：

| 方法 | 最长连续接触 s | 同一段最大有向位移 mm | 跨间断宏观最大位移 mm | 解释 |
|---|---:|---:|---:|---|
| VMC | 1.2516 | 9.09595 | 27.79014 | 时长通过，单段位移距10mm还差0.90405mm |
| 导纳 | 0.1838 | 1.71166 | 27.28325 | 宏观移动明显，但连续段时长、位移都未通过 |
| 阻抗 | 0.0074 | 0.03322 | 5.51947 | 连续段与宏观有向位移都不足 |

VMC/导纳最大位移来自各自最长段；阻抗的最大位移来自另一个0.0039s段。
各最大位移段的净位移在上述显示精度下与最大值相同；完整全部接触段的净/最大/最小位移
保存在review.json。宏观位移原点是施推时窗内第一个力阈值合格子步，并非施推前位置。
宏观轨迹同时包含名义任务运动，没有无推碰counterfactual，不能把全部位移因果归于人手。

三个控制器的力阈值间断中位数均为0.1ms，间断≤1ms比例分别93.64%、98.85%、99.97%。
这些是`force <= .05N`导致的统计分段，不等于几何上明显脱离，也不能没有额外证据就归为
数值假象。本轮保留已注册连续条件：press/hold时窗内接触力>.05N、持续>.4s、同段沿推力
方向最大位移≥1cm；没有连接间断、减小阈值或将27mm宏观位移替换入录取规则。

## 可复算证据

每条原audit清单逐文件SHA核验通过；从`exposure.npz/person_physics`的550000×6原始子步
独立重建每个连续接触段，并绑定`substep_metrics.npz`时间和dt。重建结果与保存schema2段的
最大差≤1.22e-13；accepted_run_indices与原曝光失败原因完全一致。未运行仿真、覆盖原audit
或修改冻结源。脚本使用单线程、2GiB地址空间上限，约0.5秒完成。

- 复算脚本：研究目录`tools/teacher_bank_person_anchor_review_20260930.py`。
- 产物：`outputs/teacher_bank_v10_person_anchor0_review_20260930/review.json`。
- JSON SHA256：`2f94c7999c3732582e38b69e005c75e257dda84f510b1f190842ac8e145c7835`。
- 脚本 SHA256：`2c029b7acb734f3ae247cb4db67b8f9754b42414fbb847074378f1d18293397c`。

上述脚本/JSON及首轮27回合预算汇总已逐文件核验共享至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0633/evidence/`，
保留tools/outputs相对路径；本报告随Git源码发布。原始三回合已共享。
这些证据支持继续固定预算控制器搜索；不证明参数优化必然能通过，也不提前启动ESN学习失败标签。
