# 原ESN权重：顺序扰动完整回放

2026-10-02 按用户要求只运行一条55秒ESN评估并生成完整动图，不重新训练。
开工核对远端main `d43f050f3d56e5794cbc1b9dd84d74fb8308ac79`、
baseline `699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0`，未修改baseline。
复用上次用户所看动图的p=.1 ESN权重，SHA256为
`9f4b5a8168142595873ff1c8fdcaa3b2186b7a1d1edab916d2bbd38fe5988023`。
`TRAINING_COMPLETE.json`只是原训练记录的逐字节副本，本轮无训练。

## 结果

| 项目 | 新时序结果 |
|---|---:|
| 完整物理时间 / 子步数 | 55秒 / 550000 |
| 任务成功 / strict | false / false |
| 最终阶段 | load_transfer |
| 轨迹位置RMSE | 38.708 mm |
| 峰值执行器力矩 | 48.463 Nm |
| 峰值末端线速度 | 0.094228 m/s |
| 最大外部穿透 | 0.122975 mm |
| 动作 / 储备池重放最大误差 | 0 / 0 |

仅将推杆启动由7秒改为12秒，使用`sequential-r12-v1`，其余物理设置/门槛不变。
实际人手有效接触首次4.2813秒、末次8.8977秒，累计3.5756秒；球在2.0937秒接触。
推杆和柱子没有记录到>0.05N的有效机器人接触，因此不能将无接触解释成成功让位。
完整放置未完成，strict所要求的接触覆盖也未满足。时序分离修复不等于任务修复。

独立审计重新计算物理子步RMSE/峰矩/峰速，检查有限值、checkpoint与MJB绑定、
48D/7D动作与128维储备池精确重放，全部通过。使用MuJoCo3.11.0，开发dt=1e-4；
冻结MJB SHA256=`5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9`。
本机单仿真单线程，实际MemoryMax=3GiB、SwapMax=0；运行与渲染已结束。
没有运行MLP/baseline或正式dt=5e-5，不作新时序算法优劣结论。

## 完整媒体与共享证据

三视角为全景/末端/柱子桌角，原速完整55秒；MP4实测1375帧、25fps，
GIF实测275帧、5fps、960×280。GIF会漏掉短碰撞细节，优先观看MP4。
媒体从已保存MJB和状态回放，mj_forward渲染，无额外mj_step；画面标注真实task/strict。

服务器：`arm1@192.168.31.70`。
归档目录：`/home/arm1/sii_shared/SII_compliance/runs/main/esn_sequential_r12_media_20261002_v1/`。
目录内`evidence.tar.gz` SHA256：
`c6938228a27aeb7a6b08d33245d96325fb4ec0cd2274582cfb89cc9a268c1e31`。
解包后的`outputs/esn_sequential_r12_media_20261002_v1/`含原始轨迹、checkpoint、
execution.json、AUDIT.json及`media/replay_threeview.{gif,mp4}`。

- MP4 SHA256：`d51f682141fbca62432c78c886353f4745c99189717c8d35ccdb9a1e3ba3dba1`
- GIF SHA256：`308883a2f82717f0abec76a3a5114b5f12a6700ffdf03a77bdfe69cd260ff05a`
- rollout NPZ SHA256：`8b25c9635aa424bfa108305b5f731eab5373fa700912011cc99bc30b9346e47a`

冻结提交源码在共享根目录下
`source/d43f050f3d56e5794cbc1b9dd84d74fb8308ac79/repository.tar`，SHA256为
`887e6bfb8be2213b0dd3abc8ba606b7438ad3b3a7157c498f01239a108a2e37b`。
新增本次启动器运行时尚未提交，其准确副本随run归档，hash记录在execution.json。
启动器`tools/run_esn_sequential_media_20261002.py`拒绝覆写结果，并核验运行时、
内存限制、原权重和非时序源码；运行命令与媒体输入输出hash完整保留。
