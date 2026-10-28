# 三类独立场景展示：最新版 new30 VMC teacher

用户要求仅查看场景，运动由最新版 VMC teacher 产生。本次为三条独立物理运行，
不是从综合回合切出三个时间段，也不是旧 ESN/旧 teacher 视频。

## 来源与边界

- Teacher：`teacher_student_15h_20261012_v3/TEACHER_CHOICE.json` 中的 `teacher_lhs_0`，
  使用该次采集冻结的 `source/tools/optimize_tool_contact_20261002.py::ParameterTeacher`。
  配置 SHA256 `352d6d75662aecceb2777aaa2ac5d8e3b0b576a54635930fca8d081cc879c787`，
  与新增30条示范的全部 lineage 配置 hash 精确一致，无新调参。
- 父场景：归档 office-v6 MJB；仅在新的展示目录中创建隔离变体，保留机器人、
  搬运物体、任务、teacher 输入、动作滤波器和执行器限制；dt=5e-5，完整运行55秒。
- 隔离时保留装置名字/关节以兼容原 evaluator；无关装置的 geom 移出工作区、
  禁用碰撞并隐藏。机器人/搬运物体等所有保留 geom 的位置、碰撞掩码、颜色、尺寸
  均与父 MJB 做数组精确比较。不改正式108/180回合测评的任何文件。
- 这三个展示世界不是9月30日旧 teacher bank fixture 的逐字节重跑，
  也不是新的正式公平测评矩阵：它们是从当前综合世界中隔离出对应干扰类型的演示。
- 单机 airpig 串行、单线程、MemoryMax=3GiB、MemorySwapMax=0；服务器仅作归档。

| 场景 | 保留干扰 | 展示片段（仿真秒） | 播放 |
|---|---|---|---|
| passive_corner | 刚性边角/台阶；隐藏柱子和主动装置 | 0–25 | 2倍速 |
| active_short | 小球撞击；去除刚性阻挡和其他主动装置 | 1–4 | 半速 |
| active_long | 推杆持续推压；去除刚性阻挡、小球和人模型 | 10–24 | 原速 |

桌面和放置支撑面保留，不将普通支撑接触声称为完全无接触环境。
所有媒体均由本次保存的 qpos/qvel/ctrl/mocap 轨迹回放，渲染时只做 `mj_forward`，
不重新积分、不手工修正动作；画面左为全景、右为接触近景。GIF逐帧解码核验，
源轨迹/MJB/媒体 hash 与真实 Task/Strict 结果见同名证据目录。

## 文件与可复现入口

- 已核验共享归档：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/three_isolated_vmc_media_20261028_v2_delivery/SCENES.tar.gz`。
  大小344,361,223字节，SHA256 `d50362b604135201b975c8b14cb14e391a0020f7ca3c15252bfd4079cc7ae150`；
  本机、远端暂存、最终目录三处一致。包含两份脚本、v2真实轨迹/物理记录/源码overlay/媒体，以及v1失败收据。
- [逐场景结果与媒体hash](evidence/three_isolated_vmc_scenes_20261028/RESULTS.json)。
  三条均完成55秒、actor/filter replay误差均为0；静态边角Task/Strict均失败，
  小球和推杆均为Task/Strict成功。仅是演示结果，不推导方法优越性。
  小球接触累计0.00555秒，推杆接触累计5.3574秒；三个GIF全帧解码、三个MP4完整解码均通过。
- 生成：`code/mujoco_6d_vmc_benchmark/tools/render_three_isolated_vmc_20261028.py`
- 渲染：`code/mujoco_6d_vmc_benchmark/tools/render_isolated_scene_clip_20261028.py`
- 本机缓存：`code/mujoco_6d_vmc_benchmark/outputs/three_isolated_vmc_media_20261028_v2/`
  下各场景 `media/scene.gif` 和 `media/scene.mp4`。
- Python：父工作区 `.venv-sii-local-rl/bin/python`，MuJoCo3.11.0。
  视频编码调用现成独立 FFmpeg 可执行文件，不更换仿真环境。

## 保留的失败记录

首个展示适配器的 `ball` 子串误匹配到机器人 `hand_ball_proxy`，在生成任何交付媒体前
检查发现并停止该新任务。`three_isolated_vmc_media_20261028_v1/STOP_RECEIPT.json`
及原始文件保留。v2改用准确装置名并增加保留几何数组校验，三个展示均来自v2。
首次渲染因冻结Python环境没有 `imageio_ffmpeg` 模块，在读取轨迹和输出前退出；
随后改用独立FFmpeg程序，未安装包或更改冻结环境。
