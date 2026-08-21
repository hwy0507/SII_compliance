# Paper-MPC 随机化冲击工况结果（服务器，2026-08-21）

本实验在五个评估 seed 上对棒击/球击 fixture 做了匹配的、可复现的物理参数扰动：

```text
rod_stroke_m      ±0.0020 m
rod_height_m      ±0.0015 m
rod_start_time_s  ±0.0150 s
```

同一 seed/scenario 的扰动对裸机、ESN、MLP、VMC 完全相同；木板场景保持固定。每条 raw rollout 都记录了实际 `fixture_parameters`，可从服务器结果 JSON 复核。服务器输出为：

```text
results_baseline_jitter_5seeds_20260821.json
results_esn101_jitter_5seeds_20260821.json
results_esn202_jitter_5seeds_20260821.json
results_esn303_jitter_5seeds_20260821.json
results_mlp_jitter_5seeds_20260821.json
results_vmc_jitter_5seeds_20260821.json
```

## 结果

| 方法 | 总成功率 | 棒击 | 球击 | 木板 | 棒/球抓取误差均值 |
|---|---:|---:|---:|---:|---:|
| PaperMPC 裸机 | 26/50 | 16/20 | 0/20 | 10/10 | 24.76 mm |
| ESN-101 | **50/50** | 20/20 | 20/20 | 10/10 | 11.04 mm |
| ESN-202 | **50/50** | 20/20 | 20/20 | 10/10 | 10.42 mm |
| ESN-303 | **50/50** | 20/20 | 20/20 | 10/10 | **9.30 mm** |
| MLP h128-s2 | 48/50 | 20/20 | 18/20 | 10/10 | 23.70 mm |
| VMC（无噪声阶段选优配置） | **50/50** | 20/20 | 20/20 | 10/10 | 9.40 mm |

分场景均值如下：

```text
                 rod at-grasp    ball at-grasp    board at-grasp
PaperMPC none       20.65 mm        28.87 mm         12.55 mm
ESN-101             12.63 mm         9.46 mm          7.00 mm
ESN-202             12.86 mm         7.97 mm          7.14 mm
ESN-303             11.47 mm         7.13 mm          7.63 mm
MLP                 27.62 mm        19.78 mm          7.79 mm
VMC                  8.80 mm        10.00 mm          6.02 mm
```

## 对 proposed 的正确解释

这批结果不支持“ESN 全面击败 VMC”。VMC 仍然是绝对误差最强的解析基线之一，尤其在木板和棒击上；ESN-303 在随机化棒/球平均误差上略优于本次固定配置 VMC，但三个 ESN seed 的平均值仍略高于 VMC。

支持的论文主张是：ESN 在未重新调参的情况下，对随机化冲击工况保持 `3/3 reservoir seeds × 50/50` 成功；它把棒/球误差从裸机约 24.76 mm 降到 9.30–11.04 mm，并且不需要为 rod/ball/board 分别选择刚度。因而 proposed 的核心价值是跨工况、免手工调参、可从教师轨迹蒸馏并可扩展接触历史，而不是在每个指标上压过经过场景调参的解析控制器。
