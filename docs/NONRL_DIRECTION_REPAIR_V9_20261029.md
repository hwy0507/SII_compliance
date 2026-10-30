# 三真实场景方向覆盖修复 v9：当前接续

更新：30条正式补采及数据交接已全部完成，公平训练已实际启动。
当前首先读[数据与训练交接](NONRL_V9_DATA_AND_TRAINING_20261029.md)，
不要再次派发下文已结束的补采服务。下文4/30等数字是历史快照，主矩阵仍未修复。

Goal active，主矩阵尚未修复。原v8完整108已独立审查并共享，
[结果](NONRL_V8_FULL108_RESULTS_20261029.md)为Task1/108、Strict0/108、BOTH0/108。
不能继续沿用旧99条全失败的临时结论，也不能把本轮teacher开发成功当学生主矩阵成功。

## 八球真实物理诊断已完成

`outputs/nonrl_ball_coverage_probe_20261029_v6`于08:06:42–08:17:31 UTC执行8×30秒，
4,800,000物理子步。原unit `sii-ball-coverage-v6-20261029.service` 正常exit0，
InvocationID `0e0eefbcf4154713ae3659ec830a398a`；全部198绑定源保持，未热改运行源码。
本机CPU6/数值线程1/3GiB/禁swap；观察收据保留进程与cgroup实测。
08:08:56–08:17:56 UTC共19样本，最大MemoryCurrent1393098752bytes、OOM/oom_kill/实验swap均0。

所有8条均完成场景任务、安全检查和实际方向覆盖；6条满足手/手指受扰资格，2条失败。

| 初始偏移方向 | 撞击角 -0.8rad | 撞击角 +0.8rad |
|---|---|---|
| -X | 合格 | 合格 |
| +X | 仅fr3_link7接触，保留失败 | 合格 |
| -Y | 合格 | 合格 |
| +Y | 仅fr3_link7接触，保留失败 | 合格 |

两失败不是teacher任务失败，但不满足用户要求的末端受扰采集，不能作为合格标签。
不放宽接触资格，不把“发生任何机器人碰撞”替代“推到末端”。

全八真实25Hz轨迹：物体搬运方向投影72.458–81.030mm，回程75.197–81.482mm；
六合格回合均实际到达接近/搬运/回程并符合canonical方向。该统计来自保存的手/物位置，
不是独立重建运动学，也不是抓持接触稳定性证明。所有失败均纳入审查。

- 全八审查SHA：`7a93c27d1de08dcfde55415e80dcf1517e25c6261a710759d7fcf18969512da6`。
- 实际位移SHA：`814cb886696971930f377f5ba2eae63b372776e0e25d8d2940ef3052e05b9df3`。
- 仓库小证据：`docs/evidence/NONRL_INTENT_RECOVERY_20261029/V8_BALL_V6_{REVIEW,ACTUAL_MOTION,EXECUTION_OBSERVATION}.json`。

## 已登记并启动正式补采

新入口 `tools/prepare_special_direction_collection_20261029.py` 只读取完整开发审查，
不读取学生模型或回归标签。每个方向只允许采用有真实接触且合格的撞击角；
两条失败保留但不进入正式方向依据。实际位移回顾要求全部8身份一致。

新目录：`outputs/special_scene_direction_collection_20261029_v9`。
计划SHA：`34a9142450b1cb633fd8da2c117415eaaccc635ff10b69d49d97af48e8840e33`，208绑定源。
各场景10条、8train/2val，原30身份/seed/划分保持。
棍/桌角20条配置不变；球的原速度/shift/高度参数保持，只新增方向/撞击角控制。
两条Y方向验证身份保留原独立速度/shift组合，仍不参与拟合。
两条同方向同角度的训练身份仍有不同原速度/shift，不冒充全新方向。
不直接复用开发轨迹或旧示范：全部30条按新前瞻计划重新执行与资格审查。

启动时间08:20:36 UTC；唯一模拟器服务：
`sii-special-direction-collection-v9-20261029.service`。
父PID1452135，InvocationID `173a263a95e345f8b6c84f313e017185`。
本机CPU6/数值线程1/3GiB/禁swap。收尾检查rod_00至rod_03共4条qualified，rod_04在途。
后续请读取真实`COLLECTION_PROGRESS.json`与当前`progress.json`，禁止按此快照重复启动。
主机swap近满不等于实验使用swap；实验cgroup禁止swap，启动时MemAvailable约4GiB。

新计划通过原v3完整验证；另独立核对30身份/seed/划分、teacher/action contract、
20棍角配置和10球原速度/shift/高度完全保持。只有新增的覆盖变量改变。
目前没有重训学生、没有新的108结果，不宣称修复成功。

## 下一步（依赖真实完成）

1. 监视原补采到30条完整，检查失败原因；不得自动替换失败身份或直接把未合格数据送入拟合。
2. 全部合格后用`build_special_coverage_dataset_20261029.py`构建独立
   `outputs/special_scene_direction_retrain_20261029_v9`，先运行
   `audit_special_coverage_dataset_20261029.py`检查真实train方向×估计载荷覆盖。
3. 三方法共享24train/6val；复用`train_special_scene_models_20261028.py`：
   3seed、每家每seed12候选、神经候选32000更新、相同验证动作MSE选模。
   完成后审计实际曝光与保存模型重放，再锁定九模型。保持解析ridge ESN，不因本轮失败改成新算法。
4. 在原已检查12条件上进行9模型108回归，独立审查六指标。
   这不是未见确认测试。若仍差，继续基于teacher/学习/场景证据定位，不以低loss宣称修复。

本轮仍无RL、子agent、服务器计算、门槛放宽、物理/actor输入/filter/执行器热修改。
八球完整成功/失败和新计划的168成员包已本地逐成员与源前后核验；455421181bytes，
SHA256 `89abcc6cf6060d725a334c10def28141399c150bd54edba02de048c66993cdee`。
暂存及最终共享大小/hash均核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_ball_direction_repair_20261029_v1/PROBE_AND_PLAN.tar.gz`。
v9在途物理产物未在该包内；原LOCAL_RECEIPT保留创建时的pending字样，不回改历史记录。
