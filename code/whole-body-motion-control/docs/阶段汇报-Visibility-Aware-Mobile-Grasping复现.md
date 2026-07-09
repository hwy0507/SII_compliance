# Visibility-Aware Mobile Grasping 论文机制与复现阶段汇报

汇报日期：2026-07-02  
项目路径：`/home/hwy21/桌面/whole_body_manipulation/Visibility-Awared-Mobile-Grasping`  
论文 PDF：`/home/hwy21/桌面/whole_body_manipulation/2605.02487.pdf`  
论文机制详解笔记：`/home/hwy21/桌面/whole_body_manipulation/Visibility-Aware-Mobile-Grasping-论文机制详解.md`

---

## 1. 论文要解决的问题

论文关注的是 **动态、遮挡、视野有限的室内环境中的移动抓取**。目标不是让固定机械臂在桌面上抓东西，而是让一个移动机械臂机器人在房间里移动、观察、避障，并最终抓取目标物体。

核心挑战包括：

- 机器人只能通过头部 RGB-D 相机看到局部环境，不能假设完整地图已知。
- 抓取目标、移动路径、机械臂运动空间都可能被遮挡。
- 动态障碍物可能在机器人移动或抓取过程中进入路径。
- 传统“先导航到目标附近，再机械臂抓取”的解耦方法容易出现到达后不可抓、观察角度不好、路径被新障碍物破坏等问题。

论文核心思想是：**将移动、抓取、观察和重规划放在一个闭环系统里联合考虑**，也就是 visibility-aware mobile grasping。

---

## 2. 系统架构理解

论文使用的平台主要是 **Fetch mobile manipulator**：可移动底盘、可升降 torso、7 自由度机械臂、平行夹爪和头部 RGB-D 相机。它不是一个“单独的抓取网络”，而是一套闭环机器人系统，把目标观察、局部建图、抓取候选生成、全身运动规划、执行控制和动态重规划连在一起。

传统移动抓取常见流程是：

```text
先导航到目标附近 -> 停下底盘 -> 机械臂单独抓取
```

这篇论文的架构更接近：

```text
边移动 -> 边观察 -> 边更新地图 -> 边判断是否还能安全抓取 -> 必要时重新规划
```

也就是说，它真正解决的是“机器人在动态、遮挡、视野有限的场景中如何持续决策”的问题，而不是只解决“某一帧图像里怎么生成抓取姿态”。

系统状态可以概括为：

```text
b_t = (q_t, M_t, g_t)
```

其中：

- `q_t`：机器人全身状态。对 Fetch 来说约等于 `[x, y, theta, torso, 7 arm joints]`，也就是底盘位置、底盘朝向、躯干高度和机械臂关节。
- `M_t`：机器人当前根据 RGB-D 观测维护的局部 3D 地图。它不是完整真实地图，而是“机器人目前看见并相信的世界”。
- `g_t`：当前子目标，可以是最终抓取姿态、预抓取姿态，也可以只是一个更好的观察位姿。

整体闭环数据流可以理解为：

```text
目标位置 / 目标点云
  -> 高层子目标生成 pi_g
  -> 全身运动规划 pi_r
  -> MPC / 速度控制执行
  -> 主动感知策略 pi_v 控制头部相机
  -> RGB-D 更新局部地图 M_t
  -> 检查轨迹和抓取是否仍安全
  -> 如果环境变化或子目标失败，则重新生成目标并重规划
```

### 2.1 高层子目标策略：不是盲目导航，而是逐级降低难度

论文最重要的高层逻辑是：

```text
Grasp Goal -> Pre-grasp Goal -> Observe Goal -> Failure
```

含义是：

- **Grasp Goal**：如果当前位置已经能看到目标、机械臂能到、轨迹无碰撞，就直接抓。
- **Pre-grasp Goal**：如果当前不适合直接抓，就采样一个更适合抓取的底盘位置、torso 高度和机械臂预抓取姿态。
- **Observe Goal**：如果抓取和预抓取都不可行，说明信息可能不够，就先移动到一个更好的观察角度。
- **Failure**：如果观察、预抓取、抓取都无法找到可行解，才判定失败。

这套设计的意义是：机器人不是死板地“导航到目标附近再抓”，而是会判断“现在该抓、该靠近、还是该换角度看”。这也是论文相对传统 navigation-and-manipulation baseline 的重要区别。

更具体地说：

- 直接抓取失败，可能不是目标不能抓，而是当前底盘/躯干/手臂姿态不适合。
- 预抓取失败，可能不是任务失败，而是当前视角信息不足。
- 观察失败后才真正说明系统没有找到继续推进任务的有效方式。

因此，高层策略把一个困难的大问题拆成了三个难度递增、信息需求不同的子问题。

### 2.2 抓取候选与可达性过滤：学习负责提出候选，几何负责保证可执行

直接抓取阶段大致流程是：

```text
RGB-D / 目标点云
  -> Contact-GraspNet 生成 6-DoF 抓取候选
  -> capability map 快速过滤明显够不到的姿态
  -> IK 求解
  -> 碰撞检测
  -> 选择可执行 grasp
```

这里的关键点是：Contact-GraspNet 只负责提出“视觉上可能好抓”的候选，系统还必须用机器人自身的 IK、碰撞检测和能力地图判断“机器人实际能不能抓”。

也就是说，这篇论文不是端到端学习系统，而是 **model-based planning + learned grasp proposal**：

- 学习模块负责从点云中生成抓取姿态；
- capability map 负责快速判断这个姿态大概是否在机械臂工作空间内；
- IK 负责给出具体关节角；
- collision checker 负责判断是否会撞环境或机器人自己；
- planner 负责生成从当前状态到目标状态的可执行轨迹。

这也是当前复现失败集中在 `perception_failure` 时需要重点排查的原因：只要目标 mask、目标点云或 GraspNet 候选输出不稳定，后面的 IK 和规划就没有可靠输入。

### 2.3 Pre-grasp 生成：同时考虑底盘、torso、机械臂和视野

如果直接抓取不可行，系统会生成一个预抓取目标。它不是只采样一个底盘位置，而是联合考虑：

```text
base pose q_b
torso height h
end-effector pose T_ee
```

这一步要同时满足：

- 底盘位置在 2D SDF / costmap 中安全；
- torso 高度让机械臂有更好的可达空间；
- 末端抓取姿态附近有 IK 解；
- 机械臂和底盘运动不碰撞；
- 机器人移动到该位置后仍能看到目标或不会严重遮挡目标。

这点很重要，因为移动抓取失败很多时候不是“离目标太远”，而是“站的位置虽然近，但机械臂姿态、桌面障碍、视野和碰撞约束不协调”。论文把预抓取位姿看成 whole-body 配置问题，而不是简单的导航目标点问题。

### 2.4 主动感知：论文最有创新性的部分之一

论文题目里的 **Visibility-Aware** 主要体现在主动感知策略上。它不是简单“相机一直看目标”，而是根据当前阶段动态决定看哪里：

- 还没有可靠抓取/轨迹时，优先看目标，补充目标点云。
- 正在执行轨迹时，优先看机器人接下来要经过的 **swept volume**，也就是底盘、torso、机械臂运动中会扫过的空间。
- 在动态场景中，速度更快的部位附近风险更高，因此 gaze 会偏向高速度、高碰撞风险区域。

这里最创新的点在于：**机器人不只是为了抓取看目标，也为了安全执行看未来轨迹的风险区域。**

可以把相机的注意力理解成有限资源：

```text
相机视野有限
  -> 不能同时看目标、底盘前方、机械臂侧面和所有障碍物
  -> 系统必须判断当前哪片空间最值得看
```

论文把这个问题和运动轨迹绑定起来：当前轨迹会让机器人身体和机械臂扫过一片 3D 空间，这片空间就是 swept volume。如果 swept volume 里突然出现障碍物，机器人就会撞。因此执行阶段最应该观察的不是“画面中心”或“目标物体”，而是“未来一小段时间内机器人要经过的高风险区域”。

进一步地，论文加入了 **velocity-aware gaze**：运动越快的部位，风险越高，因为留给机器人反应和重规划的时间更短。所以相机应该更关注高速运动部件附近的空间。这一点比普通的“看路径前方”更细，因为它把机器人各个部件的运动速度也纳入视野分配。

这部分可以认为是论文最有创新性的贡献之一：

```text
传统主动感知：为了看清目标
本文主动感知：为了同时看清目标和未来碰撞风险
```

### 2.5 动态地图：不是一次建图，而是持续更新可见/不可见空间

地图更新用 RGB-D 点云加 ray casting：

- 从深度图生成点云；
- 去掉机器人自身点云和地面点；
- 新观测到的障碍加入局部地图；
- 通过 ray casting 删除已经确认变为空的旧障碍；
- 对仍然被遮挡、没有看见的区域保持保守。

这让系统可以处理两类动态变化：

- **新障碍出现**：比如有人或物体突然进入轨迹附近，地图会加入新障碍并触发重规划。
- **旧障碍消失**：比如之前挡路的物体被移走，ray casting 会帮助系统确认该区域重新变为空。

因此，`M_t` 不是静态地图，而是随机器人视角和环境变化不断更新的局部信念。

### 2.6 全身规划与执行闭环：移动、躯干和手臂联合规划

底层规划是 whole-body planning，不是“底盘先走、机械臂后动”的简单拆分。系统联合考虑：

- 底盘位姿；
- torso 高度；
- 7 轴机械臂关节；
- 抓取姿态可达性；
- 当前局部地图中的碰撞约束。

实现上，底盘规划用 Hybrid A* / Reeds-Shepp 类方法提供引导，高维全身规划用 RRT-Connect / VAMP 类采样规划，再经过 shortcutting、平滑和插值。这样做的原因是 Fetch 的状态维度高，如果完全暴力搜索会很慢；而只规划底盘又会忽略机械臂可达性和碰撞。

执行阶段使用 MPC/速度控制跟踪轨迹，并在地图更新后检查当前轨迹是否仍安全。如果发现新障碍或当前轨迹不再可行，就进入 receding-horizon 式重规划：

```text
执行一小段
  -> 观察
  -> 更新地图
  -> 检查未来轨迹
  -> 必要时重规划
```

这也是它能应对动态环境的原因：系统并不假设初始规划永远正确。

### 2.7 论文最核心的创新点总结

这篇论文的创新点不是单独提出一个新的神经网络，而是提出了一套面向动态未知环境的移动抓取系统架构。最值得汇报的创新点有四个：

1. **Visibility-aware active perception**：相机视角不是固定看目标，而是在目标、未来 swept volume 和高速度风险区域之间动态分配，解决“视野有限但安全执行需要看很多地方”的矛盾。
2. **Velocity-aware gaze weighting**：不仅看轨迹会经过哪里，还考虑机器人部件运动速度；速度越快、风险越高的区域越需要被观察，从而降低动态障碍物带来的碰撞风险。
3. **层级子目标机制**：用 `Grasp -> Pre-grasp -> Observe -> Failure` 替代传统“导航到目标点再抓取”，让机器人能根据当前可达性和观测质量选择下一步动作。
4. **闭环 whole-body mobile manipulation**：底盘、torso 和机械臂联合规划，并在执行过程中通过地图更新持续检查和重规划，把移动、抓取和避障放进同一个闭环。

一句话总结架构：**这篇论文最有价值的地方，是把“看哪里”和“怎么移动/怎么抓”绑定起来，让机器人在动态、遮挡、局部可见的环境中边看边规划、边执行边修正。**

---

## 3. 当前项目与论文关系

当前仓库：

```text
Visibility-Awared-Mobile-Grasping
```

对应论文代码主体，包含：

- `grasp_anywhere/`：主要 Python 包；
- `experiments/run_maniskill_benchmark.py`：ManiSkill benchmark 入口；
- `grasp_anywhere/configs/maniskill_fetch.yaml`：论文主方法仿真配置；
- `third_party/vamp/`：全身运动规划相关依赖；
- `third_party/perception_services/`：OWL-ViT、SAM、Contact-GraspNet 服务；
- `resources/grasp_benchmark.json`：仿真 benchmark 任务集。

补充阅读的 Google Doc 已保存到：

```text
docs/Whole-Body-Motion-Planning-and-Mobile-Grasping-Resource-Map.txt
docs/Whole-Body-Motion-Planning-and-Mobile-Grasping-Resource-Map.docx
```

该文档是资源地图，不是论文正文。它说明当前项目属于 larger stack 中的 mobile grasping 部分，底层规划依赖 Fetch VAMP，仿真主要依赖 ManiSkill + ReplicaCAD/YCB。

---

## 4. 目前复现环境状态

已完成：

- 项目已克隆并重命名到无空格路径：

```text
/home/hwy21/桌面/whole_body_manipulation/Visibility-Awared-Mobile-Grasping
```

- Conda 环境已建立：

```text
mobile_grasping_in_dynamic
```

- ROS1 Noetic / ROS2 Foxy 可共存，终端启动时可选择环境。
- 项目已重新 `pip install -e .` 到新路径。
- IKFast 已编译。
- VAMP 本地依赖可导入。
- ManiSkill 的 ReplicaCAD 和 YCB 资源已下载。
- 预计算资源已放入 `resources/`：

```text
capability_map.pkl
inverse_reachability_map.pkl
reachability_map.pkl
torso_map.pkl
```

- `resources/benchmark/canonical_maps/scene_0.ply` 到 `scene_19.ply` 已全部生成，共 20 个。
- `outputs/benchmark_viz/` 已生成部分场景俯视图，例如：

```text
outputs/benchmark_viz/scene_0_rt.png
outputs/benchmark_viz/scene_5_rt.png
```

---

## 5. 感知服务配置情况

项目需要外部 HTTP 服务：

```text
GraspNet / Contact-GraspNet: 4003
SAM:                         4001
OWL-ViT:                     默认 4000
```

实际配置调整：

- NoMachine 占用了 `4000`，不能杀 `nxnode.bin`，否则远程桌面会白屏。
- 因此将 OWL-ViT 端口改为 `4010`，并同步修改：

```yaml
owl_url: "http://localhost:4010"
```

- Contact-GraspNet 默认 checkpoint `scene_test_2048_bs3_hor_sigma_001` 不完整，已改用本地完整 checkpoint：

```bash
export CONTACT_GRASPNET_CHECKPOINT_DIR="/home/hwy21/桌面/whole_body_manipulation/Visibility-Awared-Mobile-Grasping/third_party/perception_services/third_party/contact_graspnet/checkpoints/scene_2048_bs3_rad2_32"
```

当前实际跑 benchmark 时，为避免 6GB 显存被 SAM/OWL 占满，主要保留：

```text
Contact-GraspNet 4003
```

原因：ManiSkill 仿真中已有 segmentation 信息，当前 benchmark 主要需要 grasp prediction 服务。

---

## 6. 遇到的问题与已解决情况

| 问题 | 原因 | 处理 |
|---|---|---|
| Contact-GraspNet 编译失败 | 原路径 `whole body manipulation` 含空格，老脚本未正确引用路径 | 根目录改为 `whole_body_manipulation` |
| `libcudart.so.10.1` / CUDA 相关问题 | 旧 `.so` 依赖历史 CUDA | 清理旧编译产物并重新编译 PointNet TF ops |
| HuggingFace 模型下载超时 | 终端未继承代理 | 使用代理或镜像下载 SAM/OWL 模型 |
| OWL-ViT 4000 端口冲突 | NoMachine 占用 4000 | 改为 4010，避免杀远程桌面进程 |
| `move_base_msgs` 缺失 | ROS Noetic 依赖未装 | 安装 `ros-noetic-move-base-msgs` |
| `numpy 2.x` 与 ROS `cv_bridge` 风险 | `pip install -e .` 触发 NumPy 升级 | 固定回 `numpy==1.26.4` |
| `TimeLimitWrapper` 无 `.scene` | ManiSkill/Gymnasium 包装层 API 差异 | 已将代码改为 `env.unwrapped.scene` |
| `cannot create buffer` | SAM/OWL/仿真同时占用显存，RTX 3060 6GB 不够 | benchmark 阶段只保留 GraspNet，释放显存 |
| 初次 benchmark `total_tasks=0` | 缺 `resources/benchmark/canonical_maps/*.ply` | 已生成 20 个 canonical map |

已修改源码：

```text
experiments/run_maniskill_benchmark.py
grasp_anywhere/envs/maniskill/maniskill_env_mpc.py
tools/record_single_task_gif.py
```

新增脚本：

```text
tools/record_single_task_gif.py
```

用途：只运行单个 scene/task，并录制第三视角 GIF，便于做展示动图。

---

## 7. 当前 benchmark 结果

目前 `results/` 下有两个 benchmark 结果文件：

```text
results/ours_static/run_20260701_191700_68f997/benchmark_results.json
results/ours_static/run_20260701_230646_958703/benchmark_results.json
```

其中 `run_20260701_191700_68f997` 虽然创建了结果文件，但 `total_tasks=0`，不能作为有效成功率统计。当前可用于汇报的有效结果是：

最近一次完整写入的结果目录：

```text
results/ours_static/run_20260701_230646_958703/
```

结果文件：

```text
results/ours_static/run_20260701_230646_958703/benchmark_results.json
```

截至写入时间 `2026-07-02 00:52:09`：

```text
已完整写入 scene 数量：2 个，scene_0 和 scene_1
已完整统计任务数：40
成功数：0
失败数：40
碰撞失败：4
感知失败：34
规划失败：2
IK 失败：0
抓取保持成功率：0%
```

因此当前有效成功率为：

```text
0 / 40 = 0.00%
```

如果按论文仿真 benchmark 的完整规模 `20 scenes × 20 objects = 400 tasks` 来看，目前已经完整写入统计的是前 2 个 scene，共 40 个 task，覆盖约：

```text
40 / 400 = 10%
```

需要强调：这个 `0%` 是当前本机复现配置下的阶段性调试结果，不代表论文方法本身的报告性能。论文中完整系统在仿真未知静态环境约为 `68.75%`，动态环境约为 `58.00%`；当前差距主要来自本地工程配置、感知/抓取服务输入输出和代码适配尚未完全对齐。

此外，轨迹目录中已有 42 个 `.npy` 文件：

```text
results/ours_static/run_20260701_230646_958703/trajectories/
```

说明 `scene_2` 前两个任务也曾开始运行并保存轨迹，但未完整写入 JSON 总结果。

初步判断：当前结果说明系统主流程已经跑通到了真实任务执行阶段，但结果尚不能代表论文性能。失败集中在 `perception_failure`，需要进一步定位是 grasp prediction 未返回候选、分割/点云输入不合适，还是当前 checkpoint / 服务配置与论文环境不一致。

---

## 8. 当前复现阶段与官网 Demo 的差距

当前复现阶段可以概括为：

**工程链路已经从环境安装推进到 benchmark 真实任务执行与轨迹保存；但还没有达到官网 demo 中“成功抓取动图”的效果复现阶段。**

已经完成到：

- **环境层**：ROS1 Noetic、Conda 环境、ManiSkill、VAMP、IKFast、YCB/ReplicaCAD 资源和预计算 map 已基本就绪。
- **服务层**：Contact-GraspNet 已可启动并通过 `/healthz`，SAM/OWL 也曾跑通健康检查；但受 6GB 显存限制，benchmark 阶段主要保留 GraspNet。
- **仿真层**：20 个 benchmark canonical maps 已生成，`visualize_benchmark` 可生成静态俯视图。
- **执行层**：`run_maniskill_benchmark.py` 已能进入标准任务循环，完成 `scene_0`、`scene_1` 的 40 个任务统计，并保存轨迹文件。
- **展示工具层**：已新增 `tools/record_single_task_gif.py`，用于后续录制单任务第三视角 GIF。

尚未达到官网 demo 的部分：

- 官网动图展示的是“单个任务成功执行”的可视化结果；当前 benchmark 统计为 `0/40`，还没有筛出稳定成功的可展示任务。
- 当前失败主要是 `perception_failure`，说明还需要重点检查目标点云、分割输入、Contact-GraspNet 返回候选数量、grasp score 和 checkpoint 对齐情况。
- 当前 ManiSkill benchmark 理论上主要依赖仿真提供的目标信息和 segmentation，不一定需要 OWL/SAM 来“找目标”；但由于显存限制，目前没有完整同时开启 SAM、OWL 和高质量仿真渲染录制，这与官网 demo/真实视觉链路仍可能存在差异。
- GIF 录制脚本已经写好，但还需要在一个可成功或至少能完整执行的 task 上验证输出。

因此，离官网 demo 的距离不是“项目还没跑起来”，而是：

```text
已跑通工程执行链路
  -> 还需定位 grasp/perception 失败原因
  -> 找到至少一个稳定成功任务
  -> 用单任务录制脚本生成可展示 GIF
  -> 再扩展到完整 benchmark 指标复现
```

可以向老师概括为：**复现已从安装配置阶段进入算法效果对齐阶段。当前主要缺口是感知/抓取候选质量和成功案例可视化，而不是基础环境未完成。**

---

## 9. 当前可展示内容

可以展示的静态仿真场景：

```text
outputs/benchmark_viz/scene_0_rt.png
outputs/benchmark_viz/scene_5_rt.png
```

可以展示的运行产物：

```text
results/ours_static/run_20260701_230646_958703/benchmark_results.json
results/ours_static/run_20260701_230646_958703/trajectories/*.npy
```

可用于录制单任务动图的命令：

```bash
python tools/record_single_task_gif.py \
  --scene scene_0 \
  --task 0 \
  --output outputs/task_recordings/scene0_task000.gif \
  --fps 8 \
  --width 960 \
  --height 540 \
  --max-seconds 180 \
  --max-attempts 3
```

输出：

```text
outputs/task_recordings/scene0_task000.gif
outputs/task_recordings/scene0_task000.json
outputs/task_recordings/scene0_task000.npy
```

---

## 10. 可以做的 Extension / 后续研究点

结合论文机制和当前复现问题，比较可行的 extension 有以下几类：

1. **抓取可行性感知的 grasp ranking**：不要只按 Contact-GraspNet 的几何分数排序，而是综合 IK 可行性、碰撞 clearance、机械臂 manipulability、底盘移动代价和历史失败记录，优先选择“机器人真的能抓”的候选。
2. **动态障碍物预测**：当前系统偏 reactive，即看到障碍物后重规划；可以对动态点云聚类、跟踪并估计速度，把未来几秒的预测占用加入规划，减少突然出现障碍物时的碰撞风险。
3. **信息增益式主动感知**：现有 gaze 主要看目标和 swept volume；可以进一步考虑 occupancy uncertainty、目标遮挡区域和未来轨迹关键区域，让机器人主动看“最能减少不确定性”的位置。
4. **更稳健的地图表示**：从点云加 ray casting 扩展到 OctoMap、TSDF/ESDF 或带时间衰减的概率 occupancy map，更好地区分“确定有障碍、确定为空、未知、动态物体刚经过”。
5. **失败记忆与自适应采样**：记录哪些 grasp、预抓取方向、观察位姿反复 IK 失败或碰撞，动态降低类似采样的概率，提高后续尝试效率。
6. **轻量化感知服务和缓存机制**：针对 6GB 显存平台，可尝试小模型、离线 segmentation 缓存、按需启动服务，降低 SAM/OWL/GraspNet 与 ManiSkill 同时运行的资源压力。
7. **面向其他移动机械臂迁移**：如果迁移到自有 Roboot 平台，需要补齐 URDF/collision mesh、底盘运动模型、IK、TF、RGB-D 标定、controller 和 reachability/capability map。

其中最贴合当前复现瓶颈的方向是第 1、5、6 点：先把 perception/grasp failure 变成可诊断、可排序、可规避的问题，再考虑更复杂的动态预测和真实机器人迁移。

---

## 11. 目前结论

当前复现已经完成了从环境配置到 benchmark 执行的主体链路：

```text
项目代码 -> ROS/Conda 环境 -> ManiSkill 场景 -> YCB 物体 -> canonical maps -> GraspNet 服务 -> benchmark 任务执行
```

但目前还处在“跑通流程 + 定位差异”的阶段，未达到论文最终指标复现。主要原因包括：

- 当前 benchmark 虽主要依赖 ManiSkill 真值目标信息和 segmentation，但仍需确认 segmentation ID、目标点云和 GraspNet 输入是否正确对齐；
- Contact-GraspNet checkpoint 与论文原始配置可能不完全一致；
- canonical maps 为了先跑通，采用过低采样版本；
- 目前失败主要集中在 perception failure，需要进一步看每个任务的输入点云、分割 mask 和 grasp 服务返回。

因此可以向老师汇报为：

**代码与仿真环境已基本跑通，已能执行标准 benchmark 的具体抓取任务并保存轨迹；当前主要问题从安装配置阶段转移到算法服务输出和实验效果对齐阶段。**

---

## 12. 下一步计划

优先级从高到低：

1. 单独跑 `tools/record_single_task_gif.py`，生成可视化 GIF，直观看失败发生在观察、规划还是抓取阶段。
2. 对 `scene_0` 中失败任务逐个检查 `benchmark_results.json` 的 failure reason。
3. 打印/保存 GraspNet 返回的 grasp 数量和 score，判断 `perception_failure` 是否来自 grasp 服务无候选。
4. 尝试重新启用 SAM/OWL，或确认仿真 segmentation 是否已经足够，无需 SAM。
5. 用更高质量 canonical maps 重新跑少量任务，比较是否影响规划与碰撞结果。
6. 跑 baseline 配置，例如 `nav_manip`、`closed_loop`，验证不同 scheduler 的表现差异。
7. 若要完整复现论文表格，需要长时间跑完整 400 个 task，并整理成功率、碰撞率、失败类别分布。

---

## 13. 常用命令

启动 GraspNet：

```bash
cd "/home/hwy21/桌面/whole_body_manipulation/Visibility-Awared-Mobile-Grasping/third_party/perception_services"

export CONTACT_GRASPNET_CHECKPOINT_DIR="/home/hwy21/桌面/whole_body_manipulation/Visibility-Awared-Mobile-Grasping/third_party/perception_services/third_party/contact_graspnet/checkpoints/scene_2048_bs3_rad2_32"

pixi run -e grasp grasp-server --port 4003
```

检查服务：

```bash
curl http://localhost:4003/healthz
```

运行主方法 benchmark：

```bash
cd "/home/hwy21/桌面/whole_body_manipulation/Visibility-Awared-Mobile-Grasping"
conda activate mobile_grasping_in_dynamic

python experiments/run_maniskill_benchmark.py \
  -c grasp_anywhere/configs/maniskill_fetch.yaml \
  -g 0 \
  -p \
  -n 1 \
  -t
```

查看结果摘要：

```bash
python -c "import json; p='results/ours_static/run_20260701_230646_958703/benchmark_results.json'; d=json.load(open(p)); print(d['summary'])"
```
