# 配对PPO三训练seed：同六fixture部署

新24条learned和1条nominalparity重新读取raw；旧12条learned及6条共享nominal复用固定hash审计。42条独特性能记录，额外parity不进均值；另列旧zero7六条作直接动作消融。

先对每个训练seed的六fixture求均值，再描述三个seed均值的离散程度。失败始终计入分母6；不把18fixture当18独立训练重复。

| 模式 | 训练seed | task /6 | strict /6 | waypoint RMSE mm | 峰矩 Nm | 峰速 m/s | 末帧距共同目标 mm | 末6秒共同目标RMSE mm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| parameter6 | 20260923 | 1 | 0 | 155.2050 | 38.9733 | 0.150369 | 89.3985 | 94.4518 |
| parameter6 | 20260924 | 0 | 0 | 167.4313 | 38.7332 | 0.163656 | 90.6573 | 108.0323 |
| parameter6 | 20260925 | 1 | 0 | 144.6466 | 39.1508 | 0.143829 | 51.6313 | 48.1185 |
| direct7 | 20260923 | 0 | 0 | 135.9822 | 38.3292 | 0.156100 | 98.5446 | 97.8839 |
| direct7 | 20260924 | 0 | 0 | 49.6452 | 33.4572 | 0.104325 | 222.2833 | 222.2844 |
| direct7 | 20260925 | 0 | 0 | 225.1947 | 33.3463 | 0.047623 | 252.6627 | 252.6963 |

| 模式 | 三seed waypoint均值 ± SD mm | 峰矩均值 ± SD Nm | 峰速均值 ± SD m/s | task率均值 ± SD | strict率均值 ± SD |
|---|---:|---:|---:|---:|---:|
| parameter6 | 155.760974 ± 9.310115 | 38.952397 ± 0.171136 | 0.152618 ± 0.008249 | 0.111111 ± 0.078567 | 0.000000 ± 0.000000 |
| direct7 | 136.940676 ± 71.670986 | 35.044239 ± 2.323292 | 0.102683 ± 0.044301 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 |

SD是三个训练seed均值的总体标准差；仅描述小预算复验，不宣称显著性、收敛或泛化。共享nominal无独立训练seed，旧ESN/MLP单模型不赋予此SD。

## 全部learned回合与失败

| 模式 | 训练seed | fixture | task/strict | stage | 实际s | 杆触发/接触s | task失败项 | 接触/上游失败项 |
|---|---:|---:|---|---:|---:|---|---|---|
| direct7 | 20260923 | 9400 | False/False | 3 | 24.00 | True/0.029050 | 末10帧当前waypoint误差≥15mm | 杆接触≤0.3s |
| direct7 | 20260923 | 9401 | False/False | 3 | 24.00 | True/0.095850 | 末10帧当前waypoint误差≥15mm | 杆接触≤0.3s |
| direct7 | 20260923 | 9402 | False/False | 3 | 24.00 | True/4.524000 | 末10帧当前waypoint误差≥15mm | 最大非目标物穿透≥0.2mm |
| direct7 | 20260923 | 9403 | False/False | 3 | 24.00 | True/4.613900 | 末10帧当前waypoint误差≥15mm | 接触子门通过 |
| direct7 | 20260923 | 9404 | False/False | 3 | 24.00 | True/18.790650 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm | 杆释放间隔≤2s或无杆接触；末端杆间隙≤2mm；最大非目标物穿透≥0.2mm |
| direct7 | 20260923 | 9405 | False/False | 3 | 24.00 | True/19.388800 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm | 杆释放间隔≤2s或无杆接触；末端杆间隙≤2mm；最大非目标物穿透≥0.2mm |
| parameter6 | 20260923 | 9400 | False/False | 3 | 24.00 | True/1.308000 | 末10帧当前waypoint误差≥15mm | 接触子门通过 |
| parameter6 | 20260923 | 9401 | False/False | 3 | 24.00 | True/1.604600 | 末10帧当前waypoint误差≥15mm | 最大非目标物穿透≥0.2mm |
| parameter6 | 20260923 | 9402 | False/False | 3 | 24.00 | True/13.639000 | 末10帧当前waypoint误差≥15mm | 杆释放间隔≤2s或无杆接触；末端杆间隙≤2mm；最大非目标物穿透≥0.2mm |
| parameter6 | 20260923 | 9403 | True/False | 3 | 24.00 | True/1.863200 | 通过 | 最大非目标物穿透≥0.2mm |
| parameter6 | 20260923 | 9404 | False/False | 3 | 24.00 | True/10.156100 | 末10帧当前waypoint误差≥15mm | 最大非目标物穿透≥0.2mm |
| parameter6 | 20260923 | 9405 | False/False | 3 | 24.00 | True/14.266200 | 末10帧当前waypoint误差≥15mm | 杆释放间隔≤2s或无杆接触；末端杆间隙≤2mm；最大非目标物穿透≥0.2mm |
| direct7 | 20260924 | 9400 | False/False | 1 | 24.00 | False/0.000000 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm；未到loaded-lift阶段3 | 杆接触≤0.3s；杆释放间隔≤2s或无杆接触 |
| direct7 | 20260924 | 9401 | False/False | 1 | 24.00 | False/0.000000 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm；未到loaded-lift阶段3 | 杆接触≤0.3s；杆释放间隔≤2s或无杆接触 |
| direct7 | 20260924 | 9402 | False/False | 1 | 24.00 | False/0.000000 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm；未到loaded-lift阶段3 | 杆接触≤0.3s；杆释放间隔≤2s或无杆接触 |
| direct7 | 20260924 | 9403 | False/False | 1 | 24.00 | False/0.000000 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm；未到loaded-lift阶段3 | 杆接触≤0.3s；杆释放间隔≤2s或无杆接触 |
| direct7 | 20260924 | 9404 | False/False | 1 | 24.00 | False/0.000000 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm；未到loaded-lift阶段3 | 杆接触≤0.3s；杆释放间隔≤2s或无杆接触 |
| direct7 | 20260924 | 9405 | False/False | 1 | 24.00 | False/0.000000 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm；未到loaded-lift阶段3 | 杆接触≤0.3s；杆释放间隔≤2s或无杆接触 |
| parameter6 | 20260924 | 9400 | False/False | 3 | 24.00 | True/1.208800 | 末10帧当前waypoint误差≥15mm | 接触子门通过 |
| parameter6 | 20260924 | 9401 | False/False | 3 | 24.00 | True/1.418400 | 末10帧当前waypoint误差≥15mm | 最大非目标物穿透≥0.2mm |
| parameter6 | 20260924 | 9402 | False/False | 3 | 24.00 | True/6.642650 | 末10帧当前waypoint误差≥15mm | 最大非目标物穿透≥0.2mm |
| parameter6 | 20260924 | 9403 | False/False | 3 | 24.00 | True/10.757650 | 末10帧当前waypoint误差≥15mm | 末端杆间隙≤2mm；最大非目标物穿透≥0.2mm |
| parameter6 | 20260924 | 9404 | False/False | 3 | 24.00 | True/9.681250 | 末10帧当前waypoint误差≥15mm | 最大非目标物穿透≥0.2mm |
| parameter6 | 20260924 | 9405 | False/False | 3 | 24.00 | True/17.258650 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm | 杆释放间隔≤2s或无杆接触；末端杆间隙≤2mm；最大非目标物穿透≥0.2mm |
| direct7 | 20260925 | 9400 | False/False | 3 | 24.00 | True/0.383950 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm | 接触子门通过 |
| direct7 | 20260925 | 9401 | False/False | 3 | 24.00 | True/0.354750 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm | 末端杆间隙≤2mm |
| direct7 | 20260925 | 9402 | False/False | 3 | 24.00 | True/0.960500 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm | 接触子门通过 |
| direct7 | 20260925 | 9403 | False/False | 3 | 24.00 | True/0.429600 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm | 接触子门通过 |
| direct7 | 20260925 | 9404 | False/False | 3 | 24.00 | True/1.078900 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm | 接触子门通过 |
| direct7 | 20260925 | 9405 | False/False | 3 | 24.00 | True/6.357200 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm | 末端杆间隙≤2mm |
| parameter6 | 20260925 | 9400 | False/False | 3 | 24.00 | True/1.053350 | 末段物体速度≥20mm/s或不可计算；末10帧当前waypoint误差≥15mm | 接触子门通过 |
| parameter6 | 20260925 | 9401 | False/False | 3 | 24.00 | True/4.078050 | 末10帧当前waypoint误差≥15mm | 接触子门通过 |
| parameter6 | 20260925 | 9402 | True/False | 3 | 24.00 | True/1.849850 | 通过 | 最大非目标物穿透≥0.2mm |
| parameter6 | 20260925 | 9403 | False/False | 3 | 24.00 | True/2.756650 | 末段物体速度≥20mm/s或不可计算；末10帧当前waypoint误差≥15mm | 最大非目标物穿透≥0.2mm |
| parameter6 | 20260925 | 9404 | False/False | 3 | 24.00 | True/7.918000 | 末10帧当前waypoint误差≥15mm | 最大非目标物穿透≥0.2mm |
| parameter6 | 20260925 | 9405 | False/False | 3 | 24.00 | True/7.684650 | 末10帧当前waypoint误差≥15mm | 最大非目标物穿透≥0.2mm |

parameter6逐fixture相对训练nominal、direct7相对旧zero7的差值，以及每seed先聚合的差值保存在JSON。不同阶段及触杆曝光不能仅以低waypoint误差比较。共同末帧距离与绝对(18,24]s150帧RMSE不可混为一个指标；任何安全短回合均保留，末6秒量不补造。

旧报告SHA256 `c417038bcc43c79ed52925cb942a7993b2eeb56595a9b731f92167adaf44b011`；新plan SHA256 `c094ca89faa946e156843aa366592b43bc943f07c89f932c990d6273c6a5f467`。670项输入/工具hash保存在JSON。
