# SAC Impedance完整第3轮审计（2026-10-25）

SAC Impedance第3轮已完整归档，累计187278环境步。Task从17/30增至18/30，Strict仍17/30；critic loss、Q及终端MAE继续增长，不能把reward近似平稳称为健康收敛。原learner1557140已进入第4轮，本次没有改变其配置或权重。

| 指标 | 完整第2轮 | 完整第3轮 |
|---|---:|---:|
| 环境步数 | 146028 | 187278 |
| Task /30 | 17 | 18 |
| Strict /30 | 17 | 17 |
| 被动/短期/长期Strict（各10） | 0/10/7 | 0/9/8 |
| 平均回报 | -2.23729 | -2.35752 |
| 末1000更新critic loss | 2532.79 | 19284.80 |
| 样本Q均值 | 2488.46 | 5252.21 |
| replay终端样本MAE | 519.08 | 1540.28 |
| alpha | 1.17751 | 2.57404 |
| 当前alpha理论上界超限比例 | 2.5391% | 3.3569% |

Strict条件发生一失一得：active_short_train_0600从成功变失败；active_long_train_0300从失败变成功。失败阶段carry12、retreat1。上述训练周期内policy持续变化，不是固定checkpoint的独立接受测试；不能将两周期的不同replay样本视为匹配对照，或与不同步数的其他方法排名。当前alpha上界并不约束未来变化alpha；终端MAE可能含缺少remaining-time输入的混叠，不要求它严格为零。

只读诊断3712274已退出，0 optimizer更新/0新增physics。登记冻结30个条件episode、41250 transition和82500 optimizer日志行，并读取不可变cycle3 checkpoint，SHA256为38c7e9e7149bb3bc421cb5aff53f16cb42f85f80df720f2b835848851d5a9b7b。30个终端/原MJB与共同cohort模型hash再次核验；奖励由transition组件重建、网络未变、输入hash检查通过，训练诊断图已目视检查。使用已验证的原诊断工具，未修改live源码。

原四CHEQ第11轮和四SAC持续运行。另登记只读观察器3759872：仅等待SAC Admittance/VMC第3轮不可变完整归档，之后各诊断一次；不重复Direct5或本次Impedance3。观察器三小时截止只限制观察，不会停止训练，输出需后续科学复核。原CHEQ审计1346884和配对复核1346887继续等待11。source16仍未部署；本报告不选择下一训练干预。名义矩阵现117/120：slot1的60项结束、2210515已退出勿重启；slot0的2210514继续剩余3项，最终整矩阵复核/Tref仍待。

产物根目录：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。

- `runs/diagnosis_sac_impedance_cycle03_v1`：REGISTRATION、LAUNCH、冻结inputs、results和REVIEW。
- `runtime/sac_impedance_cycle03_diagnosis_v1`：本次冻结诊断源码。
- `runs/SAC_REMAINING_CYCLE03_AUDIT_V1.json`及同名前缀LAUNCH：两路待完成周期的只读审计登记；输出`runs/sac_remaining_cycle03_audit_v1`，冻结工具`runtime/sac_remaining_cycle03_audit_v1`。

本轮fetch/read远端main a52dfba、baseline f6e8f8c，均未变化。physics/MJB、任务/安全gate、actor信息、公共filter、执行器限制和dt未改。GPU持续50%、充分收敛、完整训练集SPT/指定ESN公平对比仍未完成，不以局部诊断替代最终目标。
