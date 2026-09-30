# Canonical48 PPO8192：训练前诊断与固定预算协议

在新训练启动前写入。本轮只增加直接 PPO 从零训练预算至8192步，不用演示、不warmstart，不根据新增validation结果改reward或超参数。640步试验保持原样作为对照。

## Train-only诊断与当前原VMC对照

诊断证据：`outputs/canonical48_ppo_diagnosis_20260923_r1/diagnosis.json`；原VMC原始24秒结果在同目录 `vmc_control/`。没有读取新validation表现用于做本轮设计选择。

| rod/train运行 | lift m | 末端误差 m | 最后物体速度最大值 m/s | 严格task判定的主要失败项 |
|---|---:|---:|---:|---|
| 零动作 | 0.06046 | 0.18787 | 0.000202 | lift≤0.10且末端误差≥0.015 |
| 冻结PPO640 | 0.06740 | 0.18657 | 0.000176 | lift≤0.10且末端误差≥0.015 |
| PPO640唯一完整随机训练episode | 0.25254 | 0.00715 | 0.030878 | 物体速度≥0.02 |
| 当前原VMC，同恢复fixture | 0.20614 | 0.05239 | 0.019538 | 末端误差≥0.015 |

以上均完成600步且无invalid/upstream，最终保持双指抓持。物体速度按原task定义，从最后10个object_position样本计算9个差分速度的最大范数。随机训练样本实际达到lift与位置误差条件，但仍未达到终端静止要求；它不是完全无法探索到抬起动作。零动作/冻结PPO640的rod接触持续至24s，随机训练样本的rod最后接触为9.8476s；原VMC也接触至24s，任务失败，不能沿用原归档teacher accepted标签。

原VMC调用原 `run_panel_push_20260920.py`，不带model参数、`mixture=0`，实查teacher_called=true、48D contract，rod_height显式恢复0.65m，scene和physical_panels与归档相同。结果task/gate均false、最大穿透0.150568mm、峰值外部合力217.108N、末端误差52.39mm、运行112.57s，进程峰值RSS0.48GiB。这再次说明“静态归档配置重建”不能等价于“历史teacher runtime完全重现”。

Reward不是全稀疏：600步position项分别为随机训练−5.6468、零动作−12.1811、冻结PPO640−16.7907；phase奖励均+1.5。唯一完整随机训练episode的终端奖励为0；terminal success信号的确尚未被看到。随机训练episode总reward−4.5349优于确定性PPO640的−15.7449，不能用一个episode和30次更新推断策略已收敛。

初始Gaussian actor在标准化零观测上的slowdown均值0、σ=exp(−2)=0.13534，clip到[0,1]后理论约50%落在0、均值约0.05399。实际随机训练slowdown均值0.06504、44.33%为0、没有值为1；冻结PPO640均值0.02538、14.17%为0、没有值为1。此非对称探索是标准SB3 Gaussian+Box clipping的参数化性质，0本来就是“无slowdown”，没有发现action域错误或完全停止nominal的饱和现象，因此不改actor分布。

时序审查：非终端reward使用前一action物理执行后、下一task更新后的原48D观测；phase/terminal只用于reward，不进actor/value。最后一步使用真实post-step终端标签，密集项复用40ms前最后actor观测且不bootstrap；这是现有明确的有限时域近似，未证明它导致失败。本轮保持该reward和termination定义，避免改变预算比较的含义。Reward本身不惩罚全部严格物理gate，reward更高仍不能替代gate通过。

## 预声明训练与评估

- 8192步，从随机初始化训练，seed仍20260923；不是加载640步checkpoint续训。
- 同一rod训练、同一front验证；fixture来自manifest各split第一条，配置、reset、48D/7D、WBC、安全、reward均不变。
- PPO MLP128×128，n_steps64、batch64、epochs3、lr3e−4、gamma.995、GAE.95、log_std_init−2，与640试验相同。
- 正常预算包含13个完整600步episode及392步partial；partial保留，不当成完整评估。
- 固定最后checkpoint评估，不按validation挑选模型。每2048步保存策略、optimizer和train-only normalization，保存发生在完整rollout更新之后；这些中间checkpoint用于防中断，不据此选择最好val。
- 8192步结束后重新加载最后checkpoint，冻结normalization，分别对train/validation评估零动作与PPO。所有失败保留。
- 对比新训练前640个actor observations/actions与旧训练前缀，记录误差及有限容差结果；不为达成相等修改训练。
- CPU affinity2核、单环境、单线程、nice10、CUDA15%，RSS≤7GiB且系统available≥2.5GiB守卫，45分钟timeout；若超时保留已保存checkpoint和失败证据，不声明完整结果。

输出目录预定：`outputs/canonical48_ppo_8192_20260923_r1/`。运行命令：

```bash
/home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python \
  tools/run_canonical48_ppo_20260923.py \
  --output outputs/canonical48_ppo_8192_20260923_r1 \
  --steps 8192 --seed 20260923 --device cuda --checkpoint-every 2048
```

环境桥SHA256保持 `6951e28a8740221796142f686b3df056671462567ba553784198b1ae7380ce38`。训练工具仅增加固定间隔checkpoint及对应元数据，SHA256 `bcf7bf80f4df99a9cdeb1109283255dffc31a10665b4c2c340062d57f8c5b1df`。完整代码/资源hash会再次写入本轮manifest。协议起始状态为“待启动”；实际PID、起止、进度与结果以下方更新或输出中的progress/COMPLETE为准。

## 实际执行更新

启动后进一步固定源码隔离。早期 `canonical48_ppo_8192_20260923_r1` 在最后记录416步时人工停止，原因是将后续reset改为只读独立源码快照，算法、reward、种子没有改变。原目录完整保留，`INTERRUPTED.json` 明确不计为完成种子或结果；最后进度记录之后的精确执行步数不可恢复。

实际长跑为 **`outputs/canonical48_ppo_8192_20260923_r2/`**，Python PID47496，timeout父PID47495。源码目录 **`outputs/canonical48_ppo_source_snapshot_20260923_r2/`** 完整复制scripts/tools/assets/configs并移除写权限，训练从该目录的独立entrypoint加载。所有episode reset都读snapshot中的bridge、panel、primitive、WBC与安全实现；后续共享目录改动不影响该run。资产路径仍为已固定hash的canonical_rl_assets目录。此后不再因源码隔离重启，也不改运行中的reward。

224步时RSS2.25GiB、系统available9.36GiB；最新实时状态读取r2/progress.json，不能仅凭本段PID判断进程仍运行。每2048步checkpoint位于r2/checkpoints，最终结果必须以r2/COMPLETE.json为准。

前640步可复现性检查工具：`tools/compare_canonical48_prefix_20260923.py --old outputs/canonical48_ppo_pilot_20260923_r1 --new outputs/canonical48_ppo_8192_20260923_r2`。采用预声明atol=rtol=1e−6，报告逐元素相等与误差，不以匹配结果选模或改训练；新run至少归档前两个完整episode后才能读取完整640步。

## 固定预算完成结果

8192-r2已正常结束，`COMPLETE.json` 确認总耗时 **1548.22s（25.80min）**，真实8192 transitions、384次优化更新，13完整600步训练episode加392步partial。2048/4096/6144/8192周期checkpoint全部存在，最终策略与8192周期模型hash一致；没有根据验证替换为中间checkpoint。最终RSS2.32GiB、系统available9.32GiB。

`PREFIX_COMPARISON.json`：最初640步observations/actions/phase metadata与旧640试验逐元素完全相等（误差0），不仅通过1e−6容差。`TRAINING_REPORT.json`：固定预算核算通过，全部snapshot源码hash与启动manifest相同，13个完整随机训练episode中1个task成功（episode_00001），0个invalid；终端成功奖励确实在更长训练中出现。其余许多episode虽然抬起并到达目标附近，但未满足终端稳定/误差门。不能将这些随机训练指标替代冻结policy评估。

| 当前24s冻结评估 | task / gate | final stage | 外部峰值合力 N | 最大外部穿透 mm | 末端误差 mm | reward |
|---|---|---:|---:|---:|---:|---:|
| rod/train zero | 否 / 否 | 3 | 219.224 | 0.150568 | 187.870 | −11.1149 |
| rod/train PPO8192 | 否 / 否 | 1 | 976.290 | 0.212330 | 294.149 | −21.8829 |
| front/validation zero | 是 / 是 | 3 | 87.698 | 0.000843 | 7.068 | 3.2267 |
| front/validation PPO8192 | 否 / 否 | 0 | 1138.242 | 0.074220 | 94.427 | −12.2661 |

四条均完成24s，没有执行错误；PPO的invalid/upstream标志均false，但这并不代表通过严格gate：rod穿透超过0.2mm，两个fixture都未抬起。两条零动作对照与640试验数值完全一致。8192固定最终策略相对640在本次确定性评估中退化，没有证据支持“只扩大该配置训练预算就改善baseline”。随机探索轨迹和确定性mean-policy部署之间的差异需要后续单独诊断；本轮不改评价规则、不换随机策略、不挑中间checkpoint。

冻结模型SHA256：`611323476636c3a398bc465b11c4bf51c0dc6fab280fe9067c7babc66901f16e`；normalizer SHA256：`55fe4881e585d5f48dff32cf467a07ba29c2576a48654bf33516990866366b56`。normalization在四评估期间保持完全冻结，60项静态重建检查全部通过。全trace与失败保留，报告副本在 `docs/evidence/canonical48_8192_20260923/`。

Lineage结论见 [CANONICAL48_TEACHER_LINEAGE_20260923.md](CANONICAL48_TEACHER_LINEAGE_20260923.md)：已找到hash匹配历史源代码，关键observer/WBC/safety/VMC代码与当前相同；初始q已有约3.94e−8差并在接触中放大，但完整历史数值环境未知，不能断言硬件唯一原因或RL任务不可学。本机结果不并入DGX三指标比较表。

部署准备见 [CANONICAL48_PPO_DEPLOYMENT_20260923.md](CANONICAL48_PPO_DEPLOYMENT_20260923.md)：纯48→7适配器已就绪；8192最终checkpoint本机CPU对原GPU600帧动作maxerr1.1921e−7，通过1e−6容差。后续在DGX同平台配对zero/VMC及冻结ESN/MLP前，不能宣称完成公平闭环方法比较。
