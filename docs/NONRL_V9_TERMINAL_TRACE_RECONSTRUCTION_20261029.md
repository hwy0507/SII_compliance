# 三特化场景终态时间遥测重建

本轮是progress：新增只读重建工具`tools/audit_special_terminal_trace_20261029.py`，在原108继续运行期间，使用v9 teacher六条train00/validation08保存状态补查完成时间证据。没有改采集数据、模型、任务判据或绑定运行源码，没有新物理积分/拟合/测试选模。

## 真实核验结果

工具核scene/trajectory/execution hash及实际执行源码tar中的终态判据来源与当前源码一致，再逐帧`mj_forward`重建派生几何/速度/接触；**不调用mj_step**。primitive保留原lift>0.10、末10帧物体速度<0.02、均值位置误差<0.015、最终stage及原invalid/upstream/cup veto；rod panel四阶段、ball六阶段保持。corner重建原桌顶接触历史、几何投影、底面差≤0.020、速度≤0.08、gripper command≥0.050、原margin门。末帧布尔值必须与原成功/放置字段一致，否则拒绝。

| 场景 | train00连续终态后缀起点 | validation08后缀起点 | 连续采样后缀时长train/val |
|---|---:|---:|---:|
| 带挡板棍推 | 8.88s | 8.92s | 11.12/11.08s |
| 自由球撞 | 13.36s | 13.96s | 16.64/16.04s |
| 厚桌角 | 11.88s | 11.96s | 1.12/1.04s |

六条末帧原判据均精确布尔一致；corner底面位置逐值相等、最小margin误差<5e-15m，速度误差<4e-20m/s。五个连续后缀边界检查（全失败/全成功/中途断开/最后失败/单帧成功）通过。源绑定前首版结果保留为历史，后续以`TEACHER_SIX_SOURCE_BOUND.json`为准。

## 与正式SPT的边界

本工具输出的是**原终态判据在保存采样点上的连续后缀**，不是正式完成时刻或SPT。它既没有增加一个让实验更容易过的任务，也没有从release、retreat、回合总时长猜完成时间。25Hz保存状态不能证明两个采样点间所有物理子步持续成功；primitive的invalid/upstream采用原整回合veto而不能恢复中途接触时刻；corner的历史top首次接触采用原记录，不从稀疏帧猜测。

冻结office统计以13个连续样本（至少0.48s采样跨度，既有统计约定0.52s保持）确定完成时刻。正式新场景矩阵需要在看学生结果前明确同样保持约定如何作用于各原终态门，再按该门的确认采样时刻计时。不能把本表的后缀起点直接填入正式SPT。corner placement判据也不能代替scenario contact/safety资格或office Strict。机器合规独立统计，无人体接触的舒适度为NA，扰动力矩代理单列。

工具兼容后继18开发配对的保存结构，但目前未对未完成学生运行执行，不改变v3等待器登记。三特化的最终主矩阵仍须独立未见条件、最终模型冻结、Task/Strict、完整子步安全审计和共同T_ref；Goal active。
