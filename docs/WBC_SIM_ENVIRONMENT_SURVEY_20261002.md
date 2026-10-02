# WBC 仿真环境调研与 robosuite 参考运行（2026-10-02）

## 结论

当前 FR3 项目最合适的下一步是沿用 MuJoCo，并把 robosuite 1.5.2 的 arena / object / camera / sensor 组织方式移植到 FR3，而不是立刻迁移到 Isaac Sim。robosuite 的官方 Stack 场景已经在 arm1 服务器独立环境中跑通，并输出了可视化参考视频。

## 主要候选

| 环境 | 适合什么 | 对本项目的判断 |
|---|---|---|
| [robosuite](https://github.com/ARISE-Initiative/robosuite) 1.5.2 | MuJoCo 操作任务、桌面/托盘/箱体、Stack、PickPlace、NutAssembly、Door、ToolHang、Wipe；composite controller、whole-body IK / Mink IK、多模态传感器 | 当前首选。可复用官方 arena 和物体 XML，同时继续由现有 FR3 FLASK/WBC 接管动力学 |
| [Isaac Lab](https://github.com/isaac-sim/IsaacLab) | Isaac Sim GPU 仿真、Franka Lift/Stack/Cabinet、RGB/depth/segmentation、IMU/contact sensor | 场景和渲染最丰富，但 arm1 当前没有 Isaac Sim / omni runtime，迁移代价大 |
| [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie) | 高质量机器人模型，包括 Franka/FR3 类资产 | 资产库，不是完整 manipulation benchmark |
| [Drake](https://github.com/RobotLocomotion/drake) | 动力学、inverse dynamics、轨迹优化和验证 | 算法验证强，直接可用的桌面操作场景少 |
| [Pink](https://github.com/stephane-caron/pink) | Pinocchio + QP differential IK，任务和约束组合 | 适合作为 WBC/QP 后端，不负责复杂物体场景 |
| [ManiSkill](https://github.com/haosulab/ManiSkill) | GPU 并行 manipulation、丰富物体和视觉任务 | 适合大规模视觉/策略训练，接入现有 FR3 WBC 的成本高 |
| [RoboCasa](https://github.com/robocasa/robocasa) | 真实厨房/家庭场景 | 视觉真实度高，但对当前 WBC 验证过重 |

## 参考运行

独立环境：

- Python 环境：/home/arm1/vmc_mujoco_runtime/robosuite_wbc_venv
- robosuite：1.5.2
- MuJoCo：3.3.7
- 控制器：官方 BASIC composite config，右臂 OSC_POSE
- 场景：官方 Stack
- 控制频率：20 Hz
- 参考脚本：code/mujoco_6d_vmc_benchmark/experiments/robosuite_reference_20261002/render_stack_reference.py
- 视频：/home/arm1/vmc_mujoco_runtime/robosuite_wbc_reference_20261002/robosuite_stack_reference.mp4
- 网页：http://192.168.31.70:8765/robosuite_stack_reference_20261002/

参考视频使用官方 arena 和两个可抓取方块，并在右侧显示 stage、末端跟踪误差、reward、MuJoCo contacts 和误差曲线。运行得到 288 帧、最大接触数 13、末端位置误差均值 16.6 mm。waypoint 控制用于展示场景和数据通道，不能把它当成成功的 learned stacking policy。

## 迁移计划

1. 保留当前 FR3 upstream asset、FLASK planner 和 computed-torque WBC。
2. 复用 robosuite 的 arena / table / tray / bin / object / camera / sensor 结构，避免继续使用孤立柱子。
3. 将 FR3 的碰撞几何、末端 site、关节/力矩传感器接入同一套场景；用独立的 collision audit 检查桌面、托盘、箱体和物料盒。
4. 以 Stack、PickPlace 和 NutAssembly 三种场景做分层验证：避障轨迹、末端跟踪、关节限位、接触数、峰值力矩。
5. 等 MuJoCo 版本和接触审计稳定后，再考虑 Isaac Lab 的 GPU/视觉迁移。

## 限制

这次参考视频使用 Panda，是为了先固定场景和控制器接口；它不是 FR3 的最终复现。robosuite 的 GR1/Mink whole-body 示例在当前安装中还缺少 robosuite_models，所以没有把不可用的 GR1 结果冒充成已完成的 FR3 WBC 验证。
