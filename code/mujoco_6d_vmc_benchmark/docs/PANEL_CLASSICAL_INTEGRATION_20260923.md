# 同协议 panel push classical 接入审计

2026-09-23。新增 `scripts/run_panel_classical_adapter_20260923.py` 在内存中向原 panel runner 动态创建的 primitive 模块注入 controller loader/environment hook。未修改历史 primitive、panel、physics、安全栈文件；新结果保存在独立目录。

本机单进程、BLAS=1 的 8 s impedance smoke 已完成，teacher_called=false，task success=true，但 accepted_panel_demo=false（rod contact=0，guard penetration=0.369 mm）。这只证明接口可运行，不能视为有效碰撞 baseline。

服务器运行目录的共同前缀为：

`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/`

- `panel_matched/`：45D legacy 接口诊断，VMC/impedance/admittance × 3 fixture；不得与48D学生拼表。
- `panel_matched48/`：统一48D接口的新匹配开发矩阵，VMC/impedance/admittance/current MLP/current nonlinear ESN × 3 fixture。
- 对应隔离源码：`source_resume/` 和 `source_panel48/`。
- 每个目录归档 `protocol.json`（源码hash、fixture、模型hash），每条归档 command/log/JSON/NPZ，完成后生成 `FINAL_RESULT.json`。

## 共同物理协议与评价

三种物理fixture `(seed, push_angle rad, push_height m, payload kg)`：`(9300,-0.15,0.575,0.085)`、`(9301,-0.05,0.580,0.100)`、`(9302,0.10,0.585,0.115)`。这三项联动变化，只是三个开发条件，不是全因子泛化评估。

所有方法使用相同 raised_hand_rim workstation、24 s、loaded_lift event、持久推杆（hold=1e6 s）、push stroke=0.18 m、press=0.5 s、force limit=12 N、event delay=0 s。参考参数来源是历史 loaded_push_release artifact 的 arguments；新方法全部重新仿真，未复用旧分数。

strict_success要求原panel accepted_panel_demo为真，且所有外部接触无link0–link4碰撞。原panel gate要求task success、rod contact>0.3 s、最后2 s已脱离rod、final rod gap>2 mm、外部最大穿透<0.2 mm。task success或guard接触本身不代表有效rod任务。

全程XYZ RMSE按25Hz输出的 `(position-target)` 逐轴计算，3D RMSE是三个轴RMSE的欧式范数。已启动快照中的 `physics_peak_motor_torque_nm` 实际是每CONTROL_DT=4 ms更新并保持的applied command torque峰值，来源为environment的peak_torque；它不是内层MuJoCo物理步的qfrc_actuator实测峰值。仓库runner已将此字段准确命名为 `control_step_applied_torque_peak_nm`，未覆盖正在运行的快照。`speed_peak_25hz_mps`是25Hz采样峰值，不是物理步速度峰值。阶段目标切换会影响全程RMSE，应结合task stage和接触指标解释。

## 已确认的实现边界

1. 48D观测的joint-load仍是 `[32:39]`：q7+qdot7+nominal_twist6+pose_error6+twist_error6共32维。统一48D仅把后面的estimated_force3扩为estimated_wrench6，path从42移到45。admittance所读joint-load索引正确。
2. Impedance使用Cartesian pose/twist反馈映射为J^T torque，复用原torque限幅和slew。它替换了velocity-servo torque，因此nominal joint-command速度/加速度限制不能直接限制该torque控制产生的实际运动。45D诊断已出现约1.65 m/s采样峰值和87 Nm力矩峰值；必须记录为实现限制，不能忽略。
3. Admittance仍是虚拟M-D-K积分的velocity-only residual；内部offset进入弹簧反馈，但尚未把offset作为WBC pose reference。该版本不代表充分调优的参考偏移式admittance。
4. Classical模式以model+mixture=0绕过teacher调用；panel要求的memory profile仅保留配置兼容性，JSON中的teacher_called必须为false。
5. 接口hook通过唯一源码marker注入，若原panel结构变化会显式拒绝运行。它是隔离适配层；后续应把controller factory提升为原runner正式接口，减少动态源码耦合。

## 复现入口

```bash
python scripts/run_panel_classical_matrix_20260923.py \
  --reference /path/to/loaded_push_release_20260918/rollout.json \
  --menagerie /path/to/mujoco_menagerie --output /fresh/output/path \
  --workers 3 --unified48 \
  --mlp /path/to/unified_6d_matched_students_20260921/mlp/20260923_retry1/best.npz \
  --esn /path/to/unified_6d_matched_students_20260921/esn_nonlinear/20260923_retry1/best.npz
```

输出目录必须不存在；避免覆盖历史结果。服务器用nohup独立进程运行，终端中断不影响任务。

验证：本地下载的48D admittance seed9300 trace的observation shape为 `(600,48)`，全部有限；protocol记录的MLP/ESN checkpoint hash与独立审计结果一致。所有策略均按同一25Hz时序处理48D观测。

附加MLP公平性审计：训练将归一化输入clip到[-12,12]，当前MLP推理未clip。使用本轮冻结checkpoint的mean/std对三条原始MLP trace只读计算，seed9300/9301/9302的归一化绝对值最大值分别为10.0984494677、10.1159455065、10.5786410538，每条超过12的元素均为0/28800，受影响step均为0/600。本轮比较未触发该差异；未修改推理代码。
