# 三类 teacher 数据与经典 baseline：10 小时工作记录

用户授权窗口：2026-09-30 03:48:16—13:48:16 UTC（北京时间 11:48:16—21:48:16）。
截止时停止派发新仿真，已开始的回合允许完整保存；不能把场景定义数当成成功示范数。
本轮新增的是训练域，不修改冻结综合测试环境、原任务 gate、执行器或 actor 输入。

## 固定的研究目标

| 类别 | 训练配置数 | 独立验证配置数 | 训练域变化 |
|---|---:|---:|---|
| 被动厚桌角 | 1000 | 100 | 连成一体的厚边缘、水平角度、位置、宽厚、摩擦、负载 |
| 主动短时碰撞 | 1000 | 100 | 球/椭球/胶囊体，质量、尺度、水平入射角、速度、发射时间 |
| 主动持续接触 | 1000 | 100 | 人手/棍/平头推板，水平角度、推程、驱动力上限、持续时间、质量/尺寸 |

每类采用 Latin hypercube，split 和 seed 在调参前冻结。被动碰撞的实际接触时间、峰值力
是闭环结果，不声称直接采样了“被动撞击力”。当前角度覆盖是水平旋转，不声称已覆盖任意
三维来向。短时物体发射前固定在初始化位置，发射后为自由物理体；发射目标在运行前由
归档 nominal 轨迹离线确定，不追踪本回合实际机器人。该假设不进入 actor。

物理配置 hash 仅含真正作用于该类场景的字段；每条仍须验证编译模型 hash、初始几何、实际
接触及任务完整执行，不能仅凭不同 seed/hash 认定数据有效。未击中、初态非法、接触不足、
失败控制与证据损坏分别保留。

## 三种方法与公平预算

- VMC：既是纯 ESN 的 teacher 数据生成器，也是独立 model-based baseline。
- 导纳：复用 ReferenceAdmittance，以估计外力驱动 M-D-K 参考偏移及 WBC residual。
- 阻抗：复用 MovingEquilibrium，执行 `bias + Jᵀ(K e + D(v_ref-v))`，经过相同力矩限幅／
  变化率限制；不把它改名成 VMC，也不把它的零 action7 当成 ESN 的有效动作标签。

初始计划每方法每类别16个候选×3个anchor。v4完整回合实测98.3秒计算，另需归档；
在尚未开始参数优化前，将v5固定为每方法每类别6个候选×3个anchor，3个初始点＋3个
约束GP贝叶斯候选，共162回合。先寻找任务/接触/物理可行性，再优化性能；不解封旧保留集。
VMC/导纳为 7 维，阻抗为真实 5 维，固定其仅用于阻尼参数化的质量/惯量，避免搜索冗余维度。
同预算指实际模拟回合上限相同，不强求不同物理方法有相同参数维度。
搜索按轮次、类别和方法交错派发，防止截止时间前只跑了某一种方法。

参数选定后每类每方法锁定一个候选，在相同 1000 个训练环境执行；VMC 轨迹接受完整序列筛选，
另两方法保留配对 baseline 结果。当前不做 ESN 训练。某经典法无可行候选不阻止其他方法，
选其约束优先的最好已观察候选并明确标注不可行；任何失败轨迹不能成为ESN标签。
验证集只在候选锁定后运行，不回流优化。为避免1000环境长采集挤掉全部验证，v5先执行
每类预定索引0/1/2共9个验证环境×3方法，然后按剩余窗口采集；其余97/类仍未运行。

## 筛选与审计

首先保留原 task/strict、外部穿透 ≤0.2 mm、实际力矩幅值与 4 ms servo 变化率要求。
额外训练曝光条件：厚桌角仅统计 face/连接边缘在 lift/carry 的承载接触与净上抬，排除最终
放置桌面支撑；手推需持续接触中的有限让位；杆推需接触中切向移动且在撤回前脱离。
这些是新训练数据的纳入条件，不改原正式测试 gate。接触真值只供评估，不进入 actor。

v5可行候选采用分数：`RMSE/0.05 + 0.3*max_joint_torque_ratio + 0.1*retreat_start/55`。
原v4 action_delta项在搜索前移除：阻抗直接输出力矩，action7恒零，不能据此获得平滑优势。
动作差分仍报告为方法内部诊断。RMSE 为完整物理时间的 waypoint 误差；retreat_start 是效率
代理，不能称作严格任务完成时间。峰值速度仅报告，不正向奖励速度尖峰，不新造正式速度 gate。

保留 canonical48 观察、原始 action、过滤后 action7、物理 twist/WBC scale、实际执行力矩、
速度/误差、teacher 内部状态、接触曝光记录、源码/配置/seed/模型 hash。VMC 和 filter 独立
重放；过滤后 action7 再过独立 reset filter 必须重现相同命令。NaN、错误形状、缺少物理子步、
不连续时间必须拒绝。明确物理 abort 的短回合保留为失败，不当作管线坏掉。
导纳重放目前仅覆盖 M-D-K 与动作归一化，不声称完整 FK/WBC 独立复算；阻抗重放参考积分、
记录的 Jacobian 投影和共享 limiter，并在验证单位力矩传动后将每个servo输出与其持有区间的
物理qfrc_actuator逐项对照，不声称重放了整个MuJoCo。三方法配对结束须验证相同MJB hash。

## 执行与恢复

本机一个 MuJoCo 子进程、1 线程、MemoryMax=3 GiB、MemorySwapMax=0。子 agent 并行负责
实现、静态审查与小型测试，不能未经协调另开仿真。冻结 Python/MuJoCo 3.11；先查宿主进程
与 systemd（沙箱 ps 可能只看见自己的 PID namespace）。

入口：`tools/teacher_bank_campaign_20260930.py prepare|pilot|run [--archive]`。
每条 run 单独 execution.json、request、raw/audit；源码不可覆盖。归档先写 incoming，逐文件
SHA256 核验再发布到服务器 `runs/main/<campaign-name>/`。传输未完成不称已共享。
长时任务 heartbeat `teacher-10` 每 20 分钟检查，截止 13:48:16 UTC；服务和 campaign lock
避免重复启动。实际可完成量由 pilot 测得吞吐决定，10 小时优先级高于最大回合数上限。

## 当前状态（初始化及独立审查阶段）

已完成：3300 个可复现配置；三方法接入；贝叶斯搜索/单进程恢复框架；动作、子步与曝光审计。
新测试54项通过；全部是小型正确性测试，不能代替动态表现。
独立审查修复了滤后标签未校验、NaN误差被吞、子步缺失仍晋级、合法
物理提前失败使管线停机，以及 numpy 配置在回合结束时不能 JSON 序列化的问题。

旧初始快照保留：`outputs/teacher_bank_three_domains_20260930/` 在物理运行前停止。
v2 首个被动场景被初态审计拒绝：新增连接边缘与机器人初态穿透 1.6–7.8 mm；没有把它算作
有效轨迹。其失败及源码已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v2/`。
其中 `source/tools/` 和 `source/scripts/` 是该轮真实代码；`pilot/passive_corner/vmc/` 是失败记录。
v2 源码目录还误包含历史 scripts/outputs，后续快照已排除；未删除历史数据。

连接结构已改为绕过初始手爪的两段刚性连接，42 个不同训练 fixture 初态审计通过（未积分）。
见 [几何预检](TEACHER_BANK_GEOMETRY_PREFLIGHT_20260930.md)，不由初态通过推断动态成功。
v4首VMC完整回合：task/旧strict通过，但真实face曝光缺失，未入库。RMSE36.149mm、
峰矩48.367Nm、峰速0.06160m/s。其导纳在物理运行前暴露字符串adapter误匹配hybrid_teacher，
已用精确目标替换及真实源码静态测试修复，失败原样保留。
v4 的 source（206 文件）与 metadata（2 文件）已逐项 SHA256 核验到：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v4/`。
v4以上两条记录均已核验归档。原face偏离payload上抬扫掠域至少26.16mm；旧corner记录同样
不构成face上抬接触成功证据，详见 [曝光诊断](TEACHER_BANK_CORNER_EXPOSURE_DIAGNOSIS_20260930.md)。

已停止：v5 pilot，服务`teacher-bank-pilot-v5-20260930.service`，04:30:24 UTC启动。
新训练域face按转角后的右边界和顶部对齐，六个代表fixture初态通过；其首VMC动态结果
仍失败：face先挡住下降手掌，全程停在align，不能进入teacher库。导纳、阻抗也停在align。
阻抗后置审计因NPZ反复解压保留view触发3GiB限制；修复一次读列后，用原550000子步独立
复审4.39s完成，13750条servo命令→实际力矩误差0，仍拒绝任务失败；未改原execution记录。
修复并不修改仿真，旧失败完整保留。后续几何修订须另存版本，不覆盖这次负结果。
v5源码209文件、metadata2文件已核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v5/`。
运行中数据完成后逐条核验归档，尚不声称全部已共享。
当前运行：`teacher-bank-active-v6-20260930.service`，只跑两个主动类别×三方法的完整pilot。
厚桌角上沿的新几何仍在离线研究，未据初态通过宣称可完成任务。
未完成：有效动态 pilot、完整调参、3000 条训练环境执行及各类 1000 条有效 teacher 配额、
独立验证、ESN 蒸馏。当前成功采集数为 0，不能由“3300 个定义”推断成功率。
v3 仅准备、未运行，几何修正通过预检后使用新冻结快照继续。

协作复核：04:15 UTC 远端 main 仍为 `38caf3152282df4963435bb65c11c93a1e4fffa5`，
baseline 已更新为 `5bc21d8d19eaf60691f561f0ad9dd4409749e667`；已读其新日志。
该分支在 Spark 做独立 SimbaV2 奖励训练，冻结其训练布局和配对种子，并修复旧 RL 额外
残差包络/错误载荷指标。此处不合并其分支、不占用其服务器仿真槽位，也不把新训练域
定义当作 baseline 已完成的最终共同评估。
