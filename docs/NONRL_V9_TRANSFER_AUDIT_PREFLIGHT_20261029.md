# v9实际scope回归的后处理入口与六指标预检

本轮progress：新增`tools/audit_v9_office_transfer_20261029.py`，用于实际由scope直接启动的v9组合迁移108；现有`audit_special_frozen108_20261028.py`顶层入口要求v8 preparation/handoff完成收据，不能伪造这些收据来给v9套用。新入口复用旧工具的逐回合`verify_episode`与`summaries`，保持独立子步复算、source/config/checkpoint/hash、actor/filter、Task/Strict、条件SPT及全回合分母规则。

## 冻结不变量与实际验证

- 真正scope `run-raa08b13eb33f4583ab899210958345fa.scope`，协调器PID1541733，运行`special_scene_frozen108_preparation_20261029_v8/tools/run_nonrl_spt_matrix_20261025.py`，使用v9模型锁与v9输出目录；这不表示v8 preparation对应v9完整执行。新工具按v9实际REGISTRATION、父protocol/conditions、完整source manifest、v9 FIT_AUDIT/数据/九checkpoint绑定验证，不改历史执行收据。
- 原helper首次兼容检查拒绝`Runtime changed`。原因是execution中的绝对Python字符串保留`SII_compliance/../.venv-sii-local-rl/bin/python`，parent登记为无`..`的同一路径。新适配器只归一化绝对路径的点段后比较，**不解析symlink**（不同venv可能共享同一base Python），随后给原helper传内存副本；不修改原文件。不同venv拒绝检查通过。
- 对第一条已完成ESN seed01/condition000执行完整`verify_episode`兼容核验通过：277600保存子步，RMSE112.2955mm、峰速0.4013m/s、峰矩60.4340Nm；原lift阶段global_penetration_exceeded_2mm失败保留。此为一条真实保存子步审计，不是完整108或动力学重积分。
- 新入口真实在途拒绝通过，0/107/109完成数拒绝通过；旧首版拒绝证据保留，当前使用LIVE_REFUSAL_V2。1103个后继v3登记源hash仍一致，新工具未改任何绑定文件。
- `check_special_metric_contract_20261029.py`对真实summary实现作九项手算合成检查：六指标全分母、快Task-only不设BOTH参考、接触时长加权、输入不变、五种非法BOTH时间拒绝、零成功SPT=NA、无接触NA、缺seed不静默排除、所有家族共用T_ref。合成数值没有冒称实验结果。

## 完整后处理命令（当前尚不能执行成功）

工作目录`code/mujoco_6d_vmc_benchmark`，原108 complete后再执行：

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=tools taskset -c 6 /home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python tools/audit_v9_office_transfer_20261029.py --root outputs/special_scene_frozen108_20261029_v9 --output outputs/special_scene_frozen108_20261029_v9/V9_TRANSFER108_AUDIT.json
```

实际完整108审计尚未运行；不能依据编译/拒绝/单条核验写完整通过。后续若发现其他schema或接口错误，保留拒绝并修复新入口，不回写原轨迹/门槛。旧图生成器要求v8审计schema，不能直接拿新v9结果冒充兼容，应在完整审计后适配展示。

最新原108为47完整/Task5/Strict0/BOTH0，SPT NA，scope active；唯一v3配对等待器active、PID1636845，仍无student execution。原失败全部保留。待18开发配对与train/val诊断后修复学习，再冻结未见三特化最终测试。此组合回归仅是迁移压力，主矩阵与Goal均未完成。
