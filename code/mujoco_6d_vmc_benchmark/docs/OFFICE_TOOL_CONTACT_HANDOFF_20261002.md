# 当前综合环境与三机位交接（2026-10-02）

用户认可的是 **office-tool-contact-v5 的交互展示**，并要求共享当前环境和三角度拍摄，
后续再优化 VMC 数据采集与 ESN 学习。本次只整理交接、消除复跑入口的本机路径依赖，
没有新训练、仿真或环境参数修改。视觉认可不代表任务/安全通过。

开工已查询远端并读取日志：main `03809257e72b612bdc760ada3113e8ddba32c098`，
baseline `e564e09a691293802ec76c237d717b202d592e85`。baseline 的四特化场景运行独立，
本交接不合并、不覆盖其分支。当前环境不可与旧 office-v5/combined-v4 分数混算。

## 1. 可信来源与共享地址

主机均为 `arm1@192.168.31.70`，以下为该主机上的绝对路径：

- 已核验的原物理实现源码：
  `/home/arm1/sii_shared/SII_compliance/source/03809257e72b612bdc760ada3113e8ddba32c098/`。
  本次新增的可移植入口在 GitHub main；收工源码快照按新完整 commit SHA 存入同一 `source/`。
- 原始证据根目录：
  `/home/arm1/sii_shared/SII_compliance/runs/main/tool_contact_review_20261002/evidence/`。
  142 项文件已核验；`archive_manifest.json` SHA256：
  `936b6af1988b65bfce16dcf6c4fa44b2b1bf8460913b59aff2accb6496c6221f`。
- 完整回合：证据根下 `tool_contact_20261002/v5_esn_full/`。
  包含 `esn_combined_v4.json/.npz/.mjb/.plan.json`、`esn_temporal.npz`、
  `TRAINING_COMPLETE.json`、`execution.json`、`AUDIT.json`、
  `source_overlay.tar.gz`、物理子步指标及 `media/`。
- 高密度接触诊断：证据根下 `tool_contact_20261002/v5_contact_audit/`；
  球零入射速度对照：`tool_contact_20261002/v5_ball_off/`。旧候选失败也在原归档中。
- 完整机器人资产：
  `/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_runtime_inputs_complete_20260930/menagerie/`，
  包含 `franka_fr3/fr3.xml`、`franka_emika_panda/panda.xml` 与配套 mesh。
  资产核验说明见 [资产复现报告](TEACHER_BANK_ASSET_REPRODUCTION_CORRECTION_20260930.md)。

实际计算在 airpig 本机，Python 3.11 / MuJoCo **3.11.0**。历史 execution 中本机路径是
真实来源，不能改写为服务器执行。新 agent 应下载到自己的缓存再本地计算；服务器路径
不能直接当成本机路径。大型轨迹、模型、视频不在 Git clone 中。

| 关键文件 | SHA256 |
|---|---|
| `configs/office_tool_contact_v5_20261002.json` | `850c650d9e648c480668e349502afa7180f85ba5840bc15890929ea5aaeb3467` |
| `v5_esn_full/esn_temporal.npz` | `9f4b5a8168142595873ff1c8fdcaa3b2186b7a1d1edab916d2bbd38fe5988023` |
| `v5_esn_full/esn_combined_v4.mjb` | `b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1` |
| `v5_esn_full/esn_combined_v4.npz` | `1dae96be381ca326ebe5be22cebb4b1c4aef0d464c620b1249f899350a577040` |
| `v5_esn_full/media/replay_threeview.mp4` | `4534da6526cc437ccaa7441f35000995c153e1f278ea0e85c245f5f43cba5032` |

配置 JSON 只是环境覆盖项，不是完整场景。完整设置以回合 JSON 的 `arguments`、
execution/source overlay、实际 MJB 为准。不要根据文件名中的 `combined_v4` 误判版本。
保存的独立 XML 也不等价于原初始化流程，可能丢失默认质量/碰撞掩码/精度；
重渲染直接用 MJB，重仿真必须用相同资产和初始化，并核对期望 MJB hash。

## 2. MuJoCo 场景搭建

入口为 `tools/run_tool_contact_20261002.py`，公共仿真在
`scripts/validate_office_apparatus_v5_20260917.py`；配置为上述 v5 JSON。
坐标为世界坐标（m），box 尺寸均为半长；下表描述当前选定场景，不用于重新猜造 XML。

| 部件 | 位置与尺寸/参数 |
|---|---|
| 普通桌面 | 中心 `[.58,0,.375]`，半长 `[.28,.38,.025]`，表面 z=.400 |
| 地板 | z=-.35 |
| 抬高的目标桌角 `office_v5_corner_top` | 中心 `[.650,-.100,.500]`，半长 `[.080,.250,.020]`，表面 z=.520 |
| 目标物块中心 | `[.690,-.310,.545]`，靠人手一侧 |
| 原局部厚桌边 `office_v5_corner_face` | 中心 `[.480,-.150,.520]`，半长 `[.012,.010,.020]` |
| 原柱子 `office_v5_pillar` | 中心 `[.619,-.270,.750]`，半径 .004，半高 .010；底座中心 `[.619,-.270,.407]`，半径 .055，半高 .007 |
| 未建图凸边 `office_v5_unexpected_edge` | 中心 `[.610,-.250,.555]`，半长 `[.010,.045,.035]`，底 .520 / 顶 .590 |
| 凸边接触材质 | friction `.6 .01 .001`；solref `.002 1`；solimp `.99 .999 .0001 .5 2` |
| 球 | 中心 `[.535,-.43,.61]`，半径 .060，质量 1.0 kg；2 s 沿 +y 发射，1.7 m/s |
| 棍轨道 | 中心 `[.77,-.12,.64]`，slide 轴 `[-1,0,0]` |
| 棍胶囊 | 轨道局部端点 `[.10,0,0]` 到 `[-.045,0,0]`，半径 .014，质量 .65 kg |
| 棍驱动/材质 | 行程 .235 m，力上限 14 N，solref `.001 1` |
| 人手驱动 | 行程 .2 m，力上限 80 N；保留公共场景的手部几何与关节 |

球使用真实质量/冲量，没有放大机器人动画。棍缩短、抬高、反向布置以推掌部，
不追踪末端、不依据接触结果提前撤回。凸边从 reset 起物理存在，但不在规划器先验地图中，
不是中途瞬移障碍。纯本体 actor 不接收凸边、球或其他环境状态。

| 事件 | 固定时序（s） |
|---|---|
| 球发射 | 2.0 |
| 人手推进/保持/撤回 | 3–5 / 5–8 / 8–10 |
| 棍推进/保持/撤回 | 12–13.5 / 13.5–23.5 / 23.5–25.5 |

时序名是 `tool-contact-r12-h10-v1`；不要误用保持期仅 6 s 的旧 `sequential-r12-v1`。
本回合 seed `2026091751`、variant 0、55 s、`dt=1e-4`（开发），events=all、task=pick_place，
并启用 `combined_thick_corner_pillar_v4`、`planned_hand_corner`、`unexpected_edge`、
`allow_lateral_rejoin`。正式 `dt=5e-5` 尚未完成。

## 3. 公共规划、控制与任务判定

所有方法共享先验地图 A* 路线和 IK 姿态搜索（最终倾角 -35°）、参考跟随、释放逻辑。
公共 rejoin v2 允许非终点路点的前向平面越过且垂直误差 <80 mm，终点到达约束仍保留。
不让 ESN 独占更好规划或改变路径进度；新旧 rejoin 结果分开。

当前为旧权重的纯 ESN，canonical48D 输入/action7、储备池宽度 128，没有 VMC 混合。
actor 不加入接触真值、球状态、事件时刻、任务阶段、视觉或距离。
执行器幅值/变化率和公共动作处理沿用保存参数；不同算法对比必须使用同一版本。

任务成功看完整回合的抬起和最终释放稳定放置：物块抬起 >.1 m；最后 .5 s 松手
（两指总开度 >.075 m、无机器人支撑接触）、由目标桌角支撑，XY误差 <.025 m、
Z误差 <.015 m、物块线速 <.015 m/s、角速 <.15 rad/s。strict 额外要求物理有效、
外部最大穿透 ≤.2 mm，并核对新凸边/物块穿透 ≤.2 mm。
接触覆盖另报诊断，不重新塞回旧版“必须碰全障碍”的主任务门槛；旧字段保留供审计。

## 4. 三角度拍摄：必须指定 contact-closeup

当前用户观看的完整视频是共享 `v5_esn_full/media/replay_threeview.mp4`：
55 s、1375 帧、25 fps、1920×560、原速。脚本
`tools/render_office_threeview_20260929.py` 的 **`--contact-closeup` 必须保留**；
不传该参数会用旧的 end-effector / pillar-corner 远景，不是本次认可的机位。

| 从左到右 | lookat（世界坐标 m） | distance（m） | azimuth（°） | elevation（°） |
|---|---|---|---|---|
| overview | `[.64,-.02,.45]` | 2.50 | 135 | -20 |
| palm impact | `[.54,-.19,.54]` | .72 | 110 | -15 |
| palm / rod | `[.52,-.17,.62]` | .80 | 75 | -15 |

每幅 640×480，上方 80 px 为标签。headlight ambient=.65、diffuse=.8；EGL 后端，
DejaVuSans 18。绿色目标标记只供渲染，无碰撞，也不进入 actor。
脚本从归档 MJB 和 qpos/qvel/ctrl/mocap 恢复状态，仅 `mj_forward`，不重跑物理。
脚本验证 MJB hash，并将输入/输出 hash 写入媒体 manifest；下载的 NPZ 还应与上表核对。
标题中的通用 office-v5 字样不替代 fixture 版本，阅读 v5 配置及 execution。

完整回合重渲染命令（先将共享 full-run 下载到本地，以下 CACHE/OUT/PY 为本机绝对路径）：

```bash
# 工作目录：Git checkout/code/mujoco_6d_vmc_benchmark
# PY 指向包含 MuJoCo 3.11.0、numpy、imageio_ffmpeg、Pillow 的 Python。
# CACHE 指向下载后的 v5_esn_full；OUT 是不存在的新输出目录。
MUJOCO_GL=egl OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  "$PY" tools/render_office_threeview_20260929.py \
  --rollout "$CACHE/esn_combined_v4" --output "$OUT" \
  --label 'ESN | tool-contact-v5 | 1x | development' \
  --stride 1 --fps 25 --gif-stride 5 --contact-closeup
```

完整 trace 为 25 Hz，stride1/fps25 才是原速；GIF 每 5 帧取一帧，为 5 fps。
重渲染 MJB 不需要外部 mesh；但需匹配 MuJoCo 版本和 EGL/字体依赖。
不要覆盖共享原媒体。完整原视频 SHA 如上；新编码受平台影响可能有不同 MP4 hash，
应记录自己使用的模型/轨迹/脚本 hash，不声称新文件与原文件字节一致。

接触特写在共享 `v5_contact_audit/clip_ball/media/` 和 `clip_rod/media/`：

- 球：200 Hz 状态、stride1/fps50，物理 1.9001–2.6951 s，160 帧/3.2 s，**0.25倍慢放**。
- 棍：200 Hz 状态、stride4/fps50，物理 12.5001–23.3951 s，546 帧/10.92 s，**原速**。

特写来自与完整轨迹前28秒逐元素一致的补日志回合。其覆盖文字只表示28秒窗口的结果，
不能用来声称55秒安全通过。可用 `tools/render_tool_contact_clips_20261002.py --run`
配合新建的诊断缓存目录生成；已存在的 clip 目录会拒绝覆盖。

## 5. 获取与复跑（本次不启动）

在本地新缓存目录下载归档与资产，例如先设置 CACHE 为自己选择的绝对路径：

```bash
mkdir -p "$CACHE"
rsync -a arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/tool_contact_review_20261002/evidence/tool_contact_20261002/v5_esn_full/ "$CACHE/"
sha256sum "$CACHE/esn_temporal.npz" "$CACHE/esn_combined_v4.mjb" "$CACHE/esn_combined_v4.npz" "$CACHE/media/replay_threeview.mp4"
# 如需新仿真：另下载完整 menagerie，设置 MUJOCO_MENAGERIE_PATH 为其本地根目录。
```

新 runner 的 `--reference-dir` 接受共享完整回合，校验 full-horizon 与 checkpoint hash，
要求 TRAINING_COMPLETE；拒绝把 ball-off/短探针当完整参考。默认仍兼容旧本机入口。
已经核对共享参考与原 p010 参考的权重完全相同，所有非覆盖 evaluator 参数一致。
以下示例显式限制内存/线程，UNIT 为唯一服务名、OUT 为不存在的新回合目录：

```bash
systemd-run --user --unit="$UNIT" --working-directory="$PWD" \
  -p MemoryMax=3G -p MemorySwapMax=0 -- \
  env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MUJOCO_GL=egl \
  MUJOCO_MENAGERIE_PATH="$ASSETS" \
  "$PY" tools/run_tool_contact_20261002.py \
  --method esn --reference-dir "$CACHE" \
  --fixture configs/office_tool_contact_v5_20261002.json \
  --expected-mjb b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1 \
  --output "$OUT"
```

先检查现有服务、内存和 checkpoint；本机单模拟器/1线程/3 GiB，不重复启动。
生成新的 execution/source/config/checkpoint/model/plan/trace hash，保留失败。
不要传 `--clear`、`--ball-off` 或 `--probe` 后把结果称为完整目标场景。
MLP 必须提供其自己的完整 summary/checkpoint/train record，不能拿 ESN 文件代替。
`--method nominal` 使用同一公共执行、零学习动作；不得当作 VMC 或导纳 baseline。
baseline 接入各自策略时保持公共环境/动作约束/路径与判定一致，先核对 MJB 和参数。

## 6. 当前结果和后续边界

| 项目 | 当前证据 |
|---|---|
| 球碰撞 | 同模型零发射对照，2–2.7 s 额外手部偏移最大 13.845 mm |
| 棍碰撞对象 | 仅 hand_collision，不碰物块或人手 |
| 棍伸出时脱离 | 15.1201–19.1801 s，实际行程 >.225 m，所有物理子步掌部接触力 ≤.05 N |
| 仍有的问题 | 之后回碰/抖动；最长连续受力接触仅 .1061 s，不是平滑永久滑脱 |
| 前28秒最大外穿透 | .111485 mm |
| 完整55秒任务 / strict | **false / false**，终态 load_transfer |
| 全程 RMSE / 峰值广义执行器力矩 / 手部峰值线速 | **49.428 mm / 45.880 Nm / .370425 m/s** |
| 全程最大外穿透 | **.653202 mm**，后段原 pillar/link7，超过 .2 mm |
| 动作/储备池重放 | 误差0；额外遥测与原28秒前缀状态/动作逐元素一致 |

不能用 `mj_geomDistance` 的 mesh 凸包距离证明掌部已无接触；该距离与实际接触不一致，
本次脱离结论使用逐子步受力与真实行程。运动还含任务本身的推进，不能全部归功于ESN柔顺。
失败候选v1–v4均保留，详见 [接触修正与全部失败](TOOL_CONTACT_REPAIR_20261002.md)。

已完成：环境、时序、公共路线/判定、纯本体边界、三机位、原始证据及可移植入口交接。
运行中：本轮未启动仿真/训练，不干预 baseline 的独立作业。
未完成：平滑接触恢复、完整放置/安全通过、正式步长与跨条件验证、VMC新数据采集和ESN新学习。
下一步用户恢复研究后，在本环境版本上研究 teacher 与纯ESN；不要为了成功率再移动障碍、
放宽 gate、引入接触真值或把开发视频当正式/真实机器人成功。
