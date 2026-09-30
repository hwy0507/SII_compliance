# 多seed25job完整归档传输审计

2026-09-25（Asia/Shanghai），先确认DGX COMPLETE/FINAL均为25条、无FAILED、0执行错误、0安全短回合，driver565765和全部本任务worker均退出。目标本机目录在首次传输前不存在。没有重跑仿真、删除文件或覆盖其它证据。

- 来源：`arm1@192.168.31.70:/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/paired_multiseed_six_fixture_20260925_r1/`
- 本机：`outputs/paired_multiseed_six_fixture_20260925_r1_archive/`
- 首次命令：`rsync -a --info=stats2 <来源> <本机>`，退出码0。
- 698项（582个普通文件、116目录），总计1,712,652,991 bytes；582文件全传输，删除0。
- 随后命令：`rsync -a --checksum --dry-run --itemize-changes --info=stats2 <来源> <本机>`，退出码0，无itemized差异；新建0、删除0、待传输普通文件0、待传输字节0。
- 此审计记录放在复制归档外，不向证据树加入文件。后续离线报告使用归档内冻结工具，并设置`PYTHONDONTWRITEBYTECODE=1`，防止在证据树生成cache。

| 完整归档文件 | SHA256 |
|---|---|
| COMPLETE.json | `2bc589a81e86cf70df4b7b62f5e28bd5e6e4fb84fddf1c79668d990095ed2ed8` |
| FINAL_RESULT.json | `4f05071eba3e6d561703407c1f5c4c854491635dab771ac90210fd0218746458` |
| frozen_plan.json | `c094ca89faa946e156843aa366592b43bc943f07c89f932c990d6273c6a5f467` |
| NOMINAL_REUSE_PARITY.json | `cb083cebf17f791ea565736e988e286eb134662c84b9bab07007597e65ba3fde` |

本轮25条包括24条新learned评估和1条额外nominal9400 parity。旧训练seed12条learned、共享nominal六条绑定旧18报告复用；42条独特性能记录，parity不进均值。direct7旧zero7六条另作已审计背景对照，不混入42条计数。

离线报告命令（在benchmark根运行；只读仿真数据，仅输出docs报告）：

```text
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
/home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python
outputs/paired_multiseed_six_fixture_20260925_r1_archive/source_snapshot/tools/report_paired_multiseed_deployment_20260925.py
--archive outputs/paired_multiseed_six_fixture_20260925_r1_archive
--old-report docs/PAIRED_SIX_FIXTURE_RESULTS_20260924.json
--old-archive outputs/paired_six_fixture_validation_20260924_r1_archive
--output docs/PAIRED_MULTISEED_SIX_FIXTURE_RESULTS_20260925
```

三训练seed及逐回合原门复算见[结果报告](../../PAIRED_MULTISEED_SIX_FIXTURE_RESULTS_20260925.md)。该结果不会将旧12条learned称为本次重新读取raw，也不会把每个seed六fixture当六次独立训练。
