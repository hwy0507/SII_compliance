# 现有102模型输入边界与本地三机位交付流程

2026-10-03。两项均为工程核验：0新物理积分、0拟合、0封存条件访问，不增加控制器成功率证据。
主机为本地airpig，Python3.11.15/NumPy2.4.6，单线程库设置、MemoryMax3GiB。

## 2026-10-04：固定储备池身份独立重建

01:14:41UTC完成新的零训练/零推理/零物理核验。初始与context-gate两批合计12个ESN、6个重新拟合无记忆对照，
覆盖全部216个保留ridge候选；不是只检查选定的18个checkpoint，也没有按任务成败筛选。
以原训练seed重新生成随机输入矩阵、稀疏循环矩阵及其原谱半径缩放、四组时间尺度和固定gate投影，全部逐值相同。
检查完整checkpoint字段白名单、2884个可训练读出系数、禁止直接context输出的末12行全0、限幅与输出增益配置。
不允许额外隐藏读出层/阈值字段悄悄进入本轮纯ESN合同。每个拟合模型执行两个内存负对照：修改循环矩阵与增加隐藏层均被拒绝；
不将这些被修改的内存副本写作候选。MLP/RNN允许学习其矩阵，明确排除在“固定储备池”断言之外。

这是采用原拟合运行库NumPy2.4.6的初始化重建，不要求不同BLAS/架构下重新做特征值分解逐位相同。
实际部署使用已归档矩阵；随后将本地审计逐hash关联Spark档案中的18选定权重、训练metadata和216候选，全部相同。
本机systemd单线程/3GiB/无swap，进程1.183s、CPU1.050s，原权重不改。
本结果支持当前ESN训练只改变声明的读出；不证明echo-state收缩、机器人稳定性、留出成功或优于神经baseline。

共享主机arm1@192.168.31.70，本轮根`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：

- `fixed_reservoir_audit_v1/`全部2文件已核验；保留真实本地命令/路径，没有改写执行主机。
- 结果SHA256 `b01441975949630d46b0b579b36e25bf40fdc52fd043390810c6155af3d4fdcc`，Git同字节FIXED_RESERVOIR_AUDIT_V1.json。
- 实际审计源码SHA256 `51bec65f7e63a4627aeaf4895090a7ee84a60d0387e71277eb4fdc15f89874d0`，无需MuJoCo或读取条件manifest。
- tar SHA256 `2b6ea4ba8a0db3bdde62b10dffea7f2ebb0257b46bcf2288b12d525fe11717bd`。
- 模型档案：`local_learning_archive_v1/learning_v1/`与`local_context_gate_archive_v1/context_gate_learning_v1/`。

## 已拟合模型的部署输入边界

21:23:55–21:24:06UTC，11.776s墙钟、11.545s CPU，完整检查三个拟合归档的102模型：
ESN12、重新拟合无记忆6、同特征MLP/RNN各24、普通MLP/RNN各18，没有按闭环成败筛选。
所有模型均使用同一已知训练身份train_000的1375个观测，以实际部署`load_current`入口执行。

声明字段是canonical48中的14:17名义线速度、20:23参考相对位置误差、26:29速度误差、
39:45估计六维负载、45:48名义路径方向。其余30维统一用固定seed2026100343的[-1000,1000]有限值替换。
这些其余字段并不都是接触真值；本实验核对的是学习actor声明的18字段子集。

- 全140,250时刻原请求动作与训练导出的请求动作最大差0；两种输入的动作也逐值相同。
- 82,500次可见内部状态检查逐值相同。无记忆模型的临时state检查不意味着它具有时序记忆。
- 所有请求有限、第一通道在[0,1]、其余在[-1,1]；只读观测交给actor，未发生原位修改。
- 所有checkpoint与训练收据hash在核验前后保持一致。
- 3项独立负对照通过：允许信号正确重放；仅隐藏状态偷用未声明字段也会失败；修改输入会失败。

这仅覆盖一条已知训练输入序列，不能证明所有可能输入上的隔离、真实传感器准确性或闭环安全。
不覆盖RL与经典控制器，也不把参考生成器或共享观测器的真实性归给该检查。现有观测器是编码器差分和
已知动力学/实际电机力矩残差，属于理想传感器仿真；硬件误差另需实验。将来若新增拟合，须补核对新模型。

## 三机位工程回放

21:30:42–21:31:02UTC，复用同一公开train_000原teacher的归档qpos/qvel/ctrl/mocap与精确MJB。
本地MuJoCo3.11.0，只做`mj_forward`渲染，不重新积分或让策略控制。场景/三机位/原速保持不变：
overview、end-effector、pillar-corner，1920×560，25fps，1375帧完整55s。

渲染18.771s、全帧解码审计1.692s，峰值内存691,216,384B，约0.644GiB。
6时刻拼图已目视核对三视角、任务文字和完整放置姿态；没有声称看完全部动态细节。
原输入3文件hash全部不变，视频时长/帧数/hash通过。此处显示的teacher成功来自既有训练回合，
**不是ESN结果或新留出成功**。最终仍须按预定首个共同条件展示所有38模型/seed，包括失败。

单条本地耗时外推38条约13分钟，仅作工程参考，不含文件传输、目视核对和各模型的实际渲染差异。
预算文件中的2h收尾预留保持不变，不能据此删除物理审计或提前声称全部最终媒体已完成。

## 共享与源码

主机`arm1@192.168.31.70`，本轮根`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：

- `actor_field_audit_archive_v1/ACTOR_FIELD_AUDIT_V1.json`，SHA256 `7aaba52990beb7423b707ae243434c8420f4f38ef51723d52a3ebb4dec9fc5d6`。
  Git evidence同字节保存全部102行。该目录另有实际审计/负对照源码，完整3文件集合和hash已核验。
  审计源SHA`527ec481eef9cadc4837ae5a1d2bdc91e6f74696b81eaa172b6fd4d24791bacc`。
- `media_rehearsal_archive_v1/evidence/`：10文件/18,244,126字节已完整大小/hash核验，外层`ARCHIVE_VERIFICATION.json`记录映射。
  manifest SHA`8ff005e84326e5a0230c9abc4024fab1ead164618ce63b7733919bd3b8b6d09a`；
  execution SHA`464dbe742f17fa3e65c247cbf30fe8d9f4f637b323a9ec72f6b14266ad113f5f`；
  MP4位于`media/replay_threeview.mp4`，SHA`d6a009c7240eeb8877f4ce853331044c349787083fe4227a9c1b68d07ed11b0b`。
  完整命令和实际本地路径保留在execution；未伪造服务器计算。
- 归档tar在`/home/arm1/sii_shared/SII_compliance/incoming/research72-media-rehearsal-v1.tar.gz`，
  SHA`2a8e5a140687976644095e88c189a544b0610f5afa7c63215ddbf8131366659d`。
- 输入原件仍在`teacher_bank/queue_0/train_000/`；trace SHA`785c075ced8fcc30ca470030b84166f1c0fb6607dfe3fa87b701a052bb791d67`。
  未重复归档52MB模型；输入MJB为主协议d4c28e40…，全部输入hash见execution。
- 两新检查脚本执行基于main c84a7cd加本批未提交脚本；不是干净commit执行。
  旧renderer与实际actor的完整源hash在结果中。c84a7cd源码已在
  `/home/arm1/sii_shared/SII_compliance/source/c84a7cd8aea0ab1874d7c3682773e772445c2cc5/`
  核验3201文件，tar SHA`20595252d883a0ff09b4c084544561ad45416e0f6eab6b9664d497a9752d253b`。

原四个物理队列继续，未因工程检查重启。teacher确认/新组/RL以及真正最终矩阵仍未完成。
