# 非RL覆盖补采入口与实际CPU约束修复

主矩阵仍未修复，Goal active。本轮没有新物理采集或训练。原108与后处理保持运行，
02:21:25 UTC按`ended_utc`计已完成41/108；第42条MLP seed2、条件004在途至54.04秒。
这是进度快照，不是完整矩阵或成功率。原PID/start分别1172675/32623702、1201537/32942337。

## 直接相关的学习问题

已完成的审计显示：teacher十条棍推均在撤回前完成让位/蹭过/回位；但24条训练示范的
12,600帧没有±Y主导参考方向。三锁定ESN在既有同协议成功teacher轨迹上的载荷×上下文
读出发生明显外推。前四个已完整审计条件中三方法Task/Strict全失败，不能仅凭低训练loss
或新场景开发成功宣称原测试修复。详见
[方向覆盖](NONRL_V8_TRAIN_DIRECTION_COVERAGE_20261029.md)、
[读出诊断](NONRL_V8_READOUT_SUPPORT_DIAGNOSIS_20261029.md)。

这些支持检查方向×载荷×阶段覆盖，不证明单一因果；不能断言只改“蹭棍子”必然应当保持
旧性能，也不能据此更改测试gate或丢掉失败回合。原12条件已被检查过，只能称冻结回归。

## 正式采集衔接修复

旧正式采集器的ball白名单只接受球速、撞击偏移和高度。直接把已有八方向开发配置
交给旧入口会被拒绝。新版本独立保存，原在途源与八球v4的197绑定源均未改变：

- `tools/collect_special_scene_coverage_20261029.py`：新prospective plan-v3，显式登记
  初始XYZ、carry XY、撞击角与approach事件；复用物理适配器的有限边界。
  每次正式派发须有真实完整八球REVIEW及registration/execution/qualification来源hash，
  正式计划时间必须晚于review。开发失败保留；完整review不等于全部合格。
- `tools/run_registered_special_coverage_20261029.py`：只替换采集器引用、要求正式plan；
  对原coverage wrapper逆变换逐字节相等，物理/teacher/输入/filter/阶段gate不变。
- `tools/qualify_registered_special_coverage_20261029.py`：仅wrapper名称不同，资格数值门槛相同。
- `tools/build_special_coverage_dataset_20261029.py`：构建前重新校验新plan；数据数组、
  原资格与棍推审计、24/6划分、每方法每seed 12候选、神经32,000更新均保持原实现。
  输出dataset/training schema仍用原v2，与现有三方法训练器兼容。

尚未登记正式30条，不会将八个开发控制直接充当训练/验证标签。只有八球完整审查后，
才能根据实际可达性、接触和阶段覆盖选择正式配置；杆/边角仍是必需的两类真实场景。

## 实测资源问题及更正

首个新入口检查`sii-coverage-ingestion-check-20261029.service`失败并保留：
读取实际cgroup `cpu.max`时FileNotFoundError，尚未执行物理或创建新采集状态。
调查确认本机用户服务只委派memory/pids；原108与后处理虽配置CPUQuota=100%/50%，
实际都没有`cpu.max`。因此历史文档中的这些数值应解释为**请求配置，不能证明CPU配额实际生效**。
现有MemoryMax=3221225472、MemorySwapMax=0及OOM/swap=0仍由实际文件核实。
未更改系统委派、桌面配置或正在运行的科学服务，未将资源发现等同于任务指标算术失效。

新入口要求实际cgroup配额≤1CPU，或实际单CPU亲和性（二者满足一个），同时检查单数值线程、
3GiB和禁swap。本次通过检查的服务使用`CPUAffinity=6`，读取实际affinity=[6]；
子进程继承该亲和性。CPUQuota50%仍是请求、并未生效，不将此次检查描述为实际50%上限。
最终检查服务自然exit0，runtime536ms/CPU204ms；瞬态unit随后被回收，不能用事后not-found
冒充成功证据，实际结果见命令返回和检查文件。

旧八球v4同样直接要求`cpu.max`，将无法在当前主机继续。因此保持旧源与未启动v4原件，
新增`tools/prepare_ball_coverage_bounded_20261029.py`及唯一待用v5：
`outputs/nonrl_ball_coverage_probe_20261029_v5`，REG SHA256
`be0056d33c065cf2bae56b1c3e208328abf352ecc70df035ed407f6ddb1fa752`。
八case、teacher、原108准确PID/start/准备/model-lock/审计前置条件完全一致，绑定198源。
资源检查使用上述实际上限，execution将记录实际backend。v4新增superseded说明，未改原登记或源。

## 验证与边界

[最终软件检查](evidence/NONRL_INTENT_RECOVERY_20261029/V8_COVERAGE_INGESTION_V5_CHECK.json)，
SHA256 `0731520576d801ffb3398b63ddc7a42cdefff232dc111528a38f1371557e4bd4`：

- 八个真实登记ball配置均接受；七种缺字段及七种越界/非有限/未知字段等配置拒绝。
- wrapper、资格器、dataset数组/预算的限定逆变换精确一致。
- 1个正向、14个拒绝用例测试review来源关系。此部分使用明确的内存模拟fixture，
  没有生成虚构的真实REVIEW、轨迹或标签。
- 真实缺失REVIEW拒绝；无CPU控制器且多CPU亲和性拒绝，非单线程拒绝。
- v4全部197源、原108绑定保持；v5八条件/teacher/前置身份相同，198绑定源准确。
- v5真实`--run`仍因原108未完成拒绝，没有创建execution或新仿真。

[资源与进度快照](evidence/NONRL_INTENT_RECOVERY_20261029/V8_COVERAGE_RESOURCE_SNAPSHOT.json)
记录实际cgroup、OOM/swap、身份和正确`rollout.progress.json`。
尚未验证完整正向物理路径，软件通过不能替代物理可达性或学习改善。

## 后续顺序

原108自然完成 → 原后处理完整审计/接触诊断/图表 → 实际查看并归档 → 有界服务执行
`prepare_ball_coverage_bounded_20261029.py --root outputs/nonrl_ball_coverage_probe_20261029_v5 --run`
（单CPU affinity、单线程、3GiB、禁swap）→ 原`review_ball_coverage_probe_20261029.py`全八审查
→ 新正式三场景采集/资格 → 公平重训 → 冻结108回归六指标。**不要再派发v4。**
不自动放宽gate、不使用测试标签拟合、不重选历史seed；失败均保留。

开工实际fetch/read main `e89ad58a8df24627aa46eed9d967461f4a41372e`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。远端独立RL更新快进整合，未操作其运行。
本轮为准备/修复进展，非等待冒充科研完成。无子agent、服务器计算或删除。
本轮9成员源码/准确登记/最终检查/快照已逐成员对本机文件、暂存及最终大小/hash核验，共享于
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_coverage_ingestion_20261029_v1/SOURCE_AND_CHECKS.tar.gz`。
35711bytes，SHA256 `682911ea6b09229ddfff33b693295c4a20f964c28695ad7638ef1a0c3818da8f`。
这是本轮准备源码与检查，未包括在途物理全集、未来采集或本报告。无服务器计算。
