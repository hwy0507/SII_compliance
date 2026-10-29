# v8真实编译模型参数核对

本轮检查已有30条三场景示范的实际`scene.mjb`，以及已完成原测试回合保存的冻结
`rollout.mjb`，没有积分物理、改变模型或进行拟合。不能仅凭脚本默认参数推断实际模型。

| 模型来源 | train / validation身份 | target_object质量 | 对角惯量（各轴）kg·m² |
|---|---:|---:|---:|
| 棍推10条 | 8 / 2 | 0.100 kg | 4.1666666667×10⁻⁵ |
| 球撞10条 | 8 / 2 | 0.100 kg | 4.1666666667×10⁻⁵ |
| 桌角10条 | 8 / 2 | 0.080 kg | 3.3333333333×10⁻⁵ |
| 原冻结测试模型 | 原12条件共用模型 | 0.080 kg | 3.3333333333×10⁻⁵ |

30个示范的物理dt均为5e−5，七执行器ctrlrange均与冻结测试模型相同。
冻结模型SHA256仍为`d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`。
全部示范MJB hash与其实际execution记录相符，collection plan hash为原`2ed3e2b9…`。

因此，“测试载荷比所有训练示范都重”不符合当前证据。测试质量/惯量确实出现在桌角示范中；
棍推/球撞载荷比测试重25%，不能把三类模型写成完全相同。质量在某一场景中出现不等于
其与方向、阶段和历史状态的组合已经被覆盖。此检查不证明真实载荷、估计外力、动力学、
任务监督或轨迹相同，也不能单独解释或排除质量与其他因素的交互作用。

后续保持已经登记的八球v5方向控制，核实际可达性和接触后再决定正式三场景数据。
不据此改变质量、冻结环境或gate。已有方向覆盖与读出外推证据仍需通过真实控制验证。

03:27:03 UTC完成的[准确检查](evidence/NONRL_INTENT_RECOVERY_20261029/V8_SAVED_MODEL_PARAMETER_INSPECTION.json)
包含原检查源码、31个模型的绝对路径/hash/参数和比较结果。34589bytes，SHA256
`5b64c673a4ff0855b9d77b4037196ca0b3b9c6d943e8b90905b6dd5e6bfe256f`。
只读服务`sii-v8-model-parameter-read-20261029.service`自然exit0，runtime5.655s/CPU3.485s。
请求单CPU affinity6、单数值线程、128MiB、禁swap；记录memory.peak134217728bytes，
达到cgroup上限（包含文件缓存等计费），不声称具有内存余量或OOM事件计数为0。

这不是第五条件轨迹审计，未执行正在等待用户回复的该动作。原108/原后处理继续，
Goal active。开工main9f9531d5/baselinef6e8f8c实际fetch/read。
上一轮为低内存审计准备progress；本轮新增真实模型参数证据，并核验原科学持续推进。
03:21:16.798–03:31:16.978 UTC共21次原PID/start保持loaded/active，完整回合50→52，
原cgroup最大1597509632bytes、OOM/oom_kill/swap0。主机MemAvailable4492660–4763536kB，
全机swap仍近满；两种swap口径分开。observer59582自然exit0，原科学继续，收尾已53/108。
[完整观察](evidence/NONRL_INTENT_RECOVERY_20261029/V8_FROZEN108_VERIFIED_WAIT_0321.json)
41164bytes，SHA256 `fafffc5592ab4ab5a592be3bb627c6bd4fcf5b25971fb5e956071f1313301d2a`。

参数检查与观察两份原件均含实际代码，已逐成员及暂存/最终大小hash核共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_model_parameters_wait0321_20261029_v1/EVIDENCE.tar.gz`。
6189bytes，SHA256 `4eaabd90854290c486b64f39b5ff2cc6559b4a4e7414984b033f78f9dbd8dc10`。
不含本报告或在途物理全集。第五条件新审计仍等待原用户问题的回复，未重试；
原完整后处理继续，不因此暂停Goal。
