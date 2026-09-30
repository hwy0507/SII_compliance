# 潜势奖励PPO8192：DGX六条件结果与八方法表

固定final8192模型完成六条PPO和一条zero重验，task0/6、strict gate0/6，全部保留。zero9400与原已归档轨迹逐元素完全相同，其余五条zero复用原结果。原dense PPO及原五种控制器结果保留，不选择有利模型。

| 方法 | task | strict gate | 子步RMSE均值 mm | 实际峰矩均值 Nm | 子步峰速均值 m/s | 全部24s |
|---|---:|---:|---:|---:|---:|---|
| impedance_k900_z1.2 | 6/6 | 1/6 | 67.6458 | 35.5451 | 0.122216 | 是 |
| admittance_k150_z0.7 | 5/6 | 1/6 | 141.4174 | 35.9089 | 0.079997 | 是 |
| vmc | 5/6 | 1/6 | 148.1251 | 36.7591 | 0.119597 | 是 |
| mlp | 5/6 | 0/6 | 132.9366 | 36.6001 | 0.145266 | 是 |
| esn | 1/6 | 0/6 | 160.2036 | 36.4644 | 0.145770 | 是 |
| ppo8192 | 0/6 | 0/6 | 179.0691 | 51.5716 | 0.327079 | 是 |
| zero | 0/6 | 0/6 | 209.4661 | 31.8267 | 0.079997 | 是 |
| ppo_potential8192 | 0/6 | 0/6 | 19.9756 | 31.7391 | 0.135352 | 是 |

七条新原始归档的203个数值数组有限；float32物理子步数据独立复算误差/扭矩/速度通过，50µs时间步和样本数正确；每个fixture与原方法MJB相同、初始48D观测完全相同。170份冻结源码哈希在归档后复核一致。
完整归档`outputs/ppo_potential_dgx_archive_20260924_r1/`约458MiB，服务器/本机checksum dry-run无差异；紧凑证据在`docs/evidence/ppo_potential_dgx_20260924/`，本报告JSON保留28份NPZ哈希和全部逐项检查。

| seed | final stage | rod实际触发 | task | strict gate | 当前阶段终点误差 mm |
|---|---:|---|---|---|---:|
| 9400 | 1 | False | False | False | 15.484 |
| 9401 | 1 | False | False | False | 15.484 |
| 9402 | 1 | False | False | False | 15.484 |
| 9403 | 1 | False | False | False | 15.484 |
| 9404 | 1 | False | False | False | 15.484 |
| 9405 | 1 | False | False | False | 15.484 |

终点误差针对当前stage waypoint；停在抓持阶段时低误差不代表完成抬升/搬运。rod在loaded_lift触发，若未到该阶段则没有实际经历同等杆扰动，不能把小穿透或低全程误差解释成更优接触响应。

PPO仅单rod、单seed、8192互动步，ESN/MLP使用多场景模仿数据。潜势PPO只改变reward，保留原失败dense模型；六条件为已有开发验证，不能称独立office测试或论文级文献复现。
模型SHA256：`5f07bf8bac134c8464dd5daa8d8c4b46aa547525004ad37d0173d6cf0f3b1609`。normalizer SHA256：`944f583cce8b73df5f0328a9f981e47f96cb986e7eb35384be26742e922d9f9a`。
