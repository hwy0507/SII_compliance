# 未建图桌边障碍：规划受阻与柔顺恢复对照

用户2026-10-02提供`桌角.mp4`，要求在pick-and-place中加入“执行途中才发现
规划路线被障碍卡住”的情形，检验已有柔顺控制器是否能让位、蹭开、恢复并放置。
本轮先改独立环境并做有限闭环验证，不预设ESN必须优于名义执行，不重训模型。
开工/收工前核对main `f3437ade3a44e52db4a118d5c112e6cabbb48d41`、baseline
`699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0`；baseline未改。
参考视频SHA256：`2f12464ca85e0a6a54047548ac03e98ab8524170970963c514861e77266b81c5`。

## 场景和公平对照

- 沿用靠手桌角目标`[.690,-.310,.545] m`和原55秒放置定义：松手、由目标桌板支持、
  XY<25mm/Z<15mm，最终连续0.5秒稳定；完整定义见[前一任务报告](PLANNED_HAND_CORNER_TASK_20261002.md)。
- 在上层桌板上增加固定凸边`office_v5_unexpected_edge`，中心`[.610,-.250,.555] m`，
  全尺寸`20×90×70 mm`，底面z=.520、顶面z=.590；摩擦`.6/.01/.001`，
  solref`.002/1`，solimp`.99/.999/.0001/.5/2`。从初始时刻存在，不穿模生成/瞬移。
- 离线规划器的先验地图遗漏这个凸边。目标、离线参考路线/姿态、任务进度逻辑对各方法相同。
  在线无视觉、距离、障碍位置或事件时钟输入；接触真值只用于事后审计。
- 球2秒、人手3–10秒、棍12–21.5秒的顺序扰动保留。名义组使用共同WBC跟踪器、
  零学习残差；“规划失败”在这里特指**固定先验地图路径的名义执行失败**，不表示所有
  路径规划算法都无解，也不把已有底层WBC说成毫无物理柔性的理想位置源。
  `nominal_clear`只表示没有新增凸边，原球/人手/棍子仍存在，不是完全无扰动环境。
- ESN/MLP沿用各自已训练的128宽度、48D本体/参考输入、7D输出策略，无在线VMC混合。
  原权重未训练/调整；两者原训练seed分别2026100152/2026100153，本轮不是多seed排名。
- 执行器幅值/变化率限制和原任务阈值不变。新strict为放置成功、原physical_valid，
  再加凸边—机器人/物块最大穿透≤0.2mm；这一附加检查对所有方法一致。
  接触覆盖仍单独报告，不能用“没碰上”冒充接触柔顺成功。

## 共用路径跟随修复与保留证据

首轮v1允许非终端路点跨平面接回，但误用总距离<80mm约束接回，包含了沿路径的前进距离。
使用独立几何审计得到的绕行位姿做**不步进物理的虚拟跟随检查**：旧逻辑卡在carry路点14/27。
修复为沿切线方向已跨过路点、垂直偏离<80mm，终端路点仍必须实际到达，姿态阈值不变。
同一虚拟路径在v2达到27/27并进入下一阶段；测试还拒绝90mm横向偏离和虚假终点到达。
这只证明公共进度逻辑能接回，不能当作真实机器人成功绕障。

v1四条完整失败/成功证据全部保留；v2使用相同几何和权重重新跑四条，不挑结果。
配置`configs/office_unexpected_edge_20261002.json`标记整体协议v2；结果中的
`unknown_obstacle_protocol=prior-map-omission-edge-v1`指未变的物理场景，
具体跟随版本以`.plan.json/rejoin_rule`和配置hash为准。

v1开发结果（MuJoCo3.11.0、dt=1e-4，每条55秒/550000物理子步）：

| 对照 | task/strict | RMSE mm | 峰值力矩 Nm | 峰值速度 m/s | 外部穿透 mm | 新凸边接触 |
|---|---|---:|---:|---:|---:|---|
| 名义，无新凸边 | true/true | 22.767 | 42.020 | .068210 | .093270 | 不适用 |
| 名义，有新凸边 | false/false | 25.275 | 37.106 | .067193 | .151255 | 11.3937–55秒 |
| 原ESN，有新凸边 | false/false | 26.496 | 37.763 | .084326 | .133959 | 未触及 |
| 原MLP，有新凸边 | false/false | 24.843 | 36.977 | .061384 | .095995 | 未触及 |

名义阻塞时接触累计43.6064秒、峰值32.7909N、凸边穿透.066881mm，停在carry。
ESN最后5秒路点位置误差15.35–16.01mm、姿态误差.0184–.0201rad，未碰新凸边就停滞；
不能把该失败直接归因于新凸边，也不能说ESN已学会绕过。旧ESN在前一无凸边任务也曾失败。

## v2共同修复后的结果

四条55秒重跑全部完成。各条qpos、qvel、applied_action、stage数组与各自v1逐元素相同，
因此三指标/接触/成功结果与上表一致。这说明修复了实际存在的接回逻辑缺陷，但现有
策略尚未走出需要该修复的绕行轨迹；不能把逻辑修复称为学习效果改善。
四条共同规划hash为`ddaf2d8871aa5384288279e5d8394c903313666ebe6b4781dc51a1de5bf0385e`；
三条阻塞组MJB相同，两个学生action重放误差为0，ESN储备池重放误差为0。
四条视频实际解码1375帧、GIF275帧，均为完整55秒，三视角已目视核验。
详见v2目录`CROSS_ROW_AUDIT.json`及每条`AUDIT.json`。

结论：已复现未知凸边使名义执行卡住；尚未复现“加入已训练柔顺控制器即可完成放置”。
接下来应先适配新参考下的纯ESN/MLP，使它们能正常推进到障碍，再采集并验证
接触—让位—脱离—恢复的闭环轨迹。单凭降低全程RMSE不能证明做到这一点。

## 几何审计的范围

在归档MJB上，用审计器显式知道凸边的位置：最短payload绕行路线发生夹爪碰撞；
正y方向固定绕行与已有柱子/link6碰撞；负y方向经y=-.380m的绕行通过payload扫掠、
IK与机器人静态路点碰撞检查。该审计不提供给actor/实际规划器，不步进物理。
它支持“存在几何候选绕路”，尚不证明动态执行或柔顺接触可成功。
原`INFORMED_DETOUR_EXPANDED_AUDIT.json`成功字段正确，但残留上一候选的顶层reason；
保留原文件并用`INFORMED_DETOUR_CORRECTED_RECEIPT.json`独立复核，避免覆盖证据。

## 复现、共享与未完成项

本机计算：单MuJoCo环境、单线程，systemd cgroup MemoryMax=3GiB、SwapMax=0。
解释器`/home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python`。
启动器`tools/run_unexpected_edge_pairing_20261002.py --output <全新目录>`按名义清场、
名义受阻、ESN受阻、MLP受阻顺序运行；学习组启动前核对名义组MJB hash。
每条保存execution、命令、配置、源码tar/hash、原checkpoint/training record、原始状态/动作、
子步指标、接触事件以及55秒25fps三视角MP4和5fps GIF。

权重：ESN `9f4b5a8168142595873ff1c8fdcaa3b2186b7a1d1edab916d2bbd38fe5988023`；
MLP `d9f026896d9dd1952d3c907286bc32a25d810fd8553402e1cf235f3ba6f775d4`。
阻塞MJB `3e7a6859a3e0b6ea9e6e1e4a463974f733fca8cf375887d6dc49d440d587cd5a`；
清场MJB `5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9`。
v1共同规划hash `eb57fdee62f7309310950c6ec0aa6d994a7e9d1f263d5c818dc1e23dd58fb6b0`。
历史源码以每条source_overlay为准，不拿当前源码冒充v1。

已逐文件核验189项服务器共享证据：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/unexpected_edge_contact_review_20261002_v2/evidence/`。
根目录`archive_manifest.json` SHA256为
`91dc23cc9d20d8ab4815a2c07164db41d135521d5995774a5441ff9d45bb1544`。
其中`unexpected_edge_20261002_v1/`保留首轮，`unexpected_edge_20261002_v2/`为共用修复后结果；
各组`source_overlay.tar.gz`为实际执行源码，根`tools/`与`configs/`保存新增审计/重跑入口。
原始execution中的本机路径未改写，本机outputs保留执行缓存。

v2媒体相对上述共享根的路径（各组还有完整GIF）：

- `unexpected_edge_20261002_v2/nominal_clear/media/replay_threeview.mp4`
- `unexpected_edge_20261002_v2/nominal_blocked/media/replay_threeview.mp4`
- `unexpected_edge_20261002_v2/esn_blocked/media/replay_threeview.mp4`
- `unexpected_edge_20261002_v2/mlp_blocked/media/replay_threeview.mp4`

尚未完成：新路径下原学习策略的可靠执行、接触后恢复放置、正式dt=5e-5验证，
以及新环境上多条件/多seed的ESN对baseline比较。不能凭单个场景预设论文优势。
