# Fresh Direct首轮训练与终端样本拟合诊断

Direct的fresh CHEQ reduced-reuse阶段完成首个30条件周期，**尚未学得任务成功，也无收敛证据**。
本次只读诊断解释训练误差的组成，决定继续原登记六周期阶段，不调整mask、replay、reward、
gamma、batch256、UTD1或任何物理/控制合同。其他三方法完整首轮仍由原observer等待。

## 完整首轮证据

- 41250步、36251次更新，30个55秒回合，Task/Strict均0/30。
- 回合reward均值−32.96638，范围−35.14895至−31.85053；不同条件且采集时policy在改变，
  回合序列不能直接解释成固定任务的收敛曲线。
- 失败stage：approach19、carry9、lift1、align1。没有安全abort不等于任务成功。
- 末1000更新critic loss均值9.33414，随机4096条replay的五critic平均TD绝对误差0.40134，
  全30个终端、五critic的平均绝对误差36.20118；不得用平均TD低掩盖终端误差。
- 最终alpha0.0152946、采样策略微分熵−7.13171（目标−7），近动作限幅比例10.12%。
  微分熵为负是允许的，不单凭此判定错误。
- 抽样Q均值67.44449；固定当前alpha的宽松soft-Q全局上界93.19580，超界比例0。
  不超上界不证明Q校准；前期alpha变化、尚未稳定的target和状态混叠仍影响解读。

原完整父checkpoint SHA256为
`15eb22664e7e3f4c8db3eaf4566f33f7b34bf08c596b58f21bebb6eda04cbfba`。
30个terminal结果/完成时刻与episode日志一致，实际MJB hash与登记一致；各回合reward由
transition分量重建通过，诊断网络权重保持不变。核验范围是已保存终端与实际模型，
没有重新运行全子步安全审计或固定策略评估。两幅图已目视核对。

## 终端样本的真实训练次数

按原Replay的seed+53从第1条transition重建mask生成、均匀有放回抽样和拒绝分支，
没有调用学习器更新，也没有重新仿真。**全部41250个Bernoulli mask和最终replay RNG状态
精确吻合checkpoint**，本周期没有拒绝batch，36251次抽样共包含6346次终端样本抽取。
因此这里报告的是本次已发生抽样的精确重建，不是期望次数估算。

| 终端样本被抽取次数 | 样本数 | 参与训练的critic预测数 | 参与训练的平均绝对误差 | 被mask排除的平均绝对误差 |
|---|---:|---:|---:|---:|
| 0 | 1 | 3 | 92.19025 | 91.91556 |
| 1–20 | 2 | 8 | 91.04674 | 91.83065 |
| >20 | 27 | 110 | 15.80927 | 92.74881 |
| >100（上一行子集） | 20 | 83 | 4.84438 | 97.60254 |

mask是每条transition对每个critic是否参与监督的固定Bernoulli标记；样本被抽取多次，
仍不会直接训练mask为0的那个critic。表内20/100只是描述性分组，不是新增训练或收敛gate。
全部终端的in-bag MAE22.67739、out-of-bag MAE92.62802；统计保留全部样本，不删除大误差。
当前较大的总终端误差包含刚进入replay尚少更新的样本，以及被原ensemble规则留出的预测。
这不能证明误差完全由采样次数造成，也不能证明critic已健康：观测不含剩余时间，
终端状态可能与非终端混叠，且任务还没有任何成功样本。

继续训练时应对同类年龄/抽样次数和mask分别观察拟合，不将一次整体MAE直接解释成发散，
也不因高次数样本误差较低而宣布收敛。原四方法完整cycle0/1/3/5审计继续，当前Direct已
从同父checkpoint完整接续到12worker，未在本次诊断中重启或导入任何新权重。

## 产物与局限

集群主机 `rltest-1025--a6ed2ff39b3c-s5gnp35dxg`，产物目录：
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/fresh_direct_cycle00_diagnosis_v1/`。

- `results/DIAGNOSIS.json`、`results/training_diagnostics.png`：冻结完整cycle0网络与训练日志诊断。
- `TERMINAL_EXPOSURE_REVIEW.json`、`terminal_exposure.png`、`terminal_exposure.py`：精确抽样重建、逐终端误差和代码。
- `REVIEW.json`：30终端/MJB、结果及artifact hash复核。

配套仓库JSON记录完整路径、hash、诊断指标和30条抽样结果；大型checkpoint和图留集群。
0新physics、0optimizer更新，正式在途训练独立继续；物理/MJB、gate、actor信息、公共filter、
执行器限制和dt未改。此为第一轮训练诊断，不是充分训练后失败、算法优劣或ESN比较结论。
GPU50%尚未达到，未用辅助占用掩盖；本轮没有另测GPU，不沿用上轮数值冒充新测量。
