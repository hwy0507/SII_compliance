# 同平台RL调参与直接动作：运行前协议

目标是完成当前尚缺的RL调参训练链，并检验解析VMC后端在相同互动预算下的作用。本协议先于新一轮训练写入。已有PPO失败模型、经典控制器和proposed全部冻结保留，不改变gate，不依据9400–9405或front验证成绩重新选择奖励、参数或checkpoint。

## 两条训练分支

两条均在DGX当前同一软件环境训练，分别独立单MuJoCo环境、1CPU线程，合计最多2个物理worker；总服务器并发仍≤4。两条都使用8192真实互动步、训练seed20260923、MLP[128,128]、PPO learning_rate=3e−4/n_steps64/batch64/n_epochs3/gamma=.995/GAE=.95/log_std_init=−2，actor与critic仅canonical48。观测归一化各自在训练数据在线拟合，评估冻结；不声称两个因策略不同而访问的训练序列相同。

| 分支 | RL输出 | 实际执行 | 解析内部记忆 |
|---|---|---|---|
| direct7 | 原slowdown/yield7 | 原action7安全/WBC链 | 不增加VMC后端 |
| parameter6 | 六维[-1,1]log刚度目标 | 固定名义VMC生成action7，再用相同安全/WBC链 | VMC滤波/offset/velocity及增益各6维 |

parameter6使用已验证`canonical48_vmc_tuning_20260924.py`：主轴K为训练名义值0.5–2倍，D按sqrt(K/K0)保留原点附近线性化阻尼比，固定限速、M、旋转、滤波与饱和，不能独立选择slowdown。adapter读取原始SI单位48D，不读VecNormalize的数值。两种动作维度、网络输出层参数数目、先验和可执行控制集合不同，必须如实报告；相同输入/预算不等于完全相同函数类。

奖励两分支共同沿用已存在且冻结的`push4_gate_potential_v1`，没有根据本轮验证重新设计奖励。固定有限任务终端潜势为零，保持原开发gate；不会因新策略失败放宽任务或接触门。该奖励对齐开发gate，不直接优化三指标，也不等于完整panel或office gate。

## 数据、控制与物理来源

训练只用canonical manifest首个train push `push_00000`，原seed800及物理场景，显式恢复rod高度0.65m。此轮是接口与小预算试验，仍非多条件充分训练。parameter6的**全部名义VMC options仅来自该训练配置**，评估front/之后六条件时固定不变；不能利用验证teacher的K/D或其他控制参数。物理场景及共用执行器仍按原fixture配置，不通过替换场景环境变量来改变共用执行链。

独立新Gym层包装原action7 bridge，旧source不修改。两条新训练在同一只读snapshot下执行，逐项保存运行源码/协议/fixture/model资产和运行时版本hash、完整命令、资源及失败状态。最终模型固定8192步，2048/4096/6144/8192 checkpoint只为诊断/恢复留存，不用验证挑选。

## 必须先完成的运行前验收

1. 纯合成测试覆盖raw/normalized分离、六维参数到七维执行、跨回合VMC状态清零、拒绝非法输入、reward终止和partial边界、transition记录。第三方agent独立review新代码，修复证实问题后才能冻结。
2. DGX完整24s参数Gym持续zero6，必须与已经归档的同平台同源nominal VMC执行轨迹逐值一致。zero6是名义VMC，不是zero7。actor日志额外文件不影响比较；teacher_action只有原先声明的日志语义差异。所有比较先检查有限值，MJB与原任务/安全数值一致。仅源码证明为set的contact列表允许排序规范化。
3. 同源direct7 Gym持续zero7，与既有direct action桥或同配置direct zero参考比较，要求相同原始轨迹和物理配置。若旧MJB未保存，使用已验证同配置重新归档的参考，不捏造旧hash。
4. source、参数、数据与这些验收结果保存完毕后，才启动配对训练。若验收失败，保留失败/原数据并定位，禁止通过放宽动态字段比较或挑fixture使其通过。

## 修复可追溯性缺口

每次transition保存pre raw48、next raw48、请求动作（parameter6或direct7）、实际action7、参数K/D与增益状态（参数分支）、reward及各项、phase仅作reward标签、terminated/truncated、next有效性。原bridge终端没有下一次actor观测，不凭空读真值补一个48D：终端next占位必须标`next_observation_valid=false`，terminated仍阻止bootstrap。预算partial的最后真实next必须保留，不把它伪装终端，也不遗失末项reward。

旧8192实验缺少的实际Gym reward/terms与partial末next将在此新版本完整保存。若未记录PPO内部value/advantage，就不能声称已审计其实际GAE/loss；报告实际覆盖范围。日志写出异常不能吞掉，应写FAILED并保留可恢复checkpoint。

## 冻结评估与最终报告

每个分支固定最终模型后，在同train rod和validation front各运行一次无学习对照（direct7为zero7，parameter6为zero6名义VMC）与一次确定性PPO，共每分支4条24s。奖励与模型参数不再调整。报告任务、开发gate、阶段、杆/护板是否实际经历，不把阶段1的小waypoint误差解释成最终任务成功。

共同50μs物理子步三指标用于后续六条件部署时保持原测量定义；当前若某评估只保留25Hz/4ms数据则必须分别标注，禁止冒充子步峰值。追加共同目标距离只作诊断，不覆盖冻结主表。后续六条件部署同样保留所有失败及独立nominal-VMC对照，且参数分支必须继续用训练名义配置，不能换回各验证fixture的teacher。

当前状态：实现、独立review与24s Gym parity准备中；尚未启动本协议训练。运行PID、source/hash和完整结果以后写持续入口。旧本机两种reward实验及DGX部署均已结束，不重复启动。
