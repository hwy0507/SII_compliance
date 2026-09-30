# 多训练seed六条件部署：准备与审核记录

本文保留启动前的准备和审核证据，后续实际状态见[启动记录](PAIRED_MULTISEED_DEPLOYMENT_LAUNCH_20260925.md)。执行范围见[预声明协议](RL_PAIRED_MULTISEED_DEPLOYMENT_PROTOCOL_20260925.md)：新24条learned+1条nominal9400 parity；只有完整raw parity通过后复用旧nominal六条。性能数据为36条learned+6条共享nominal=42条独特记录，额外parity不进均值；direct7使用的旧zero7六条另计。没有把nominal复制为三个训练seed，也不把每个seed的六fixture当独立训练重复。

已新增prepare、执行driver、离线report和独立snapshot builder。prepare读取[具体DGX请求](evidence/paired_multiseed_20260924/deployment_request_20260925_r1.json)，最终模型显式seed/8192步/384更新、全部transition和SB3 float32奖励、四项finaleval、train/validation zero完整精确parity、600帧实际device回放均为强制前置条件。执行driver在任何物理launch前从request重新生成全部plan并要求精确相同；默认2worker，协调上限4，先1nominal，再4个9400，最后20条。任务失败保留；执行/对齐错误停止新launch。

子进程超时为每条1800s；清理中TERM和KILL后的reap各最多15s，无法reap的本任务PID保存在结果和active状态中，不能误报空闲。只清理该driver自身创建的进程。

## 已完成的纯离线检查

- 新工具12项测试及已有报告7项测试，共19项通过。覆盖确切25job矩阵、三seed聚合/不把fixture方差冒充seed方差、安全短回合仍计分母、任务失败与执行错误的区别、全raw精确parity、路径/hash漂移及有界子进程清理。
- 对旧nominal9400真实归档执行只读`nominal_parity(old,old)`：5份NPZ、36个数值/字符串数组通过；字符串只作dtype和逐值精确比较，所有数值另要求有限。没有新仿真。
- 新报告同时绑定自身和复用的prepare/原driver/原report源码hash；不可在运行期间修改这些冻结工具。
- 已在DGX对seed20260924两分支和seed20260925 direct7运行新prepare的独立`check_run`，各77项输入绑定通过，600帧CUDA回放exact。该记录只证明这三个run，不提前宣称第四个完成。

## 独立只读快照

本机及DGX目录均为`outputs/paired_multiseed_deployment_source_20260925_r1`。复制原199文件并新增10项，总209项；原165份训练Python逐字节不变，所有Python仅静态compile、不导入仿真入口。source目录/文件设为0555/0444。主协调任务已独立核查DGX全部209项hash及不可写位。

BUILD SHA256：`6ca2a7da41b994aa09fbd0cf8d9b82c74ee64f590e96a49b26aa200a9357ab6e`。

| 文件 | SHA256 |
|---|---|
| prepare_paired_multiseed_deployment_20260925.py | `829d32be2d99db144554712d9825950263b21c0db34d2928768db73a10ca3796` |
| run_paired_multiseed_deployment_20260925.py | `bce626466b7221da504f57195645603cd443cf064cb7d22ef1b36bcff1f3facc` |
| report_paired_multiseed_deployment_20260925.py | `e9271d4bfc342036221d739df97ffb9c32d59bdcaa49a0bd0edadd944e1ff86c` |
| RL_PAIRED_MULTISEED_DEPLOYMENT_PROTOCOL_20260925.md | `d3ab8f93d98e9963d4b6fb62e5c57c476d5b31450616e36b96998c3c9778ec04` |
| deployment_request_20260925_r1.json | `458bbad7343bf3dcab421be7ac5f0738a88e262a061c92b0a0896159f65243a9` |

DGX新证据位于该隔离目录`evidence/`；zero/replay使用原多seed目录中单独`deployment_evidence/`的证据，绝对路径已实际核对。旧训练source、旧部署快照、运行中的训练文件均不改。

## 具体计划冻结时的状态

第四run seed20260925 parameter6最终独立审计及zero/replay已完成，replay退出0、actual600、无fallback。随后在DGX执行完整prepare，四run全部final/flat/zero/replay、原163/新165训练源、完整nominal/runtime/配方和原六fixture绑定均通过。该prepare只写计划，未启动仿真。

实际计划：[本机plan.json](../outputs/paired_multiseed_deployment_source_20260925_r1/plan.json)，DGX为相同相对路径。SHA256 `c094ca89faa946e156843aa366592b43bc943f07c89f932c990d6273c6a5f467`；状态`prepared_not_started`、`simulations_started=0`，25job，342项输入hash、173项执行源hash。完整只读构建快照仍为209文件，173是实际计划执行源清单的不同计数口径。

| 训练seed | 模式 | 六fixture learned条数 | final checkpoint SHA256 |
|---|---|---:|---|
| 20260924 | parameter6 | 6 | `1b2dfab72987e94a0afd9e14a495369a9cf730acbf3f3b34954171dcb633ad8e` |
| 20260924 | direct7 | 6 | `543bbc6bccd902f8039da4295817adc3099c72a96a11549198b3ac08cdf8e059` |
| 20260925 | parameter6 | 6 | `2547682c01dd07585323f7fba8309d7d3c74a0c9060092e816bd03408d2d4767` |
| 20260925 | direct7 | 6 | `6a29dc6a05eb2510b4f3e5f7965936ef808056e9d6f6223cc0e6da89326be30c` |

额外nominal9400仅绑定seed20260924 parameter6的训练manifest，使用zero6且不运行actor；在完整parity通过前不复用任何名义性能对照。各自normalizer、transition/final/zero/replay路径和完整hash见plan。

具体plan随后经主协调任务审核并获明确启动授权，实际driver已启动；时间/PID、再核证据、完整命令及资源见[实际启动记录](PAIRED_MULTISEED_DEPLOYMENT_LAUNCH_20260925.md)。本准备说明不代表评估完成，不填入任何未执行分数。
