# 有界横向反馈教师：五回合开发验证已启动

固定一个参数配置：cross-track gain=1.5/s、速度上限0.02m/s、横向载荷尺度1N。canonical48参考误差投影到水平路径法向，在载荷较大时平滑抑制回位项；不使用几何/时间/阶段/成功真值。旧ParameterTeacher、MJB/场景参数/Task/安全gate/公共filter/执行器和dt5e-5不改。新wrapper通过替换actor接入原物理worker，不改其源码；原execution.json保留student-diagnostic来源，再用HANDOFF_EXECUTION.json准确说明实际混合行为。零前缀代表新teacher全程执行，不冒充旧teacher。

新服务`sii-cross-track-teacher-development-20261030.service`原PID1766039，CPU6单路/线程1、MemoryMax3GiB/swap0。登记1142源码，运行中不得编辑。旧full12、最终等待器和旧两条纠偏服务已inactive。全五回合固定顺序：rod00纯teacher、ball00纯teacher、corner00纯teacher、rod00学生175步后teacher、rod00学生275步后teacher。只有训练身份，无未见输入/选模/拟合；任一科学失败仍继续完成有限五回合，基础设施异常保留停止、不自动重试。

学生前缀选择已有MLP02验证rank2（checkpoint/hash登记），原rod00安全通过但提前持续回位失败，避免原rank1在接管前已有穿透超限混淆。预期不是保证恢复；两条实际新teacher后缀和名义三场景都须独立审查。

零物理集成控制：前缀0/175/275保存历史的独立纯teacher/student回放、完整/注入物理异常的记录/label mask、真实五case prepare/hash检查、重复prepare拒绝均通过。独立审查入口再用纯controller重建动作和实际teacher标签，原公共filter逐步回放、rod几何顺序/保持、原Task/安全资格，配对相同MJB/初始canonical48/filter；前缀反事实teacher输出仍禁止作执行示范。循环数据warmup/lossmask与共享重训仍需后续协议。

首条真实rod00已500步/400000子步完成，qualified=true；新增独立campaign前缀review也通过，重新核动作/label及源/配对/资源证据。峰矩34.523502Nm、外穿透0.071541mm；越棍7.72s、持续回位确认8.16s、撤回开始12.80s。只是首条开发真实成功，不是五条完成、偏离状态恢复证明或新teacher全面安全。球撞已接续，桌角/两条纠偏仍待。

Goal active：五回合完整结果、共享纠偏数据与公平重训、九模型锁定、冻结未见108/六指标/媒体仍待。原teacher与学生全部失败档案保留；旧office108的57待补不覆盖。无RL/删除/并发第二模拟器。服务器仅存储/hash。

后续状态：三名义场景rod/ball/corner均qualified=true，新增独立三case前缀review重新核验通过；两条学生前缀纠偏尚待。三场景通过不是偏离状态恢复成功或最终泛化。此补充在首条raw包生成后写入，包中文档为此前版本，原raw/登记/源不变。
