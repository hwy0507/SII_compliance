# 四路扩容后的小batch训练吞吐诊断

当前batch256、UTD1、四路各12worker仍未达到GPU50%利用率。本轮外部采样显示：
**在测量窗口中，物理采样和周期尾部并行度对吞吐构成限制；没有证据把低利用率主要归因于
Polyak更新。** 当前训练、奖励和物理控制合同均保持，未部署性能候选。

## 测量范围及第一次测量的干扰

四个learner按PID/启动时间/命令核对，额外观察一个Admittance采样器
（active_long_train_0000）。py-spy使用线程标识，单独识别MainThread；同步读取/proc CPU
时间、实际PROGRESS和cgroup CPU计数，不把CUDA辅助线程的空Python栈算成主线程空闲。
收集器和profiler绑定保留CPU53；没有启动额外仿真或optimizer更新。

第一次50Hz采样出现四learner约13–14秒滞后警告，程序实际运行74.24秒。尽管返回code0，
这仍是测量干扰，v1完整保留，不作为精确耗时或正常吞吐依据。初步在v1看到环境大量等待
动作，并考虑Polyak优化；低频复测改变了这一判断。没有将该候选写入live代码。

第二次降到10Hz，五个目标均code0/Errors0，**无采样滞后警告**；各MainThread599个样本。
程序总时间64.27秒（含收尾），/proc首末观测间隔59.05秒。每路训练吞吐以各自PROGRESS
实际时间差计算，不直接除以名义60秒。仍有采样开销，不能称完全无扰动测量。

## 低频复测结果

下表比例以明确识别的主线程样本为分母；更新/target/等待等为inclusive分类，不能相加。
CPU占用以一个逻辑核为100%；这些是该窗口观测，不是全阶段平均。

| Learner | 采样器数，首→末 | 等待输入 | learner update | target更新 | 进程CPU | transition/s |
|---|---:|---:|---:|---:|---:|---:|
| Direct | 5→0 | 78.80% | 12.85% | 1.00% | 16.51% | 9.66 |
| Impedance | 12→12 | 49.92% | 39.73% | 3.51% | 47.00% | 30.79 |
| Admittance | 12→12 | 45.58% | 43.07% | 3.84% | 48.71% | 31.93 |
| VMC | 6→6 | 65.78% | 27.55% | 2.84% | 26.91% | 17.47 |

Direct/VMC正处周期尾部，不能把它们的低吞吐归因于算法较慢。Impedance/Admittance保持
12个worker时也有大量selector等待。四learner在窗口分别真实增加544/1818/1885/1032步
及相同数量的更新，没有因观察停止训练。

被采样的Admittance环境CPU占用93.61%，主线程样本93.32%位于_physics_step调用内，
等待stdin动作约5.01%。其中mj_step调用所在行占23.37%，world_step中的接触统计、
物体/机器人几何属性查询和其他遥测也占有可见比例。这里的23.37%包含原生调用期间
Python栈停留，不是CUDA kernel时间，也不是独立的MuJoCo精确计时。

容器cpu.max为5500000/100000，即55核配额；本窗口cgroup平均消耗约34.33核，
新增节流period/usec均0。当前证据不支持CPU配额节流是该窗口的限制；周期尾部空槽、
单worker物理循环和CPU开销仍可限制GPU输入供给。一次环境样本不能外推到所有条件。

## 后续决策与保护

优先调查采样热循环中静态几何属性访问/接触遥测和周期尾部空槽，任何候选都必须独立验证
控制输出、物理轨迹和安全统计等价后，才在另行登记的安全边界考虑部署。
不根据有滞后的v1优先实施Polyak优化，也不为占用率扩大batch/UTD或修改dt。
本轮未准备或部署训练性能修改，原六周期正式阶段和1/3/5完整周期审计继续。

实际source_train16的780个source和24个parameter文件hash重新核验通过。
物理/MJB、actor输入、公共filter、执行器限制、gate、奖励和原训练协议均未修改。
这项诊断解释当前吞吐限制，不是GPU50%达标、加速效果、收敛或最终ESN比较结果。

集群SSD根 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl` 下：

- `runs/FRESH_SMALL_BATCH_PROFILE_V1.json`、`runs/fresh_small_batch_profile_v1/`：高频有滞后记录和限制说明。
- `runs/FRESH_SMALL_BATCH_PROFILE_V2.json`、`runs/fresh_small_batch_profile_v2/`：低频profiles、CPU/进度遥测、REVIEW及最终SCIENTIFIC_REVIEW。
- `runtime/fresh_small_batch_profile_v1/`、`runtime/fresh_small_batch_profile_v2/`：只读收集与核验代码。

两次收集进程均已正常结束，不要重复启动；原四learner仍运行。原始speedscope/遥测留集群，
仓库JSON记录摘要、绝对路径和hash。初步工具REVIEW内的Polyak候选建议由最终
SCIENTIFIC_REVIEW的决策覆盖，未以初步建议修改任何正式训练。
