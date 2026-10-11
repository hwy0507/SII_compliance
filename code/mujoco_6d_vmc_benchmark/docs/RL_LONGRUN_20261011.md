# 10月11日晚一次性baseline长时任务

用户要求下班后继续监视与过夜推进，不使用定时任务。开工核对远端main
`6c6c83413d3076b3e3e5206cb77bf44f06ea1ab2`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及两日志/AGENTS。
工作区已有未跟踪`docs/MEETING_FLOWCHART_IMAGE_PROMPTS.md`不属于本任务，未动/未提交。

## 实际运行与完成边界

保留12:01启动的recovery_20261011_v1及其冻结源码、登记、在途worker、checkpoint，
没有重启稳定训练或再启动第三个模拟器。两路各1线程/MemoryMax3GiB/禁swap，
全部计算仅airpig本机。19:27可用内存约1.6GiB，不新增训练并发；磁盘可用337GiB。
服务器仅接收小型审计包并核验hash，不使用服务器训练/渲染/仿真。

现有队列的安全截止保持2026-10-12 12:01:50 CST，不伪改已加载的登记或无缝延长承诺；
trainer到截止在当前回合结束后落盘。若整队列未完成，保留部分checkpoint与pending，
报告尚缺哪些方法/条件。用户本次未指定小时数，不宣称授权了新的15小时。
今晚按原队列完成导纳/VMC后自动接续其余配置；当前不能承诺七组明早全部完成，
也不把到达165k或零成功视为“调参充分、可直接投稿”。

19:30快照：

| 方法 | 实际节点 | 开发Task | 开发Strict | RMSE mm均值 | 回合峰矩均值Nm | 回合峰速均值m/s |
|---|---:|---:|---:|---:|---:|---:|
| 直接动作office_task | 163927 | 0/8 | 0/8 | 20.088 | 40.531 | 0.3447 |
| RL调阻抗 | 165000 | 0/8 | 0/8 | 21.352 | 50.136 | 0.3752 |
| RL调导纳 | 90750（训练中） | 待评估 | 待评估 | — | — | — |
| RL调VMC | 82500（训练中） | 待评估 | 待评估 | — | — | — |
| direct_metric/两组historical entropy | 本次未接续 | 待评估 | 待评估 | — | — | — |

前两项都已经有完整八条件独立审计，引用原始审计而非将训练回合成功率冒充评估。
经典90回合已完成的结果仍见BASELINE_OVERNIGHT_CLOSEOUT，不重复搜索。
本表是RL开发预算节点，不是proposed与所有baseline最终统一测试。

## 连续监视、汇总和故障处理

- 现有一次性协调器和30秒连续监视器保持运行，没有新增timer/cron/heartbeat。
- 新服务`sii-longrun-report-20261011-v1.service`19:30实际active，MemoryMax256MiB/禁swap，
  只做标准库读取/hash/小包归档。每60秒汇总七配置的实际训练步数和已审计开发节点。
- 每个新节点核对审计hash、8个唯一development身份、Task/Strict逐行计数、checkpoint各文件hash。
  保留早停在分母内，列出full_horizon和阶段分布；没有评估明确pending，不使用0/0。
  原独立子步/动作审计由现有worker和节点审计完成，本汇总不声称重新运行物理。
- 监视器ALERT或快照超过300秒不更新，会写本run的STOP_REQUESTED请求回合边界停机；
  不杀worker、不发进程组信号、不覆盖故障、不自动重启。若当前回合自身挂死，
  cooperative marker不能强制救活或终止它，需后续人工/agent诊断。
- 外层终止后写CLOSE；实验失败保留为失败并非零退出，不把systemd成功字样当作实验成功。
  汇总程序自身异常写ALERT；不承诺自动修复未知故障或agent在会话结束后永久在线。
- 首节点和每个新审计节点、终止时导出独立服务器小包。传输或核验失败记录EXPORT_FAILURE，
  不影响训练、不声称共享完成、不删除本地文件。新大轨迹仍本地，未做全量归档。

4项回归通过：早停保留分母、checkpoint篡改拒绝、条件身份替换拒绝、pending不伪造零成功。
真实首轮四个已有开发节点（两个110k、两个165k）的证据和checkpoint核验成功。

本机实时入口：
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/rl_longrun_report_20261011_v1/LATEST.md`
和LATEST.json。运行与监视原收据位置见RL_RECOVERY报告。

首轮已逐文件核验发布：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_longrun_report_20261011_v1_001/evidence/`。
8文件178372字节，manifest
`039c5ba20d3f73b074d0bc6899e355f33568456dc739012b44fb41dc55d07d48`。
包含汇总源码、登记、四个审计和REPORT.json/md；不包含原始轨迹或checkpoint实体。
未来包_002等仅是预定命名，不提前声明存在或已核验。

已完成：过夜运行状态/资源检查、汇总和节点归档服务启动、首轮结果/权重核验及服务器发布。
运行中：RL导纳/VMC与原监视、长时报告服务。未完成：剩余配置/节点、多seed与最终统一对比。
