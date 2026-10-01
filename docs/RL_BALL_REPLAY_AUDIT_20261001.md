# RL 球碰撞视频问题交接 — 2026-10-01

用户原话：两个 RL MP4 中球碰一下就很诡异地弹开，没有 ESN 和 zero 自然。用户接受 RL baseline 结果差，但需确保环境、碰撞和对照解释可信。用户已下班，明确明天再说；本次记录后停止排查，不启动实验或自动跟进。

## 已确认（仅针对现有视频）

检查对象为 campaign_01 的 100k、RL seed61001、case_000，非后续有界奖励修复结果。已在 Safari 查看原 MP4 撞击窗口的连续帧拼图，以及两个 RL 原视频截取的慢放。

| 方法 | 有力球—机器人接触部位 | 首次接触 s | 累积接触 ms | 峰值 N | 累积冲量 Ns |
|---|---|---:|---:|---:|---:|
| office_task | hand / fr3_link7 | 2.06275 | 1.55 | 1057.85 | 0.2852 |
| metric | 未记录到（检测阈值 >0.05 N） | — | — | — | — |
| ESN | fr3_link6 | 2.10565 | 0.50 | 1598.90 | 0.3605 |
| zero | fr3_link6 | 2.10560 | 0.45 | 1668.83 | 0.3661 |

- task 的球撞到手腕附近后偏转，随后在桌面附近运动；metric 机械臂抬起，球从下方经过、落桌后继续前行。不能把 metric 描述成已承受球撞击，也不能把不同接触部位当作相同撞击响应。
- 四者 MJB SHA256 相同：aaf20cb6041b61c89d668863e4a8da908937454952509f64c73ad3172fa9b7f7。这只支持模型相同，不能证明接触条件相同或数值动力学完全可信。
- 原状态每 40 ms 保存，渲染 stride=5，MP4 为 10 fps：相邻画面跨 200 ms 仿真时间，以 2 倍速播放。碰撞被压在帧间，明显放大跳变观感。此前把原状态采样间隔当成视频间隔的说法需要更正。
- 高频球日志的条件写死为 t<0.30 s，但该 campaign 在 2 s 发球。四者高频日志都仅有 289 点，截止 0.29995 s，接触全 false，完全漏掉实际撞击。现有归档不足以还原亚毫秒速度/能量变化。
- 冻结 validator 将延迟发球标为 presentation-only，正式评估默认零延迟；campaign 四种方法均用了 2 s。明天需明确该开发协议与正式协议边界，不能混称。
- 发球前固定球位姿并清零速度，发球时一次设置 y 速度；已读该函数，未发现发球后专门给 RL 球额外速度的代码。不能仅凭外观推断注入能量。
- ESN/zero 接触时间更短、峰力更大，故“接触短所以 RL 碰撞不自然”的旧推断不成立。此次没有修复物理、重训或新仿真，不能宣称问题已解决。

## 明天待继续（当前暂停）

1. 先向用户说明以上确认项，区分跳帧、接触部位变化、未受撞击与尚未验证的数值异常。
2. 核查球与桌面/其他几何的接触序列、手腕速度、碰撞前后动能，判断 task 偏转有无数值异常。旧日志缺高频撞击证据，不能伪造结论。
3. 如继续诊断，在独立版本修正相对发球时刻的高频记录，保存完整接触对、力、速度；不热改冻结结果。先按原条件短回放验证，不能靠补帧制造物理证据。
4. 确认是否需共同受撞条件的柔顺性测试：metric 未曝光应单独报告；不同受撞部位不能直接比较抗冲击表现。保留原策略的真实失败。
5. 更清晰的视频需提高状态记录/渲染帧率并标注真实速度；现有慢放只是延长原画面，无法恢复缺失撞击帧。

## 精确路径与复核

主机 arm1@192.168.31.70，全部项目文件留 Spark。

- 原实验：/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/
- 原数据：上述目录 evaluation/{office_task_seed61001,metric_seed61001,esn,zero}/case_000/rollout.{json,npz,mjb}、rollout_ball_detail.npz、BEHAVIOR.json。
- 原视频：上述目录 media/<method>/replay.mp4 与 manifest.json。
- 数值证据及输入/输出 SHA：上述目录 report/BALL_REPLAY_AUDIT_20261001.json。
- 新只读证据提取脚本：code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/audit_ball_replays.py。
- 运行命令：`/home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu/bin/python /home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/audit_ball_replays.py`。已成功，四者原 MP4/MJB 与既有 manifest hash 一致，视频 10fps。
- 冻结源：/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/frozen_main_01/code/mujoco_6d_vmc_benchmark/scripts/validate_office_apparatus_v5_20260917.py；延迟发球约 248–258 行，高频日志约 332–334 行。
- 派生媒体：/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/assets/ball_replay_audit_20261001/。每方法 jpg 为原 MP4 零起始帧 8–15（约仿真 1.64–3.04 s），slow.mp4 为帧 7–20、原播放速度四分之一，即仿真约 0.5 倍速；画面内旧 replay 2x 字样未改，不能误认慢放速度。无插值、无新物理。
- 浏览页：http://192.168.31.70:8765/ball_replay_audit_20261001.html

本次开始检查 main=ba84ed8a39ed743f603aa5d60e901bdf87090e1d、baseline=17d00a93da4efcf5f8f747ed52909039f4fc2090；只提交 baseline，不操作 main，不恢复旧暂停作业或旧 heartbeat。
