## 2026-10-30：75拟合完成，固定27已实际接续

全部75拟合完整完成，原训练服务自然inactive/PID0。FIT_AUDIT通过，九模型锁定hash `105f3dfd36d026980963ff8fa3c335af771b8b7e163f26f0bf9664e060f13091`。本轮逐文件核验75个checkpoint及metadata hash、九模型共同validation最小值选模；原FIT_AUDIT包含九模型各15750帧部署actor精确重放误差0，不是闭环成功证明。证据 `docs/evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_ALL75_FIT_COMPLETION_20261030.json`。

原诊断服务PID1838688/Invocation6e4b70f18e2646e1b3dced9c0b0f5f9b已自动diagnosis_run。首条rod00/ESN seed2026102801完整20s、500动作/400000子步，保存审计Task/Strict/machine均true、actor/filter replay通过；接触4.73095s→让位4.84s→越棍7.20s→持续回位确认7.28s<撤回12.80s，峰矩35.1269Nm、穿透0.070846mm。完成时间8.84s使用终态13样本确认语义，不与棍回位80ms门混同。此条是训练身份开发回合，非全27、非unseen泛化；人体舒适通道缺测NA，接触代理不当真人舒适度。当前RNN seed01棍推已实际推进125动作/100000子步，最终108仍零派发。科学失败将保留并在完整27后定位修复，不重选模型。

# 新teacher数据重训后的学生闭环诊断入口

新脚本位于 `code/mujoco_6d_vmc_benchmark/experiments/diagnose_contact_yield_students_20261030.py`。仅准备完成，尚未登记或派发物理回合；完整采集和75个训练作业仍是前置条件。本轮没有读取未见测试条件文件或测试轨迹。

旧开发目录和未见测试入口硬绑定旧 v9 dataset SHA、模型 catalogue、选模目录与服务。直接把新数据模型塞入旧登记会混淆来源。本入口另建登记，复用未改的物理worker、单回合审计和action/filter重放；不改历史入口，也不冒用旧模型资格。

## 固定范围和决策

对 `contact_yield_scrape_retrain_20261030_v1/MODEL_LOCK.json` 已按六开发validation MSE锁定的九模型，统一运行 rod00/ball00/corner00 三个 train 身份，共27条。不会按结果重新选择checkpoint或替换seed；不会扩大调参预算。它是闭环诊断，不是追加训练或新的选模规则，也不是主结果。

每条检查：当前checkpoint/metadata hash，物理MJB、初始canonical48与同身份合格teacher逐数组配对，场景参数/seed、同公共filter、source inventory、dt5e-5与完整预登记时长。沿用独立逐子步有限/矩/速度/外穿透审计、原Task/三特化Strict/终态保持语义、棍推接触—让位—越过—撤回前持续回位以及actor/filter重放。

全部27条可读科学失败都保留并执行完整名单；基础设施异常停止、保存已完成前缀和当前身份，不自动重试。独立完整review重算每条指标与action/filter，不从既有passed字样推断通过。开发诊断不计算局部T_ref或SPT、不发布最终排名。若出现新失败，先据teacher/student配对证据定位数据/学习/接口，不能自动归罪ESN或改变最终门槛。

## 派发前置和入口

须当前采集与训练接续两个服务inactive，30条完整独立资格passed、75fit/108候选和九冻结模型独立审计passed，且来源hash一致。只有此时才能登记一个不存在的新目录：

```bash
# cwd: code/mujoco_6d_vmc_benchmark
# 使用 .venv-sii-local-rl/bin/python；物理服务 CPU6、单线程、MemoryMax3GiB、swap0。
python experiments/diagnose_contact_yield_students_20261030.py prepare --root outputs/contact_yield_student_development_20261030_v1
python experiments/diagnose_contact_yield_students_20261030.py run --root outputs/contact_yield_student_development_20261030_v1
python experiments/diagnose_contact_yield_students_20261030.py review --root outputs/contact_yield_student_development_20261030_v1 --output outputs/contact_yield_student_development_20261030_v1/REVIEW.json
```

上述命令为待执行协议，**本轮未运行**。run必须通过systemd资源约束，不能直接在普通shell派发。新入口获取独立协调锁，并检查公共物理锁；原worker仍负责真实物理锁。不得覆盖已有/不完整目录；运行后禁止编辑注册源。

## 当前验证范围

[零物理控制](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_STUDENT_DIAGNOSIS_CONTROLS_20261030.json)覆盖27项完整顺序、保留全部科学失败、第四条基础设施异常保留前三与当前身份、重复启动拒绝、少模型/重复seed或名/少场景/validation冒充train拒绝、活动前置拒绝、未完成review拒绝。

[真实保存轨迹配对控制](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_STUDENT_PAIRING_CONTROLS_20261030.json)基于新teacher的rod00初态，正确配对通过，错误MJB、filter或初始canonical48均拒绝。没有mj_step、拟合、旧模型新评测或最终测试，不能把这两个控制称作27条实际通过。

原唯一采集服务与等待器保持运行；当前目标仍是完整新数据、公平三模型训练、冻结未见108及六指标主矩阵。最终测试必须另适配新模型来源并登记，不能调用旧v9硬绑定register冒充新主结果。真实人体舒适缺通道仍NA、代理分列；旧综合场景数据保留历史，不混入新主结果。

## 当前teacher棍推全量复核

原服务PID1827286/Invocation ec3b6f480c184966bf86c5def563210d保持；三次宿主级活体观察确认从rod08的475step/380000子步接续至ball00的150→325step/120000→260000子步，未重启。10条棍推全部独立资格通过，真实actor重放、同参数/初态/MJB/filter核验及各原行为审计都通过；这是8 train/2开发validation身份，不是新学生成绩。

[完整10条棍推复核](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_ALL10_ROD_INDEPENDENT_REVIEW_20261030.json)与[真实事件图](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_ALL10_ROD_TIMING_20261030.png)：每条都实际接触、让位、越棍并在撤回前持续回位，回位确认领先撤回1.24–5.59秒；此前失败的rod09现在领先2.19秒。图的回位门是5mm管道/80ms，与最终Task完成保持0.48秒属于不同语义，不能混用。时间来自真实物理接触子步及40ms几何采样，没有用命令时间代替实测。

球/角仍在原单路采集，尚不能声称30/30、新数据拟合或最终108完成。三次观察内MemoryCurrent最高约1.705GB/3GiB、OOM0/实验swap0，等待器仍未提前派发。新raw仅本地；之前服务器raw导出限制未通过本轮绕过。
