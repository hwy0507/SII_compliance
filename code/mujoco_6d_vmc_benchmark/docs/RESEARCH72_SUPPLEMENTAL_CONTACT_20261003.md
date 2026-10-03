# 补充全任务接触负载：公开开发后登记、最终开封前固定

2026-10-03 18:58 UTC。本修订仅增加描述性统计，不改 actor、环境、task/strict、
原事件窗口、模型选择规则或恢复定义。真实最终24身份仍封存。

公开 development_001 的全部6个初始ESN候选与原teacher时序图显示：人手主动推压结束后，
放置阶段仍可能遇到静止的人体几何。旧human事件窗口只覆盖person_start至person_start+7秒，
因此不能把旧事件力指标解释成全任务人体接触负载。这是补充统计的事后开发依据，不能写成最初预注册。

新metric_version为 `4-supplemental-whole-horizon-contact`：

- 原contact/recovery以及全局RMSE、实际力矩/速度等字段完全保留。
- `whole_observed_horizon`记录全部实际观测子步：external_robot以及ball/human/rod/edge/pillar。
- `outside_event_window`记录ball/human/rod原事件窗口之前或之后的所有实际子步。
  不等同“撤回之后”；球窗口仍止于person_start。edge/pillar原本就是全程窗口，不定义多余窗外量。
- 统计接触时长、峰值、接触P95/RMS、力模积分、平方力积分、首末接触时间；暴露阈值仍0.05N。
  无接触P95/RMS为NA；积分包括掩码范围内所有力值。提前终止只统计实际观察时长，不补未来零值。
- 力列是各接触力模之和，并非净合力；external_robot不含payload，edge包含robot或payload。
  各列不是互斥分解，禁止相加形成新的总力。
- 最终矩阵逐方法列出全长/短回合各自暴露、缺失与统计，保留失败；旧文件缺此字段记missing。
  补充表仅描述，不据其作配对优越性推断。原严格成功且共同暴露的配对表仍明确标注原事件窗口。

本地14项测试通过，包括迟发人体接触、短回合未来时长、缺失/无接触/失败分离和证据hash关联。
第一次测试入口缺PYTHONPATH导致导入错误，修正执行路径后通过，未改物理或统计来消除失败。
Spark原生NumPy2.2.6只读复算7条完整公开轨迹，全部旧数值/结果字段精确不变；0新仿真、0拟合。
人体系数积分（Ns）如下，不能把这一条件当作最终泛化结论：

| 候选 | 原事件窗 | 全程 | 窗外 | 窗外接触时长s |
|---|---:|---:|---:|---:|
| 原teacher | 91.283825 | 91.451241 | 0.167416 | 0.02675 |
| ESN301 point | 23.010806 | 23.436313 | 0.425508 | 0.07315 |
| ESN301 temporal | 28.467455 | 29.778006 | 1.310551 | 0.26330 |
| ESN302 point | 20.682762 | 22.113728 | 1.430966 | 0.29505 |
| ESN302 temporal | 29.779467 | 30.789439 | 1.009972 | 0.17725 |
| ESN303 point | 88.082210 | 88.082210 | 0 | 0 |
| ESN303 temporal | 16.913817 | 17.176420 | 0.262603 | 0.01770 |

共享主机 `arm1@192.168.31.70`，根
`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：

- `supplemental_contact_regression_v1/`：独立实际执行源码和results/000至006.metrics.json。
  results/REGRESSION.json SHA `29ee8fff3ccd85bc50746341814d8278f64fd526aae9c92e099220ef29075c04`；
  逐产物hash已逐一核验，原始轨迹/execution未改。
- 新指标源码SHA `e4416fdd2c8c5bf3b9d37db3278ae9ca24b3d07b096d7f58c6991dc4d6f8f680`；
  回归脚本SHA `1070d5199df4b23af53d312586eedc409abda7fa3974ab3eaa24a4ccfbd1d982`。
- `public_condition1_esn_curves_v1/trajectories.png` / `.pdf`：全部6ESN候选加原teacher，
  同一条件全部完整55s，10ms最大包络；不能把包络积分当力积分。
  PNG SHA `5fd2b34969ed991fc93e7cb1d05f387c2764db825dd5178620653ca75b55e144`；
  PDF SHA `7baca50dea03c4cc5156a23060e30bad0d87a1e784c3158a09da03aa83910475`。

运行中的冻结runtime保持不变；未来最终审计使用v4。已运行开发审计若仍v3明确保留版本，
需要补充时另存只读重算产物，不覆盖原始receipt，也不伪称所有开发轨迹已经补算。
