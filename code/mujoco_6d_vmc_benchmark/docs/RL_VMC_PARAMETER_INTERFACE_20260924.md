# RL调参baseline：独立接口与待验证边界

本项目VMC是六轴解析虚拟弹簧—阻尼动力学，并非神经网络；ESN/MLP模仿它输出的7D动作。此baseline让RL网络预测VMC参数，再由VMC输出原action7，与直接输出action7的PPO分开。它借鉴可变阻抗RL的方法族，不冒称Da-VIL双臂QP系统的忠实复现，也没有修改proposed。

## 当前实现

`scripts/canonical48_vmc_tuning_20260924.py`提供独立adapter，策略仍只可读取canonical48。RL输出六个范围[-1,1]的log刚度目标，映射为原六维K的0.5–2倍。log倍率每秒最多改变`ln(2)/0.20`，动作周期仍40ms；D按`D0*sqrt(K/K0)`变化，保留主轴原点附近线性化阻尼比（饱和弹簧的非零offset切线刚度不同，不是全局恒阻尼比）。M、坐标旋转、滤波、饱和、积分器和action限制全部沿用原VMC。VMC只读取48D中39:45的本体估计wrench，不读取真值接触、阶段、质量或障碍状态。adapter必须接收原始SI单位48D，不能把策略使用的VecNormalize输出直接交给它；调节的是R6旋转后的主轴K，并非世界XYZ轴独立刚度。

选择范围和变化率只用于限定新接口，不根据验证成绩扫描；正增益和限变化率不构成变刚度被动性证明。原VMC的filter/offset/velocity及增益状态都保留至回合结束，reset全部清零；这是有内部状态的解析后端，与直接PPO的控制结构不同，必须在主表标注。

名义配置必须显式含`stiffness_6d`和`damping_6d`，缺少则拒绝构造。真实CoreTeacher在缺项时使用CLI stiffness/damping补值，与SixDVirtualDynamics独立构造器默认值不同；独立review发现这一边界后已修正，避免“零参数”悄悄改变控制器。完整训练来源配置不受该缺项问题影响。新增测试直接比较真实CoreTeacher，包含与配置不同的CLI默认值。

零参数指从reset开始始终输入六维零：这时K/D逐值等于原固定VMC。曾经调过参数后回零请求，只会逐步恢复增益，不能宣称立刻消除已有虚拟动力学状态。测试使用600帧接触/释放估计wrench序列，要求输出和内部状态与原SixDVirtualDynamics逐元素相等；另检查参数边界、阻尼比、跨回合清零、拒绝非法输入不变状态、只使用允许的wrench切片。这些是离线接口验证，不是MuJoCo闭环成绩。

## 后续执行规则（尚未启动训练）

已在DGX隔离快照和同一训练fixture上完成该adapter零参数闭环与原固定VMC的对照，MJB、有限原始轨迹、安全路径完全一致；独立结果见`VMC_PARAMETER_ZERO_PARITY_RESULTS_20260924.md`。原driver因contact集合序列化顺序误报FAILED，原证据保留，独立审计只规范明确set字段后通过。不得以zero-action7代替nominal-VMC：前者关闭了VMC residual，两者的含义不同。

后续Gym参数action空间为6维，执行action仍为7维；日志必须同时保留RL原始参数、限速后K/D、实际VMC action、reward各项及每次transition的next observation，避免混用旧action7日志。策略与价值输入仍为48维，不追加VMC内部状态。比较时明确其部分可观测性以及解析后端提供的内部记忆。

训练协议须在运行前另行冻结：固定名义VMC参数只从训练集取得，验证时不得替换成每个验证条件的teacher参数；同一网络、奖励、互动预算、seed和最终checkpoint规则与配对的直接动作RL一致。名义VMC、RL-tune-VMC、direct-action RL都须保留。当前潜势reward试验尚在运行，不根据它的验证成绩挑奖励版本用于此新baseline。

控制类差异必须保留：此接口含24维解析隐藏状态（滤波、offset、velocity、log gain各6维），不是额外真值输入，却提供了不同于无记忆direct PPO的先验和记忆。direct-action7可独立输出slowdown，parameter6中的slowdown由原VMC残差范数派生；相同48D输入并不等于相同函数类或可执行动作集合。从名义到倍率边界最快0.2s，两个相反边界互换最快0.4s。

当前完成接口、离线测试和DGX两条24s零参数闭环等价审计，二者task/accepted_panel_demo均true；这仅证明同源接口等价。尚无已训练的参数RL模型、学习后三指标结果或论文级复现，也未证明本机与DGX历史数值环境等价。
