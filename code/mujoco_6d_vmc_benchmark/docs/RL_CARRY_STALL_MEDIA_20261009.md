# RL调阻抗搬运停滞：完整三视角回放

选取已完成的第一个开发身份`repair_development_000`，用于解释“搬运阶段卡住”，
不是按表现挑选的代表性统计，也不替代八条件结果。
模型为本机11k交互的RL调阻抗checkpoint，Task/Strict均false，完整55秒未提前终止。

- 4.56秒结束lift，随后进入carry；最大抬升162.010mm。
- 10.588秒开始接触意外桌沿，持续至55秒，累计44.412秒。
- 未进入承载转移/释放阶段，最终物块到目标的XY误差86.415mm。
- 回合RMSE23.289mm、峰值力矩37.059Nm、峰值速度0.37024m/s。
  低误差与小幅运动不能代替完成放置。

下载目录有完整GIF和MP4：
`/home/airpig/下载/RL调阻抗_搬运卡住_三视角_20261009.gif`及同名`.mp4`。
三视角分别为全景、末端、柱/桌角；绿色圆点仅为目标位置的渲染标记。
画面约55.2秒、276帧、5fps，覆盖原记录0.04–55秒，未剪掉失败段。

本地使用原MuJoCo3.11.0及保存的MJB/qpos/qvel/ctrl，执行`mj_forward`后离屏渲染，
没有`mj_step`、重训、重新选择动作或改变原物理轨迹；未打断两路训练。
复用`tools/render_office_threeview_20260929.py`，参数`--stride 5 --fps 5`，
渲染单线程、MemoryMax1GiB/禁swap。imageio_ffmpeg0.6.0从既有环境复制到独立临时依赖目录，
未修改训练解释器或冻结源码。视频完整解码、GIF全部帧读取及中间/最终帧目视核验通过。

输入轨迹SHA：`df115c6b32efaa54da948ab00c7ff9921ae38bca895125b52b7a30d9a9174ddd`。
模型SHA：`d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`。
GIF SHA：`5da853bf3475561101739a457f75379e4eb8fd0b39a0467d271547ce7660476a`。
MP4 SHA：`c09ada450e7e1d3d9411d911a7891d1a17a82289d9a0bd78cc6ebf3f0e99b3f2`。

原始回合已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage4/evidence/parameter_impedance_segment011k__repair_development_000/`。
新媒体本地目录为`outputs/baseline_local_rl_20261009/media_impedance_dev000_20261009/`；
服务器媒体与渲染源码已逐文件核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_impedance_carry_media_20261009/evidence/`，
6文件、10968041字节，清单SHA
`ba0c4e2f27362f8dd4306657bbd2b9c600a9c9d47c35c468150dd847904a3ae9`。
