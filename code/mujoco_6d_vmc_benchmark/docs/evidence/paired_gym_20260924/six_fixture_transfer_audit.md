# 六条件18条评估：归档传输核对

2026-09-25（Asia/Shanghai）将已完成的DGX输出只读取回，目标目录在传输前不存在。没有重新运行仿真，没有修改源归档或覆盖已有不同证据。

- 来源：`arm1@192.168.31.70:/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/paired_six_fixture_validation_20260924_r1/`
- 本机：`outputs/paired_six_fixture_validation_20260924_r1_archive/`
- 首次命令：`rsync -a --info=stats2 <来源> <本机>`；退出码0。
- 464个普通文件、84个目录，总计1,249,993,338 bytes；464个文件全部传输，删除0。
- 随后命令：`rsync -a --checksum --dry-run --itemize-changes --info=stats2 <来源> <本机>`；退出码0，无任何itemized差异；新建0、删除0、待传输普通文件0、待传输字节0。
- 该核对证明源树全部文件在本地逐内容一致；不使用`--delete`，本次目标原先为空。此记录保存在树外，不改变复制归档。

| 已复制文件 | SHA256 |
|---|---|
| COMPLETE.json | `2e93af556d011f52c9cb24795cb04d15d971492c89a8a65af8c05d8879a3584e` |
| FINAL_RESULT.json | `93ae8857a0bc0324c8783f66bb7c82411c1a4ef49da5565566ff27733d271b58` |
| frozen_plan.json | `8c42a62308007d210051f19dbe45b9a878df19450ca66b4545b63ff14d87864c` |
| execution_manifest.json | `40491bb0194f29205a65033b400e0b1a444109bdea6736355a33ce853ad668c5` |

COMPLETE记录18条、task(parameter6/direct7/nominal_train_vmc)=1/0/1、gate=0/0/0，安全短回合0，source_unchanged=true。数值与门槛的进一步独立复算见[配对六条件结果](../../PAIRED_SIX_FIXTURE_RESULTS_20260924.md)。新18条重新读取raw；旧48条复用固定hash的已审计JSON，不声称66条都在本次重新读取raw。
