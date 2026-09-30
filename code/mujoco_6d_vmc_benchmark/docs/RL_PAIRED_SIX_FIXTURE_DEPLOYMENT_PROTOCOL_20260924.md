# 配对parameter6/direct7：六条件部署前协议

状态：仅准备，未启动本协议的18条仿真。训练及其源码快照由独立任务管理；本协议不修改已冻结训练文件，不选择checkpoint或改变reward。两个最终模型完成独立审计、600帧离线回放和本协议hash冻结后，再由主任务核查DGX总并发并启动。全服务器物理worker上限4，不因本工具存在而自动开worker。

## 固定矩阵与对照

原六fixture seed9400–9405，每个固定运行parameter6最终8192、direct7最终8192和nominal_train_vmc，共18条新回合。前两种分别使用自身训练normalizer；nominal_train_vmc是parameter6从reset起持续zero6，使用训练全部名义options，具有原解析VMC状态。它不等于旧六条件名义VMC，也不等于zero7。原五方法、旧dense/potential PPO及其失败证据全部保留。

六fixture任务/物理参数和环境CORE_VMC_CONFIG从原VMC命令恢复，禁止将训练CORE环境覆盖到验证环境。parameter6后端单独读取最终训练manifest的完整nominal_options，并与原train fixture记录中的CORE_VMC_CONFIG字典全量相等；包括K/D、M、坐标旋转、滤波、饱和、速度/offset/action限制及其余显式options。不能只复制K/D或改用验证teacher。

direct7的zero7对照可以复用已归档六条，但必须在新部署实际MJB与原fixture逐条一致、共同物理源码/配置与初始观测一致且旧文件hash有效后才接受。只有MJB相同不足以证明控制运行配置完全相同。没有满足复用证据时保留“待核查”，不填入虚构对照。

## 精确输入与回合状态

训练首帧来自ArchivingCanonical48Env.reset收到的首次actor队列观测，env.obs保存float64原始48D；返回actor前转float32。后续每帧由原bridge接收下一次actor队列观测，env.obs仍是原float64，step返回float32。parameter wrapper在发送本步action前读取env.obs，绝不以转换后的actor返回值重建wrench。终端next只是占位并标无效，不构成第601次actor调用。

部署loader每次接受原panel runner生成的float64 raw48：actor路径先转float32，再调用该分支自己的训练VecNormalize（training=False、norm_reward=False），然后deterministic predict并执行训练Box裁剪。parameter6路径另外把未经转换的原始raw48及六维请求交给Canonical48VMCTuning；raw[39:45]为其SI wrench。direct7不更新VMC记忆。loader拒绝错误维度、非有限值以及已经float32化的raw backend输入。

每次加载/episode先reset原VMC滤波、offset、velocity和六维log增益；nominal K/D恢复训练值，策略归一化均值/方差/count保持冻结。policy输出层为6或7，部署执行始终action7，且不调用teacher、不做mixture。物理env、WBC、安全层与50µs测量包装沿用冻结版本。

## 加载与证据

新增文件独立于训练快照：

- `scripts/canonical48_paired_deployment_20260924.py`：最终模型/normalizer/manifest来源校验和raw48→action7加载器。
- `scripts/run_panel_paired_deployment_20260924.py`：独立panel入口，原source不改；写出deployment配置与每帧raw、请求、action7、K/D/log_scale。
- `tools/audit_paired_deployment_replay_20260924.py`：纯离线600帧最终模型动作回放，不创建物理环境。
- `tools/prepare_paired_six_fixture_deployment_20260924.py`：最终审计通过后只生成18job冻结计划，绝不启动进程。

只接受最终训练COMPLETE：8192真实transition、固定final8192、模型与normalizer哈希匹配、source_unchanged和normalization_frozen。出现FAILED.json时拒绝，即使COMPLETE并存也不能覆盖失败。两分支训练manifest的预算/超参数、训练fixture、reward、运行环境、资产hash、冻结source和名义options必须匹配；不要求因策略不同而产生的归一化统计相同。执行后端源码必须与训练manifest中的adapter和SixDVirtualDynamics哈希一致。

prepare还必须消费两份独立真实transition audit，核passed、manifest hash、training_transitions=8192、SB3转换8192项全部准确，以及每个原始episode的journal/NPZ/actor/contract哈希。逐条重核原SB3 received reward与Gym日志转换并绑定received日志hash。audit episode路径可从原run绝对路径或精确run后缀唯一映射到当前归档train/eval目录；拒绝逃逸、重复、模糊匹配和缺漏，不因为跨机目录不同而跳过文件验证。计划保存两份audit SHA及其原始run标识。

## 600帧回放：阈值现在固定

始终验证每分支最终`eval/train/ppo/episode_00000`的全部实际帧，不从结果选择轨迹。首先检查transition raw与actor_trace raw逐元素相同、实际action7相同、相邻next与下一帧raw相同、最后next无效且仅末步terminated。原runner存在穿透>2mm安全提前终止，因此不能要求失败策略一定产生600帧。

固定fallback现在预声明：若该learned评估为1–599帧，只有完整终端日志、rollout.invalid_physics=true且实际duration=0.04×帧数时接受为真实安全短回合。先完整回放实际短前缀；再仅使用训练manifest.argv中唯一绝对`--proof-root`所指定的本branch `<mode>/gym/episode_00000` 原先固定的600个raw边界，做“独立原训练推理路径 vs 新loader”双路离线推理与解析后端比较。检查proof COMPLETE/PARITY/hash、同训练source/fixture/assets/runtime/device/options和实际MJB，proof本身必须600帧zero且无安全终止。不得改选其他learned轨迹，不补写假设的未来闭环状态，不将fallback称作600步实际策略部署。执行错误、缺日志、无效终止掩码、来源不明短回合仍阻断。

1. 策略推理：默认部署device沿用训练manifest（同平台同device，要求请求动作exact）。如事前指定跨device部署，policy request比较固定absolute tolerance=1e−6、rtol=0；不在观察差异后放宽。单独报告跨device最大差异。
2. 解析VMC与action链：从reset开始用记录的相同请求和相同raw重放，要求action7和K/D/log_scale absolute tolerance=1e−12、rtol=0。再用部署actor实际生成的请求驱动独立VMC，和loader实际action7按同阈值比较。
3. reset后二次重放完整600帧，所有输出要求exact；normalizer mean/var/count前后exact。单独报告“部署实际action7 vs 原训练评估action7”的端到端差异；若跨device只满足policy阈值，不声称原未来闭环轨迹逐位等价。

首帧与后续帧使用相同训练cast顺序；回放不会把terminal占位输入策略。fallback以外的缺完整600帧、任何非有限值、模型/源hash不匹配均失败，保留失败日志，不能改选别的评估轨迹或降低标准。当前仅合成测试通过，真实最终模型回放须等最终模型存在后执行。

## 运行前冻结与验收

prepare工具生成状态prepared_not_started的plan JSON，包含18条完整命令、原fixture来源、两个模型与normalizer hash、两份parity hash、新部署源码hash及本协议hash。不允许覆盖已有plan文件。主任务复核剩余资源后先各运行9400共3条，逐条核查：原MJB/共同配置/初始raw、无teacher/mixture、600×48 observation和600×7 execution、参数日志与原rollout逐元素匹配、模型及归一化hash、真实50µs子步样本和接触记录。通过后才推进其余15条；不能因为任务失败而停止记录或选择性重试。

冻结主指标沿用物理子步位置waypoint RMSE、实际actuator峰矩、子步末端峰速，并同时报task、原strict gate、final stage、杆真实触发/接触。安全提前停止保留实际时长和失败状态；程序执行错误另列，不能当有效完整回合。共同最终目标末6秒3D/XY/Z仅辅助诊断，失败不排除。未达到stage3时杆未触发，不能把低waypoint误差或低接触峰解释为更好柔顺性。

本协议只制定部署，不增加新reward、调参、验证选择或训练预算。不对目前未运行的18条给出结果。
