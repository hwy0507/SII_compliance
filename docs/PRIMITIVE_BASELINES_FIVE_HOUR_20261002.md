# 四特化场景 baseline 五小时协议 — 2026-10-02

用户授权2026-10-02 07:36:31–12:36:31 UTC（15:36–20:36上海），当前线程持续工作，不建立定时任务。最终环境/WBC由另一agent负责，本轮使用四视频的原冻结特化场景。

四视频SHA完全匹配服务器teacher_eight_20260918原件。原轨迹与命令来自 outputs/esn128x128_four_scene_20260918/teacher_gallery/{ball_013_000,push_001_102,corner_013_repeat_1_901,table_corner_003_201}。场景分别使用v7球、core持续无挡板棍推、v6侧角及legacy厚桌角，不将昨天综合office环境冒充视频场景。

## 采样与训练

复用collect_four_scene_pareto_20260918.py中的物理随机化范围和.35/.7/1强度；四类每类1000训练定义，12验证、12测试。各split独立随机种子720100/820100/920100；保存完整参数与物理hash，无重复。训练按四场景轮转、每场景固定随机排列；replay按场景等概率再按transition均匀采样，避免56秒corner主导13秒table。条件定义数不是实际训练完成数；不承诺五小时完成4000独立完整轨迹。

纯RL使用已固定官方SimbaV2 86899c277cdc697b2b02d827243de1ea93f20a1d，在线从零，不做BC。共享proprio48/action7：q7,dq7,nominal6,pose_error6,twist_error6,estimated_load7,estimated_wrench6,path3；不输入场景ID、时间、接触真值、几何、teacher动作。任务层保留源场景原逻辑，包括球接触phase gate及legacy放置监督器，不冒称actor接收这些真值。

两reward office_task/有界metric，各seed74001/74002，目标60k；gamma.9995、UTD2、initialtemp.0001、entropy-2、warmup5000/std.02。每10k固定checkpoint，原始reward与官方归一化记录。有限预算不保证收敛，不把失败隐藏或解释为SimbaV2本质弱。11:40UTC停止新增训练回合，当前回合完整保存；预留56分钟评测/媒体/审计。每seed实际steps与共同固定checkpoint单独报告。

经典控制器为标准六维M-D-K导纳与bias+Jᵀ(K e+D e_dot)+零空间阻尼阻抗。导纳K=[60,150,300]，阻抗K=[300,600,1000]，各zeta=[.8,1.4]；每候选四场景×两个训练fixture共8回合，各6候选，共96回合。所有场景共用一组选定参数，不按测试场景选控制器。选择按物理有效任务数→接触任务数→物理有效数→四场景均衡归一化三指标，验证/测试不选参。11:30UTC搜索派发截止。RL与经典不同训练机制/样本数明确报告，评测条件成对一致。

## 接口、证据与限制

实际动作在env.step入口替换，原legacy teacher可被旧runner计算但被丢弃，绝不输入baseline；旧original.json/NPZ的controller/teacher action标签不代表执行控制器，权威记录为新result.json/control.npz/intervals.json。原安全层、限幅/力矩变化率、场景dt保留；阻抗通过共同力矩限幅和slew投影。厚桌角用paper_mpc调用路径以去除VMC独有的内部增益调度；共同参考/物理保持，属于显式baseline适配。

任务成功保留primitive原条件；legacy厚桌角必须真实抬升+放桌+松手，不使用只完成抓取也会true的旧task_success。物理数值门槛外部穿透≤0.2mm；目标扰动接触与其他桌面/底座接触分别记录，不以其他碰撞冒充球曝光。接触pair时长按每物理步union计数；原pilot中的重复接触点计时问题已修，旧数据保留。

球6.4秒审计开关对照：time/action/qpos/qvel/ctrl/position/object_position逐元素最大差全0；全物理子步RMSE/实际力矩峰/末端峰速独立复算通过。RL pilot实际750步、1470更新跑通，失败保留；两经典球完整30秒通过接口，固定阻抗任务成功、导纳失败，未作泛化结论。厚桌角两个经典试跑物理通过但放置失败。

所有新产物主机arm1@192.168.31.70，根/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002：
- reference_videos与VIDEO_SOURCE_MATCHES.json：本地四视频原件/匹配证据。
- source_scene_20260918：原场景冻结源码；SOURCE_HASHES.json。
- ANCHORS.json/FIXTURES.json/BUDGET.json：源配置、独立样本定义、授权时窗。
- frozen_adapter01：本轮执行器/训练代码快照及HASHES.json。
- invariance01/AUDIT.json：真实物理无扰动与三指标复算。
- campaign01：正式本轮开发训练/搜索结果（启动后生成）。

开工已fetch main=f3437ad（新靠手桌角任务/ESN失败），baseline=699e317。未合并main或修改其环境/WBC，不恢复旧SIGSTOP训练，不创建/恢复heartbeat。最多同时三路本轮仿真，Spark总并发≤4。
