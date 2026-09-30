# 三训练seed六条件部署：实际启动记录

主协调任务审核具体25job plan、四组最终模型/normalizer和完整证据后明确授权启动。实际启动于2026-09-24 18:22:31 UTC（北京时间9月25日02:22:31），持久driver PID **565765**，一次性launcher PID565764，`start_new_session=True`，SSH断开不终止driver。首条nominal物理worker PID **565773**；首次读取状态为`nominal_parity`、0/25完成、driver存活，尚不能称parity通过。

来源：[准备说明](PAIRED_MULTISEED_DEPLOYMENT_PREPARATION_20260925.md)、[预声明协议](RL_PAIRED_MULTISEED_DEPLOYMENT_PROTOCOL_20260925.md)、[启动JSON（含完整命令）](evidence/paired_multiseed_20260924/deployment_launch_20260925_r1.json)、[资源及启动前校验](evidence/paired_multiseed_20260924/deployment_prelaunch_resources_20260925_r1.json)。

启动前再次逐项核对342项输入、173项执行源码及plan本体，全部hash匹配。实际plan输出目录`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/paired_multiseed_six_fixture_20260925_r1`确认为不存在，未用其它目录的检查替代。全服仅原WebUI Python服务，没有其它仿真worker；实际launcher记录可用内存122446784KiB。最多2worker、已确认空闲slot2，整个服务器仿真总上限4。

plan SHA256：`c094ca89faa946e156843aa366592b43bc943f07c89f932c990d6273c6a5f467`。独立source的BUILD SHA256：`6ca2a7da41b994aa09fbd0cf8d9b82c74ee64f590e96a49b26aa200a9357ab6e`。旧训练/部署快照及被冻结的新source均未修改。一次性launch helper另存于stage根，不进入source；SHA256 `f45b04ca92aa9e1e9010519fd29c6e2bc70dfacaeb0048741e863f37809120a8`。

完整命令（记录实际已执行的命令，不表示再次启动）：

```text
/home/arm1/vmc_mujoco_runtime/.venv/bin/python
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/paired_multiseed_deployment_source_20260925_r1/source/tools/run_paired_multiseed_deployment_20260925.py
--plan /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/paired_multiseed_deployment_source_20260925_r1/plan.json
--expected-plan-sha256 c094ca89faa946e156843aa366592b43bc943f07c89f932c990d6273c6a5f467
--available-worker-slots 2
--max-workers 2
```

cwd为该stage的`source/`；环境固定OMP/OpenBLAS/MKL各1线程、EGL、禁止写bytecode。完整stdout/stderr写入stage下`launch/driver.log`；实际进程、job命令、原始数据及错误写入新的plan输出根。

执行顺序固定为1条nominal9400完整raw parity→四个最终模型9400预检→余下20条。任务/strict失败照常保留并继续；执行/对齐错误停止新launch、不重试、不改gate。现阶段不写入未执行成绩；完成后取回完整归档、checksum核对，再用冻结report复算新24条和parity、绑定复用旧18条并按训练seed聚合。

## 首条nominal完整parity通过

首条nominal9400已完成，driver在约151s进入四模型预检。完整600帧、5份NPZ/36字段逐值相等、数值有限、JSON动力学和MJB一致；[实际parity证据](evidence/paired_multiseed_20260924/deployment_nominal_parity_20260925_r1.json)已取回。MJB SHA256 `587593ff61bdf57b7ebf3986514afc3f8010cf90aeb23d405b5bc856395192e1`。这条只用于复用旧nominal六条，不能作为额外性能样本。

随后实际两worker PID566449/566450，分别seed20260924 direct7/parameter6的9400，RSS各约1.55GiB。进程显示3个OS线程（含CUDA等运行时线程），不冒称整个进程只有1个OS线程；OMP/OpenBLAS/MKL计算线程限制仍为1。该次状态为1/25、无FAILED；后续以实际结果为准。

## 25条运行全部结束

driver用时1740.145s结束，COMPLETE/FINAL均为25条、无FAILED、0执行错误、0安全短回合。已只读确认driver565765及所有本任务物理worker均退出。新24条learned的driver汇总为：seed20260924 parameter6/direct7各task0/6；seed20260925 parameter6 task1/6、direct7 0/6；四run strict均0/6。所有失败保留，此处仍是运行汇总，独立raw复算结果另报。

服务器完整归档582个文件、1,712,652,991 bytes，开始取回本机全新`outputs/paired_multiseed_six_fixture_20260925_r1_archive`。COMPLETE SHA256 `2bc589a81e86cf70df4b7b62f5e28bd5e6e4fb84fddf1c79668d990095ed2ed8`；FINAL SHA256 `4f05071eba3e6d561703407c1f5c4c854491635dab771ac90210fd0218746458`；nominalparity SHA256 `cb083cebf17f791ea565736e988e286eb134662c84b9bab07007597e65ba3fde`。传输完成及checksum通过前不将本记录当作本机完整归档证明。

## 完整归档与独立报告已通过

随后全582文件取回完成，`rsync --checksum --dry-run --itemize-changes`无差异、退出0，见[传输审计](evidence/paired_multiseed_20260924/deployment_transfer_audit_20260925_r1.md)。使用归档内冻结工具独立复算新24条raw和1条nominalparity，通过来源、MJB、动作、物理指标和原task/panel/strict门检查；旧18条仅绑定hash复用，没有重称raw全重算。

[三训练seed结果报告](PAIRED_MULTISEED_SIX_FIXTURE_RESULTS_20260925.md)及同名JSON已生成，670项输入/工具hash留档。MD SHA256 `82f04c104995f4a625af1c895ab01dc9ec2c6748f660aa9fdb5c58ae041317d9`，JSON SHA256 `7d9fac8c9a8c77ff36995df86c91f356cc6333ae87c6c83706a380cc09382683`。

三seed parameter6任务分别1/6、0/6、1/6；direct7均0/6，所有strict均0/6。direct7 seed20260924六条停stage1、没有触杆，不能把49.645mm低waypoint RMSE称为轨迹/任务最好；seed20260925六条虽到stage3并触杆，但全因抬升不足和末段误差失败。parameter6新增唯一task通过是seed20260925/9402，仍因穿透门失败。全部失败及阶段/接触曝光均已保留。
