# 自由球示范的实际搬运核查

本轮确认：八条v8训练球示范中的物体确实移动，并非只有参考目标变化。
这缩小了故障范围，但不能证明三场景示范已覆盖原搬运任务。
原108仍在运行，主矩阵未修复，没有新采集或拟合。

## 实际记录

仅读取`special_scene_retrain_20261029_v8`的八个ball train身份；validation和测试不纳入统计。
逐一核对训练lineage、trajectory/execution/qualification及原资格输入hash。
读取同一时钟的`legacy.npz`手部、物体、目标及阶段记录，计算各阶段实际位移。
阶段起点使用上一阶段最后一个保存点；approach没有t=0位置，起于40ms。

| train身份 | 物体搬运方向投影 mm | 物体回程方向投影 mm | 搬运期手物相对位置最大变化 mm |
|---|---:|---:|---:|
| ball_00 | 89.288 | 88.702 | 0.551 |
| ball_01 | 90.138 | 89.895 | 0.597 |
| ball_02 | 89.978 | 89.112 | 0.546 |
| ball_03 | 90.104 | 89.389 | 0.589 |
| ball_04 | 90.075 | 89.162 | 0.536 |
| ball_05 | 90.029 | 89.392 | 0.600 |
| ball_06 | 89.994 | 89.689 | 0.554 |
| ball_07 | 90.100 | 89.082 | 0.553 |

搬运目标均为原`[85,35,0] mm`，长度约91.924mm；回程是相反方向。
物体在loaded_lift阶段垂向位移143.935–144.601mm。
搬运与回程的实际投影为正，因此不能将这些示范解释为“手动了、物体始终没动”。
但八条共享同一搬运方向，仍未补上此前查明的±Y主导运动及联合状态覆盖空缺。

相对位置为世界坐标差，包含物体旋转影响，不是滑移量、接触力或连续夹持认证。
该工具读取已存25Hz位置，没有独立从MuJoCo状态重新求运动学；`legacy.npz`在本次
计算时记录快照hash，不冒充原资格审计已绑定其位置数组。原物理资格审计保持独立。

## 对后继修复的具体影响

新增独立`tools/describe_ball_actual_motion_20261029.py`，不修改v6已绑定的198个源。
原八球v6完整运行及原review完成后，可对八个实际`<v6>/<case>/ball`目录同时传入
`--folders`，用`--output`指定新证据文件，逐项查看真实手/物位移。
不能仅凭`physical_direction_coverage`（目标及actor方向核对）宣称物体已按新方向搬运。
正式补采构建后，可传入`--training <新训练根目录>`核查八个train球身份。
工具不新增成功阈值，不修改原review、资格、teacher或训练/验证选择规则。

手算用例覆盖：共同搬运、物体静止、反向运动、阶段未到达；时钟、阶段倒退、非有限值、
形状错误均拒绝。真实八条32个阶段另用标量计算复核实际位移/方向投影/相对位置变化。
这些检查验证算术，不认证新物理或模型成功。

## 证据与执行

- [实际结果](evidence/NONRL_INTENT_RECOVERY_20261029/V8_BALL_ACTUAL_MOTION.json)：
  231100bytes，SHA256 `3b5301e446f3b1017d90406ae24e16f1e85ce9c95e1050eb3588ea8b5df89e06`。
- [手算与实际标量复核](evidence/NONRL_INTENT_RECOVERY_20261029/V8_BALL_ACTUAL_MOTION_CHECK.json)：
  645bytes，SHA256 `70825fd2fd3511b95bad9cbf689b3352ef4e30ac8bce3d536a6c69753aa4f15e`。
- 两工具及两证据共四成员逐字节核验，25290bytes包SHA256
  `6e070fc858f924b2f844e57d4c2114aec76881eb052601566e3052daf0d0d253`；
  暂存与最终大小/hash一致，已共享：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_ball_actual_motion_20261029_v1/SOURCE_AND_EVIDENCE.tar.gz`。

只读服务`sii-v8-ball-motion-description-20261029.service`自然exit0，运行134ms/CPU92ms。
派发配置为CPUAffinity6、数值线程1、MemoryMax256MiB、swap0；未保存进程内限额/峰值快照。
服务随后被回收，后查的默认infinity/空affinity不能当作实际运行限额或内存峰值证据。
原仿真1172675和后处理1201537在06:03UTC仍active；06:05:22UTC原108已85条，RNN2
条件009在44.04s/carry，原科学继续。v6未启动，全部198绑定源逐hash不变。

开工main `7445692e944fecda1ad447e871ee39007e7aa8ae`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`实际fetch/read。
本轮为新增实际运动核查progress，Goal active；原完整108审查归档后继续八球覆盖、三场景
补采、公平重训与冻结回归。可选004审计未重试，无RL、子agent、服务器计算或删除。
