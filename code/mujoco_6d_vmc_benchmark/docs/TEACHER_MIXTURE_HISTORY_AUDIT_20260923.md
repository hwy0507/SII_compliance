# ESN方向分歧：教师参数混合与接触历史审计

2026-09-23。本轮只做离线数据读取与冻结模型重放，未启动仿真、改动训练数据、重选checkpoint或修改gate。结论用于开发诊断，不能作为新的held-out性能结果。

## 当前证据支持什么

训练数据确实混合了不同VMC参数，但**抽样教师参数不能解释ESN-LP9301尾部的反向x动作**：在完全相同的600步估计wrench历史上，36组训练教师全部给出正向尾均值，而冻结ESN给出负向。另一方面，训练并非缺少持物接触：687/714条push训练轨迹都有loaded-lift接触样本。更值得继续验证的是接触持续历史、fixture与当前状态的联合分布，以及进入长期受阻状态之后的误差累积。

完整证据：

- `evidence/classical_20260923/teacher_mixture_audit.json`：36条确定性训练抽样、标签重放、固定历史多教师输出、ESN特征近邻。
- `evidence/classical_20260923/teacher_contact_support_v2.json`：全部train/validation源结果元数据、全部push短轨迹阶段对齐、真实配置去重。
- 独立工具：`tools/audit_teacher_mixture_20260923.py`、`tools/audit_teacher_contact_support_20260923.py`。服务器仅单线程运行，不实例化MuJoCo环境；不读取test轨迹。

## 参数混合是真实存在的，但不是现成的根因

对source_search_result中的实际config作排序键、紧凑JSON序列化后SHA256去重：714条训练push对应714种实际配置；227条验证push对应227种配置。这里不只是manifest的parameter_group标识不同。训练axis_rotation_rpy的各轴范围（rad）为roll [-.19436,.20034]、pitch [-.28150,.21839]、yaw [-.37969,.13136]；验证分别为[-.20349,.18672]、[-.31147,.15823]、[-.5,-.04977]。

固定抽样规则是在每个训练physical_fixture中，按SHA256(id)排序选前12条：rod/rear/combined各12，共36条。其实际源配置从零VMC状态顺序重放原记录wrench，原teacher_action最大误差仅`4.67e-8`，与保存float32精度相容；因此后面的对比使用的是有原标签校验的教师方程及真实配置。

| 固定访问历史 | 36教师尾1秒x action最小/中位/最大 | x>.01的教师数 | x<-.01的教师数 | 同历史冻结ESN尾x均值 |
|---|---|---:|---:|---:|
| 原ESN9301 | +.00764 / +.01900 / +.05970 | 28 | 0 | -.00195 |
| ESN-LP9301 | +.01894 / +.03029 / +.07445 | 36 | 0 | -.10527 |
| 已恢复VMC9301 | 数值零 | 0 | 0 | +.00534 |
| 已恢复MLP9301 | 数值零 | 0 | 0 | +.00726 |

原ESN的尾均值接近零，但存在强烈逐帧交替；实际安全slew之后的负偏置见完整因果报告。ESN-LP则在无额外slew均值偏置的情况下，原策略自身持续负向。

这反驳的是“这36组教师混合可以解释该尾段负方向”的具体解释，**没有排除全部714配置、其他时段或多值监督的一般问题**。48D输入没有显式teacher参数，但可通过历史间接包含参数作用；仅凭混合不能断言不可学习。近邻标签一正一负也不等于相同完整历史被赋予互相矛盾的标签。

## 实际首次接触与请求阶段不同

| split/scene | episodes | requested事件阶段 | 实际首次接触阶段 |
|---|---:|---|---|
| train/push | 714 | approach 714 | stage0 595（83.3%）；loaded-lift stage3 119（16.7%） |
| validation/push | 227 | approach 227 | loaded-lift stage3 227（100%） |
| train/ball | 9 | approach 8；pregrasp 1 | stage0 8；stage1 1 |
| validation/ball | 2 | loaded_lift 2 | stage3 2 |
| train/corner | 16 | approach 16 | stage0 16 |
| validation/corner | 1 | approach 1 | stage0 1 |
| train/table_corner | 102 | 该字段不存在 | 相同contact.first_stage字段不存在 |
| validation/table_corner | 25 | 该字段不存在 | 相同contact.first_stage字段不存在 |

push训练分组进一步显示：rod293与combined302全部首次stage0；rear119全部首次stage3。验证front227全部首次stage3。也就是说fixture与首次接触阶段在现有划分中耦合；不能把stage影响与几何影响独立识别。table_corner使用另一结果格式，字段缺失不表示没有接触，不能跨场景直接套stage编号。

## 训练有loaded contact，但接触持续历史和fixture联合分布不同

push短轨迹的observation/action在step前、force在step后。本工具用前一帧25Hz force范数>.05N对齐当前observation，并由原events重建stage3。源转换器虽然把时间字段命名command_time_s，实际复制的是post-step时间；审计核对源数组后减.04s。这是审计时间对齐注意事项，不是已发现的训练bug（训练按原顺序使用）。

| push统计 | train | validation |
|---|---:|---:|
| 有loaded-contact样本的episode | 687/714（96.2%） | 227/227 |
| loaded-lift总样本 | 350,458 | 122,574 |
| 其中稀疏接触样本 | 26,265（7.49%） | 40,118（32.73%） |
| 每episode累计loaded-contact样本时长中位数 | 1.12s | 7.12s |
| 每episode累计loaded-contact样本时长最大值 | 8.04s | 13.48s |

这里是25Hz接触样本累计量，不是连续接触最长段，也不是物理子步真实接触时长；不能拿它与子步contact duration直接相减。stage3样本中的绝大多数训练状态是未接触/已经恢复，scene/episode/time均衡训练并不会专门提高长接触恢复片段的权重。

每5个loaded-contact样本抽1个，得到全714训练episode中的5,545条当前状态。其Fx范围[-11.43,9.74]N、Fz[-7.68,13.07]N，ESN-LP尾均值Fx=4.98N、Fz=-4.19N在范围内。因此不能把失败简单描述为力幅度超出训练范围；逐维范围也不能证明48D联合状态或reservoir历史有充分覆盖。

## 记忆特征的局部支持：提示，而非OOD证明

36条抽样训练轨迹每5帧取1帧，使用部署时176D读出归一化特征（48D观测+128D顺序reservoir）。下列距离是query尾25帧各自最近邻RMS距离的均值，且每条训练轨迹先从零记忆按全序列计算特征。

| 9301访问轨迹 | 对36条训练子集的176D最近邻距离 | 该轨迹状态上的冻结ESN尾x |
|---|---:|---:|
| VMC | .289 | +.00534 |
| MLP | .108 | +.00726 |
| 原ESN | .719 | -.00195 |
| ESN-LP | 1.033 | -.10527 |
| MLP-LP | .193 | -.00379 |

训练参考是每条episode尾5个抽样特征到其他35条episode的最近邻距离均值，36个episode均值的中位数.030、90分位.321、最大.464。它与query尾25帧、不同访问状态的统计条件并非完全一致；这些距离只提示局部历史支持变差，不是经过校准的OOD阈值或概率。该小样本库的近邻结果不能代表全841训练episode，更不能推断所有失败都由记忆造成。

另用全部714条训练push的loaded-contact当前48D观测（5,545条）查近邻，原ESN尾距离.343、ESN-LP尾.503；这是不同样本库、维数和归一化定义，不能与上表横向相减。成功VMC/MLP尾已无接触，不适合作为这个接触限定库的反例。逐帧reset会在无接触成功轨迹制造大的虚假残差，故不作为修复。

## 预声明下一实验：固定教师的接触历史覆盖对照

2026-09-24更新：以下预声明12条已于9月23日20:19:49完成，现已独立归档审计，见 [完整结果](TEACHER_HISTORY_DIAGNOSTIC_20260924.md)。六对MJB和实际接触阶段均符合设计，但固定teacher task/strict均0/12；本批保留为失败诊断，不直接进入成功示范bank，也没有据此重训。以下保留运行前方案原文。

本轮停留在证据与方案，不重训既有模型。最有信息量的下一步是先固定一个训练来源VMC配置，采集小规模、成对的新训练/验证fixture轨迹：每个fixture分别在接近阶段和持物阶段开始扰动，记录真实首次接触与接触持续历史。在VMC控制的完整轨迹上离线评估两个冻结student的逐阶段动作误差及执行slew误差，再决定是否值得重训。这样能把教师参数混合固定下来，并区分“老师访问状态上的模仿误差”与“student闭环访问状态的累积偏移”。若物理首次接触未按设计发生，照实报告，不按结果补抽有利seed。

建议先预留3个新train fixture与3个新validation fixture，每个2种启动阶段，共12条完整24s教师轨迹；在运行前锁定几何、seed、配置SHA和动作/观测预算，校验它们与历史train/validation/test的fixture/content/hash隔离。930x与940x开发评估轨迹不进入训练。

若该对照确认长接触或恢复片段误差突出，再做独立的成对MLP/ESN变体：共同增加仅train来源的长接触/恢复片段，或同预算DAgger；VMC参数显式固定且完整顺序重放标签。两模型使用同一episode集合、同一总更新数、同一选择指标，仅train/validation选模型；原冻结proposed保留。必须同时报告不变gate、任务、物理峰值、追踪和接触恢复，不能仅凭监督MSE或更平滑动作宣称修复。新数据是否真正来自student访问状态需要明确标记，不能把离线teacher重标注称作新物理on-policy轨迹。
