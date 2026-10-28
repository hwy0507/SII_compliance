# v8完整棍推行为审查与实际回放

共享媒体：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_rod00_media_20261029_v1/MEDIA.tar.gz`。
8文件、8519539bytes，SHA256 `f9bb844c1ff51e7392da11ff38662f362fc5668b4b588f12cffee55d02a89233`。
全部本机包成员逐字节核验，共享暂存/最终大小和hash一致，独立目录发布、无覆盖。
[媒体来源](evidence/NONRL_INTENT_RECOVERY_20261029/V8_ROD00_MEDIA_MANIFEST.json)、
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_ROD00_MEDIA_SHARED_RECEIPT.json)。

## 完整十条棍推均在撤棍前回位

`outputs/special_scene_vmc_collection_20261029_v8` 原30条件、24train/6validation保持。
十条棍推（8训练、2验证）已全部完成，原资格和独立时序检查全部通过：真实手接触→让位→
完整手/手指包围盒跨过棍支撑面→进入原5mm回位管并保持原80ms→早于撤棍。
原门槛没有改变；该检查基于40ms保存几何与物理子步接触记录，不是新的独立动力学积分。
[完整十条审查](evidence/NONRL_INTENT_RECOVERY_20261029/V8_COMPLETE_ROD_BLOCK_REVIEW.json)。

| 身份 | 划分 | 蹭过 s | 回位确认 s | 撤棍开始 s | 提前量 s | 相比v7回位耗时变化 s |
|---|---|---:|---:|---:|---:|---:|
| rod00 | train | 7.72 | 8.16 | 12.80 | 4.64 | −0.72 |
| rod01 | train | 11.00 | 11.20 | 13.00 | 1.80 | +0.76 |
| rod02 | train | 7.68 | 7.76 | 12.95 | 5.19 | −0.16 |
| rod03 | train | 7.76 | 7.84 | 12.85 | 5.01 | +0.16 |
| rod04 | train | 7.76 | 7.92 | 12.80 | 4.88 | +0.20 |
| rod05 | train | 7.80 | 7.88 | 13.00 | 5.12 | −0.16 |
| rod06 | train | 7.76 | 8.12 | 12.90 | 4.78 | −0.16 |
| rod07 | train | 7.96 | 8.16 | 12.90 | 4.74 | +0.36 |
| rod08 | validation | 7.76 | 8.24 | 12.85 | 4.61 | +0.28 |
| rod09 | validation | 7.88 | 7.96 | 12.95 | 4.99 | +0.12 |

该变化是相同身份的描述性配对，正值代表变慢；4条更快、6条更慢，不能称全面改善。
对照来源为已提交的`V7_COMPLETE_ROD_BLOCK_REVIEW.json`，身份逐行核对。
两验证条件只按冻结判据检查并报告，没有用其回位时间重选教师参数。
这些时刻不是最终综合任务完成时间，也不是SPT。

## 回放确实来自本轮数据

渲染使用v8 rod00实际`scene.mjb`与`trajectory.npz`，500帧、25fps、20秒；
GIF250帧/80ms，1倍速。渲染仅恢复状态并调用`mj_forward`，没有`mj_step`或控制器重跑。
原工具`render_video_reference_vmc_20261028.py`未改，独立受限渲染服务已自然退出success。
MP4全帧解码、GIF逐帧解码及media hash检查通过。

已实际查看4.76、5.04、6.48、7.72、8.16、12.64秒双机位拼图：手逐渐越过绿色棍，
8.16秒及12.64秒棍仍伸出。右机位挡板仅渲染半透明，物理挡板和碰撞没有删除。
画面辅助理解动作，接触/让位量/完整跨越仍以数值审计为准。
rod00精确首次接触4.7444秒、让位4.84秒、回位确认8.16秒、撤棍12.80秒。

本机媒体缓存（最终数据将在全30终止后归档）：
`code/mujoco_6d_vmc_benchmark/outputs/special_scene_vmc_collection_20261029_v8/rod_00/rod/media/`。
共享MEDIA包仅含媒体和来源manifest，不冒充原始物理全集备份。

## 运行状态与剩余工作

20:33:32–20:43:32 UTC有界只读观察21次，原collector1088910/start31713076始终live，
5→10条真实推进，最后进入ball00；观察自然结束，没有重启模拟器。
20:44:21重新核验同一身份，11/30合格、ball01在途，原接续1089228等待。
MemoryMax3GiB、swap0、线程1保持，cgroup OOM事件0。当前未发生新学生训练。

仍须完成球撞和厚桌角、全30资格审查与24train覆盖审查，再公平拟合/锁定9模型，
真实三场景学生18诊断，最后原12×9=108回归及六指标独立审计。最终效率指标为双成功条件SPT，
完整矩阵双成功最短完成时间作T_ref；无成功记NA。峰矩均值包含所有回合，
舒适度仅用实际人体接触dt分母，机器合规率与Task/Strict分开报告。
当前12已经被检查过，只能称回归，不能称未见泛化。没有根据中间结果修改训练预算或选模规则。

前轮属于实质progress：完成七项教师修复、新30派发和发布。本轮实际fetch/read main
`ce38aa8811694605bc056b2fbc0be95141fe8cf9`、baseline`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。
无RL操作、子agent、服务器计算或数据删除；Goal active，尚未认定ESN或主矩阵修复。
