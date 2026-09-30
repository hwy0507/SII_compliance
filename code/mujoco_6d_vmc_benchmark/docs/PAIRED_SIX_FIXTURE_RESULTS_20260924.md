# 同DGX配对RL与训练名义VMC：六条件结果

18条全部纳入，原raw子步误差/实际actuator矩/末端速度已独立复算；任务失败、strict失败和真实安全早停均保留。物理dt=50µs，表中各峰为每回合真实子步峰再对六条件取均值。

本次只重算新18条raw。旧48条从绑定SHA256的已审计JSON复用，没有在本次重新计算旧raw；可选11方法附表不能描述为66条全部重新审计。位置RMSE相对各策略状态机waypoint，不是共同时间连续目标，也不是共同最终目标距离。未到stage3时不能凭较低RMSE判断更优。

| 方法 | task | strict | waypoint RMSE均值 mm | 实际峰矩均值 Nm | 子步峰速均值 m/s | 完整24s |
|---|---:|---:|---:|---:|---:|---:|
| parameter6 | 1/6 | 0/6 | 155.2050 | 38.9733 | 0.150369 | 6/6 |
| direct7 | 0/6 | 0/6 | 135.9822 | 38.3292 | 0.156100 | 6/6 |
| nominal_train_vmc | 1/6 | 0/6 | 147.4929 | 38.5095 | 0.148874 | 6/6 |

parameter6的学习增益应相对nominal_train_vmc判断：两者使用完全相同的训练名义options，后者从reset起持续zero6，并非旧fixture名义VMC。direct7的学习增益相对原zero7判断；本工具只复用明确固定的旧审计JSON中同fixture、同MJB且共同配置检查通过的zero行。逐fixture差值保存在JSON，不把不同阶段的小waypoint误差当任务成功。

| 方法 | final stage分布 | 杆触发 | 杆有力接触 | 任意非目标物外接触 | 杆接触时长范围 s |
|---|---|---:|---:|---:|---:|
| parameter6 | {'3': 6} | 6/6 | 6/6 | 6/6 | 1.308000—14.266200 |
| direct7 | {'3': 6} | 6/6 | 6/6 | 6/6 | 0.029050—19.388800 |
| nominal_train_vmc | {'3': 6} | 6/6 | 6/6 | 6/6 | 1.263350—11.415900 |

有力接触沿用原审计>0.05N口径；非目标外接触包括桌面、护板和杆，排除抓取目标物。杆在loaded-lift阶段触发，未到阶段的策略可能没有实际经历杆扰动，即使其他外接触存在；因此名义相同fixture不等于实际相同扰动曝光。

| 方法 | seed | 时长 s | task/strict | final stage | 杆触发 | 杆时长 s | waypoint RMSE mm | 实际峰矩 Nm | 峰速 m/s | 非目标物外接触 |
|---|---:|---:|---|---:|---|---:|---:|---:|---:|---|
| parameter6 | 9400 | 24.00 | False/False | 3 | True | 1.308000 | 129.5579 | 39.0632 | 0.150609 | push_back_guard:0.0627s; push_rod_geom:1.3080s |
| parameter6 | 9401 | 24.00 | False/False | 3 | True | 1.604600 | 123.6685 | 41.0709 | 0.158535 | push_back_guard:0.1176s; push_rod_geom:1.6046s |
| parameter6 | 9402 | 24.00 | False/False | 3 | True | 13.639000 | 191.4728 | 39.4489 | 0.146229 | push_back_guard:1.5634s; push_front_guard:0.0022s; push_rod_geom:13.6390s |
| parameter6 | 9403 | 24.00 | True/False | 3 | True | 1.863200 | 118.0437 | 34.3870 | 0.146588 | push_back_guard:0.2876s; ws_push_back_guard_bracket:0.0338s; push_rod_geom:1.8632s |
| parameter6 | 9404 | 24.00 | False/False | 3 | True | 10.156100 | 177.1867 | 40.5135 | 0.148971 | push_back_guard:1.2796s; push_front_guard:0.3796s; push_rod_geom:10.1561s |
| parameter6 | 9405 | 24.00 | False/False | 3 | True | 14.266200 | 191.3001 | 39.3560 | 0.151282 | push_back_guard:1.7270s; push_front_guard:0.0405s; push_rod_geom:14.2662s |
| direct7 | 9400 | 24.00 | False/False | 3 | True | 0.029050 | 62.8344 | 39.2095 | 0.166935 | push_rod_geom:0.0291s |
| direct7 | 9401 | 24.00 | False/False | 3 | True | 0.095850 | 64.3814 | 41.3431 | 0.162863 | ws_push_back_guard_bracket:0.0086s; push_rod_geom:0.0958s |
| direct7 | 9402 | 24.00 | False/False | 3 | True | 4.524000 | 127.0843 | 39.9398 | 0.151701 | push_back_guard:0.3045s; ws_push_back_guard_bracket:1.4694s; push_rod_geom:4.5240s |
| direct7 | 9403 | 24.00 | False/False | 3 | True | 4.613900 | 131.6578 | 39.6522 | 0.151701 | push_back_guard:0.1286s; ws_push_back_guard_bracket:1.3057s; push_rod_geom:4.6139s |
| direct7 | 9404 | 24.00 | False/False | 3 | True | 18.790650 | 216.3345 | 34.7757 | 0.151701 | push_back_guard:0.0328s; ws_push_back_guard_bracket:17.7993s; push_rod_geom:18.7907s |
| direct7 | 9405 | 24.00 | False/False | 3 | True | 19.388800 | 213.6007 | 35.0552 | 0.151701 | push_back_guard:0.0526s; ws_push_back_guard_bracket:18.0530s; push_rod_geom:19.3888s |
| nominal_train_vmc | 9400 | 24.00 | False/False | 3 | True | 1.263350 | 126.9696 | 39.1475 | 0.144020 | push_back_guard:0.1598s; ws_push_back_guard_bracket:0.2051s; push_rod_geom:1.2634s |
| nominal_train_vmc | 9401 | 24.00 | False/False | 3 | True | 2.269300 | 131.5882 | 42.6277 | 0.150830 | push_back_guard:0.1096s; ws_push_back_guard_bracket:0.0755s; push_rod_geom:2.2693s |
| nominal_train_vmc | 9402 | 24.00 | True/False | 3 | True | 2.313250 | 124.7189 | 35.6006 | 0.148661 | push_back_guard:0.1568s; ws_push_back_guard_bracket:0.1660s; push_rod_geom:2.3133s |
| nominal_train_vmc | 9403 | 24.00 | False/False | 3 | True | 2.215950 | 136.2825 | 41.2276 | 0.148986 | push_back_guard:0.2546s; ws_push_back_guard_bracket:0.0151s; push_rod_geom:2.2160s |
| nominal_train_vmc | 9404 | 24.00 | False/False | 3 | True | 8.882100 | 173.5498 | 37.4077 | 0.152388 | push_back_guard:1.0519s; ws_push_back_guard_bracket:1.1760s; push_rod_geom:8.8821s |
| nominal_train_vmc | 9405 | 24.00 | False/False | 3 | True | 11.415900 | 191.8481 | 35.0458 | 0.148359 | push_back_guard:2.0924s; ws_push_back_guard_bracket:0.7320s; push_rod_geom:11.4159s |

## 逐回合任务失败解释：严格复算原门

原task要求物体抬升>100mm、最后10点物体速度峰<20mm/s、末10帧当前waypoint平均误差<15mm、物理有效、原主审计无上游接触、最终stage3及cup_safe。grasp_lift_success仅对应前两项。表中cup_safe等标志来自原JSON；cup_stable/cup_support_contact同时保存在JSON，但不把无杯场景的cup_support_contact=False另造为失败门。
最终目标残差使用冻结源码/原PANEL_CONFIG恢复的共同手端目标`[0.54, 0.0, 0.785]`m，仅作辅助解释，不替换waypoint主指标或任务门；没有抓物时手端接近目标也不能称任务完成。

| 方法 | seed | grasp_lift | invalid / 原upstream / cup_safe | 抬升 mm | 末段物速 mm/s | 当前waypoint末10均误差 mm | trace末帧距最终目标 mm | 原task失败项 |
|---|---:|---|---|---:|---:|---:|---:|---|
| parameter6 | 9400 | True | False / False / True | 181.850982 | 18.413744 | 70.474193 | 73.737750 | 末10帧当前waypoint误差≥15mm |
| parameter6 | 9401 | True | False / False / True | 166.281748 | 15.622797 | 85.379760 | 87.961505 | 末10帧当前waypoint误差≥15mm |
| parameter6 | 9402 | True | False / False / True | 124.242126 | 15.253347 | 142.085755 | 139.733569 | 末10帧当前waypoint误差≥15mm |
| parameter6 | 9403 | True | False / False / True | 247.882583 | 0.376946 | 4.283181 | 4.263836 | 无，原task通过 |
| parameter6 | 9404 | True | False / False / True | 182.947747 | 12.363737 | 84.498809 | 82.467332 | 末10帧当前waypoint误差≥15mm |
| parameter6 | 9405 | True | False / False / True | 115.623450 | 15.919488 | 150.593697 | 148.226871 | 末10帧当前waypoint误差≥15mm |
| direct7 | 9400 | True | False / False / True | 232.432491 | 0.275801 | 32.328635 | 32.284112 | 末10帧当前waypoint误差≥15mm |
| direct7 | 9401 | True | False / False / True | 229.784810 | 0.504368 | 34.598595 | 34.509518 | 末10帧当前waypoint误差≥15mm |
| direct7 | 9402 | True | False / False / True | 228.095053 | 4.161418 | 39.372280 | 38.961738 | 末10帧当前waypoint误差≥15mm |
| direct7 | 9403 | True | False / False / True | 234.936867 | 0.802430 | 30.973929 | 31.106833 | 末10帧当前waypoint误差≥15mm |
| direct7 | 9404 | False | False / False / True | 25.288973 | 0.773646 | 226.704361 | 226.660956 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm |
| direct7 | 9405 | False | False / False / True | 24.644845 | 0.070522 | 227.750230 | 227.744425 | 物体抬升≤100mm；末10帧当前waypoint误差≥15mm |
| nominal_train_vmc | 9400 | False | False / False / True | 182.423049 | 20.413362 | 68.132141 | 71.740570 | 末段物体速度≥20mm/s或不可计算；末10帧当前waypoint误差≥15mm |
| nominal_train_vmc | 9401 | True | False / False / True | 164.287386 | 14.417410 | 85.850653 | 88.111780 | 末10帧当前waypoint误差≥15mm |
| nominal_train_vmc | 9402 | True | False / False / True | 246.128877 | 0.452400 | 6.023062 | 5.994400 | 无，原task通过 |
| nominal_train_vmc | 9403 | False | False / False / True | 209.801399 | 31.074962 | 38.362374 | 43.220106 | 末段物体速度≥20mm/s或不可计算；末10帧当前waypoint误差≥15mm |
| nominal_train_vmc | 9404 | True | False / False / True | 215.083814 | 12.905136 | 41.722456 | 39.652905 | 末10帧当前waypoint误差≥15mm |
| nominal_train_vmc | 9405 | True | False / False / True | 137.009049 | 12.303097 | 119.723097 | 117.823157 | 末10帧当前waypoint误差≥15mm |

| 方法 | seed | 杆时长 s | 原释放间隔 s | 最终杆间隙 mm | 最大外部穿透 mm | 穿透门余量 μm | 原接触/上游门失败项 |
|---|---:|---:|---:|---:|---:|---:|---|
| parameter6 | 9400 | 1.308000 | 17.384300 | 13.947698 | 0.194667 | +5.333 | 无，接触子门通过（仍需task） |
| parameter6 | 9401 | 1.604600 | 17.347050 | 33.585271 | 0.211030 | -11.030 | 最大非目标物穿透≥0.2mm |
| parameter6 | 9402 | 13.639000 | -0.000000 | -0.000002 | 0.209635 | -9.635 | 杆释放间隔≤2s或无杆接触；末端杆间隙≤2mm；最大非目标物穿透≥0.2mm |
| parameter6 | 9403 | 1.863200 | 16.821000 | 66.901526 | 0.207742 | -7.742 | 最大非目标物穿透≥0.2mm |
| parameter6 | 9404 | 10.156100 | 4.223800 | 39.719843 | 0.208987 | -8.987 | 最大非目标物穿透≥0.2mm |
| parameter6 | 9405 | 14.266200 | 0.000900 | 0.000735 | 0.212595 | -12.595 | 杆释放间隔≤2s或无杆接触；末端杆间隙≤2mm；最大非目标物穿透≥0.2mm |
| direct7 | 9400 | 0.029050 | 20.111200 | 59.831984 | 0.148616 | +51.384 | 杆接触≤0.3s |
| direct7 | 9401 | 0.095850 | 20.030100 | 51.968584 | 0.160826 | +39.174 | 杆接触≤0.3s |
| direct7 | 9402 | 4.524000 | 11.760550 | 52.823927 | 0.204164 | -4.164 | 最大非目标物穿透≥0.2mm |
| direct7 | 9403 | 4.613900 | 10.510400 | 54.820733 | 0.171342 | +28.658 | 无，接触子门通过（仍需task） |
| direct7 | 9404 | 18.790650 | -0.000000 | -0.000101 | 0.228333 | -28.333 | 杆释放间隔≤2s或无杆接触；末端杆间隙≤2mm；最大非目标物穿透≥0.2mm |
| direct7 | 9405 | 19.388800 | -0.000000 | -0.000083 | 0.218744 | -18.744 | 杆释放间隔≤2s或无杆接触；末端杆间隙≤2mm；最大非目标物穿透≥0.2mm |
| nominal_train_vmc | 9400 | 1.263350 | 18.145800 | 15.337124 | 0.198470 | +1.530 | 无，接触子门通过（仍需task） |
| nominal_train_vmc | 9401 | 2.269300 | 16.551900 | 15.800499 | 0.204878 | -4.878 | 最大非目标物穿透≥0.2mm |
| nominal_train_vmc | 9402 | 2.313250 | 16.260900 | 69.808201 | 0.209852 | -9.852 | 最大非目标物穿透≥0.2mm |
| nominal_train_vmc | 9403 | 2.215950 | 16.225550 | 30.999328 | 0.202951 | -2.951 | 最大非目标物穿透≥0.2mm |
| nominal_train_vmc | 9404 | 8.882100 | 9.195350 | 50.323131 | 0.216333 | -16.333 | 最大非目标物穿透≥0.2mm |
| nominal_train_vmc | 9405 | 11.415900 | 5.630200 | 10.871646 | 0.209154 | -9.154 | 最大非目标物穿透≥0.2mm |

原panel门另要求杆时长>0.3s、计划结束时刻−杆末触>2s、最终杆间隙>2mm、所有非目标物最大穿透<0.2mm及杆无上游接触；原strict再要求所有非目标外物均无上游接触。释放间隔严格使用原代码的计划24s，即使安全提前终止也不改其公式；task中的物理失败仍阻止通过。穿透余量=200−峰深度(μm)，仅作连续解释，不放宽原门。
JSON保留所有原布尔标志、逐项重算结果、失败项、峰穿透障碍、原主接触时长、最终双侧抓持，以及共同目标末帧XYZ残差；完整24s回合另外给出绝对(18,24]末6秒150帧诊断，短回合留空，不补造未来位置。以上均来自既有归档，没有新仿真。


## 11方法附表：共同部署条件，训练来源不同

| 方法 | task | strict | waypoint RMSE均值 mm | 实际峰矩均值 Nm | 子步峰速均值 m/s | 完整24s |
|---|---:|---:|---:|---:|---:|---:|
| impedance_k900_z1.2 | 6/6 | 1/6 | 67.6458 | 35.5451 | 0.122216 | 6/6 |
| admittance_k150_z0.7 | 5/6 | 1/6 | 141.4174 | 35.9089 | 0.079997 | 6/6 |
| vmc | 5/6 | 1/6 | 148.1251 | 36.7591 | 0.119597 | 6/6 |
| mlp | 5/6 | 0/6 | 132.9366 | 36.6001 | 0.145266 | 6/6 |
| esn | 1/6 | 0/6 | 160.2036 | 36.4644 | 0.145770 | 6/6 |
| ppo8192 | 0/6 | 0/6 | 179.0691 | 51.5716 | 0.327079 | 6/6 |
| zero | 0/6 | 0/6 | 209.4661 | 31.8267 | 0.079997 | 6/6 |
| ppo_potential8192 | 0/6 | 0/6 | 19.9756 | 31.7391 | 0.135352 | 6/6 |
| parameter6 | 1/6 | 0/6 | 155.2050 | 38.9733 | 0.150369 | 6/6 |
| direct7 | 0/6 | 0/6 | 135.9822 | 38.3292 | 0.156100 | 6/6 |
| nominal_train_vmc | 1/6 | 0/6 | 147.4929 | 38.5095 | 0.148874 | 6/6 |

两种新RL同DGX、同8192互动预算，但parameter6含解析VMC记忆/控制先验且输出6维，direct7输出7维，不能称相同函数类。旧dense/potential PPO在本机训练，本轮配对RL在DGX训练；这里比较的实际六条件部署均为DGX。旧ESN/MLP模仿数据及经典搜索预算也不同，11方法附表不表示等训练条件。
存在安全短回合时，指标来自各自实际时长，不能与完整24s窗口直接排名；所有失败仍计入分母6。waypoint由状态机推进，指标需与阶段、task/strict、扰动曝光一起解释。没有按验证成绩挑checkpoint、改变reward或放宽gate。
输入和工具hash共464项保存在同名JSON。旧8方法JSON SHA256：`ec921c8d04cc6af12b822548690f59b87ec5262342dd43b0d811ec7c3b2a6e9b`；部署plan SHA256：`8c42a62308007d210051f19dbe45b9a878df19450ca66b4545b63ff14d87864c`。
