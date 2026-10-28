# 用户视频对应的三类独立场景：最新版 VMC teacher 重跑

2026-10-28。此次以用户提供的三个 MP4 为场景定义。此前由综合场景隔离得到的桌面凸起、球与推杆演示，不能代替这三个历史特化场景，尤其不能将桌面凸起等同于下述厚桌沿任务。正式 108/180 回合比较、训练数据、RL 运行均未修改。

## 场景来源与复现边界

路径均相对 `code/mujoco_6d_vmc_benchmark/`。视频 SHA256、大小及完整结果索引见 [RESULTS.json](evidence/video_reference_vmc_20261028/RESULTS.json)。

| 用户视频 | 找到的已有场景/渲染入口 | 本次保留的物理含义 |
|---|---|---|
| 棍子（有挡板）.mp4 | `scripts/run_panel_push_20260920.py`、`scripts/render_panel_push_20260920.py` | 物理前后挡板约束下的持续推杆干扰，抓取并抬升物块 |
| 桌角.mp4 | `scripts/render_compliance_audited.py` 的 isolated corner 分支 | 桌下抓取，接触厚桌子的竖直裙板/桌沿，越过边缘后向桌面放置 |
| 球（被弹开）.mp4 | `scripts/run_primitive_teacher_v7_20260917.py`、`scripts/primitive_contact_scene_v7_20260917.py` | 自由球撞击机器人并离开，机器人继续抓取抬升 |

标题、布局、原场景代码与保留 recipe 对应，但旧视频的完整运行元数据已不可得；不声称逐参数、逐轨迹精确复现旧视频。杆采用 `configs/workstation_source_demo.json` 中 raised_hand_rim 几何，关闭额外 workstation 家具以匹配参考视频；球采用 `configs/ball_source_demo.json`。全部使用新仿真结果，未拼接旧视频。

杆：24 s，seed 800，名义速度 0.08 m/s，12 N 推杆命令、行程 0.18 m、持续保持（推杆命令力不等于瞬时接触力）。球：30 s，seed 800，名义速度 0.07 m/s，质量 0.5 kg、速度 2.4 m/s、半径 0.06 m、9 mm 接触壳层，approach 阶段延迟 0.42 s。角：13 s，原 isolated-corner seed 20264031。实际配置/argv/MJB/hash 保存在每场景目录。

## 最新 teacher 的实际接入

选用新增 30 条示范使用的 `teacher_lhs_0`，来自 `outputs/teacher_student_15h_20261012_v3/TEACHER_CHOICE.json`。配置 SHA256：`352d6d75662aecceb2777aaa2ac5d8e3b0b576a54635930fca8d081cc879c787`。`ParameterTeacher`、`StableReadoutTeacher`、`SixDVirtualDynamics` 三个类与采集冻结源码 AST 一致。

保留原场景构造器、名义任务 supervisor 和执行器接口；在 env.step 边界舍弃旧控制器输出，用 canonical48 和独立因果关节负载观测器生成新 teacher 动作。actor 无真实接触力/几何/时钟特权输入；原任务 supervisor 仍使用模拟状态决定抓取/放置，不能把整个系统称为无特权闭环。

角场景以旧 `paper_mpc` 名义分支进入，目的是关闭旧 VMC 专属手工补偿与增益调度；原 `legacy.json` 仍记录这个分支标签，实际动作控制器由新 execution/保存动作/独立 replay 证明，不能按 legacy 标签误认为此次运行了 MPC。角场景保留原线速度让位上限 0.16 m/s，杆/球为 0.32 m/s，因此这不是三场景统一接口的正式公平评测，也不是用户原视频控制器的性能复现。

## 本次真实结果

| 场景 | 物理时长 / 动作数 / 子步数 | 结果与限制 |
|---|---|---|
| 厚桌角 | 13 s / 325 / 260000 | 抓取抬升完成，5.36555 s 首次接触侧板；最终未释放、未完成放置。机器人与桌面最大穿透 1.065 mm，保留失败 |
| 带挡板推杆 | 24 s / 600 / 480000 | 原场景 `grasp_lift_success=true`；杆与机器人累计接触 2.57545 s，最大穿透 0.180 mm；也接触了后挡板 |
| 自由球 | 30 s / 750 / 600000 | 0.5062 s 首次撞击，原场景 `grasp_lift_success=false`；不能因为球被弹开就判任务成功 |

角场景的旧 `task_success=true` 只说明其内部抓取/抬升子任务，不代表放置成功；最终 `scenario_success=false`。目标底部距桌面约 4.303 mm，支撑稳定条件未满足，release gate 未打开。旧失败原文为 `placement_failure` 和 `physics_step_table_penetration_or_missing_audit`。

上述不是正式 office-v7 的 Task/Strict 结果，不据此覆盖180回合表。独立子步观测的最大接触力（角侧板/杆/球）约 234.42/338.28/180.75 N，亦不宣称全部舒适或安全。球旧接触统计仅累计力大于 0.05 N 的接触 19.5 ms；新增观测累计接触对存在 31.8 ms，两种口径分别保留，不混用。

三条保存动作与公共 filter 独立重放均精确相等。每条视频使用对应保存 MJB 与 qpos/qvel/ctrl/mocap 状态，不重新生成行为。MP4 为 1280×540、25 fps、原速；GIF 为 960×405、12.5 fps。所有 GIF 全帧、MP4 完整解码通过，关键帧已目视检查。杆右视图仅渲染时将挡板透明化，碰撞仍保留。

## 失败收据与修复

最初 v1 新校验器在遍历 filter 记录时仍经过采集钩子，导致校验输出再次追加进被遍历列表。角完成真实325步后在校验阶段报错，保存了325条物理记录和326条额外校验记录；独立脚本核对后缀来源，并对真实325条执行 actor/filter 精确重放通过。原失败状态不改写，另存 `INDEPENDENT_AUDIT.json`。

v1 杆完成600步后因同一校验循环增长触发3 GiB OOM，未保存完整新actor来源证据，不作为交付结果。保留原脚本、OOM失败收据与旧轨迹。修复为校验直接调用未插桩的 filter，再在 v2 独立目录串行重跑杆和球；两条均完整退出，独立审计通过。没有为了改变任务失败而调参重试。

## 文件与运行

交付路径：角为 `outputs/video_reference_vmc_20261028_v1/corner/`；杆/球为 `outputs/video_reference_vmc_20261028_v2/{rod,ball}/`。各自 `media/new30_vmc.mp4`、`media/new30_vmc.gif` 为本次新媒体。旧 v1 杆明确排除。

新入口：`tools/run_video_reference_vmc_20261028.py`（`--output 新目录`，可选 `--scenes corner rod ball`）；渲染：`tools/render_video_reference_vmc_20261028.py --scene 已完成场景目录 --ffmpeg 可执行文件`；独立审计：`tools/audit_video_reference_vmc_20261028.py 已完成场景目录`。先检查同目录 execution/运行进程，勿重复启动。

计算主机 airpig，解释器 `/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python`，MuJoCo 3.11.0，dt=5e-5，单模拟器/单线程、MemoryMax=3 GiB、swap=0。未安装新包或改变冻结环境。

已核验归档：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/video_reference_vmc_20261028_delivery/SCENES.tar.gz`。190468315 字节，SHA256 `2adb6691a0bb68331d7d17e12cbf0edfc3fdda36a86a967e9b6a64e8c74bc737`。包内84个文件与本地逐大小/hash一致，传输暂存与最终位置的包大小/hash一致；包含三段媒体/轨迹/MJB/源码、原失败v1和新脚本。服务器只存储/hash，没有仿真。见 [ARCHIVE.json](evidence/video_reference_vmc_20261028/ARCHIVE.json)。

开工 main `11af52479045acef7aba9114d12175704c444c46`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；收工发现 main 前进至 `0e59c278e96c852f1a46ae49c3574fc99c919a7d`，已读取新日志/AGENTS 并安全快进。更新为其他 agent 的 RL 进展，无本次场景源代码变更。运行时新脚本是本地未提交 overlay，其真实hash已记录，不冒充干净历史commit。
