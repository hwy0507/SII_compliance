## 2026-10-30：球撞全九模型保存历史诊断，不把低MSE等同恢复成功

新增分析脚本`code/mujoco_6d_vmc_benchmark/experiments/diagnose_contact_yield_ball_support_20261030.py`、[完整数值](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_BALL_SUPPORT_DIAGNOSIS_20261030.json)及[三家族九回合诊断图](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_BALL_SUPPORT_DIAGNOSIS_20261030.png)（另有PDF）。来源为本次完整27开发中的真实ball00轨迹，不是旧场景或合成曲线。零新增物理/optimizer/test输入；九学生全750帧精确actor重放、dataset/模型/原review/指标hash核验。

结论进一步收窄：

- 三RNN对全部24条teacher训练历史的requested-action MSE约1.05–1.09e-5，比ESN的1.14–1.27e-5更低，但球撞闭环3/3失败、ESN3/3成功。不能简单归因“训练步数少或整体拟合差”，teacher-history平均MSE不足以验证闭环恢复。
- RNN01/02/03的20–30s平均向上requested yield分别0.06863/0.02936/0.04046m/s；同一保存历史的反事实teacher分别约0/0.000345/0.000387m/s。这是动作偏差的实证线索；requested yield并非实际末端速度，不能直接作为实际抵消量/因果证明。
- 使用与MLP/RNN一致的18字段、train-only归一化/clip/绝对值扩展，对12600训练帧做精确最近邻RMS距离。六个validation身份的全部帧距离p95=0.181445（球两validation p95=0.169246）。RNN01和MLP01后期全部高于前者，支持覆盖不足线索；但失败RNN02后期距离中位0.0663、全部低于前者，故该距离不能解释所有失败。它不包括RNN hidden history，不是校准OOD概率，低于p95不证明充分覆盖或可恢复。
- 成功MLP03后期反事实动作MSE0.01079，高于失败RNN02的0.001184，不能将此误差直接作为成功判据、选模指标或任意新增门槛。阶段不同、teacher内部历史及闭环反馈都可能影响对应关系，尚未分解因果。

六神经checkpoint的normalizer与重新计算值最大差1.11e-16（浮点求和顺序），绝对输入标志一致；原先逐位normalizer断言因此失败，改为明确数值容差后全部通过，未发现归一化部署bug。四条真实观察独立直接减法/平方/最小值与cdist距离完全一致。PNG已目视检查；三列纵轴独立标注，不能凭曲线高度跨列比较。

下一步仍是已具体化的真实teacher恢复验证及共同纠偏数据决策，不能把本反事实/距离图当新增成功示范。四条探针的自动审批拒绝尚未解除，未执行登记/采集，也未绕过。两原服务本轮宿主核实inactive/PID0、最终108零派发；Goal active。

## 2026-10-30：完整27开发审查结束，实际恢复探针待明确授权

原诊断和final108等待器均已自然inactive/PID0；完整独立review与本轮保存文件hash核验一致。开发结果为三个train00身份×三seed，不能称unseen泛化：

|方法|Task|Strict/双成功|机器合规|棍/球/角双成功|
|---|---:|---:|---:|---|
|ESN ridge|9/9|9/9|9/9|3/3、3/3、3/3|
|RNN|6/9|6/9|9/9|3/3、0/3、3/3|
|MLP|8/9|6/9|8/9|1/3、2/3、3/3|

新teacher已让ESN三个场景开发身份全部通过；不能延续“新ESN整体退化”的假设，也不能据此认定最终主矩阵已修复。失败仍集中RNN球撞后恢复、MLP棍行为/穿透及一条球恢复。四条球失败都属于任务失败，不能用低峰矩/机器合规或失败SPT美化。当前主矩阵待，最终108后继按原协议明确`development_not_qualified_no_final_dispatch`，从未读取最终条件/派发测试。

完整小证据：[CONTACT_YIELD_COMPLETE27_DEVELOPMENT_20261030.json](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_COMPLETE27_DEVELOPMENT_20261030.json)，含27原指标、原独立actor/filter精确重放、三家族/场景汇总与失败清单。此次仅独立核原hash和记录，没有新物理积分。新raw仍仅本地，不能宣称服务器归档。

### 下一项具体修复实验

新增独立`experiments/contact_yield_recovery_campaign_20261030.py`与worker/auditor，未改任何已绑定工具/物理源码。四条均使用失败学生seed01与原train00条件：MLP棍7s后接管、RNN球10s/20s后接管、MLP球10s后接管；运行到原20/30s完整时域。当前同配置VMC teacher沿实际学生历史预热，再真实接管；学生前缀与原失败轨迹逐数组严格配对，保存全部失败；独立重放动作/filter及原Task/Strict/机器门。不改teacher/门槛/物理/测试，不做拟合/模型重选。若后缀合格，仍需另登记三家族共同纠偏数据协议，禁止把反事实前缀作为实际成功示范。

四条原保存历史上，独立纯controller预期与switch算子精确一致、学生完整重放精确一致，三种非法prefix被拒绝；控制证据`CONTACT_YIELD_RECOVERY_OPERATOR_CONTROLS_20261030.json`。这只是零物理控制，未证明教师实际恢复能力。RNN01后期向上残差约.069m/s、名义向下约.067m/s的抵消是待检验线索，非唯一因果证明。

**登记命令两次被自动审批拒绝**：审批明确认为现有修复/重采授权未覆盖这四条具体teacher接管干预，要求用户明确批准。未绕过、未创建新run目录或启动服务；已向用户展示具体四条设计及资源边界请求批准。其余独立核验、源码和文档交付继续。Goal active；解除这一明确审批阻碍后才执行依赖动作。

## 2026-10-30：开发15/27，球撞出现任务恢复失败

原服务同PID1838688/Invocation6e4b70f18e2646e1b3dced9c0b0f5f9b持续active；球撞前六条完整，ESN01/02与MLP02 Task/Strict/machine均true，RNN01/02与MLP01 Task/Strict false但machine true；当前ESN03球在途，最终108仍等待/零派发。

新增只读 `CONTACT_YIELD_FIRST4_BALL_DIAGNOSIS_20261030.json` 只涵盖首四球回合：原审计/qualification输入hash及完整750动作/600000子步核验；ESN01/02任务阶段5、终点误差7.265/6.235mm；RNN01/MLP01仍阶段0、误差41.714/147.862mm、无抬升，真实球接触且无穿透/上游接触/物理失败。反事实teacher在各学生保存状态的20–30s动作MSE依次ESN01 .00059735、RNN01 .00743459、MLP01 .01626974、ESN02 .000087985。反事实不是实际教师接管证据，不能单独证明恢复能力或因果份额；优先调查撞击后动作学习/任务恢复不足，不能因机器安全就算成功。全27完整后再登记公平修复，不改变活源/选模/gate、不看最终test。

## 2026-10-30：棍推九条完成，已接续球撞

固定rod00开发身份的九模型回合全部完整结束：ESN三seed Task/Strict/machine3/3；RNN三seed同为3/3；MLP Task3/3、Strict1/3、machine2/3。MLP03实际双成功；MLP01行为失败、MLP02穿透安全失败保持。不能把单开发条件结果扩展为最终测试成功率，不计算开发SPT或重选模型。

新增 `CONTACT_YIELD_ALL9_ROD_DEVELOPMENT_20261030.json` 保存九条真实METRICS/行为门/来源hash、原actor/filter审计输入hash及完整500动作/400000子步记录核验，全部失败保留。没有新独立动力学积分。两活登记source清单一致，原服务PID1838688/Invocation6e4b70f18e2646e1b3dced9c0b0f5f9b自然接续ball00：首ESN01 Task/Strict/machine均true，当前总计10/27，RNN01球已350动作/280000子步；无OOM/swap、内存约1.99GB/3GiB。最终108仍waiting/零派发，全27后再审查修复与最终比较安排。

## 2026-10-30：前六条审计与两种MLP失败分离

固定诊断完整6/27，均为rod00训练身份：ESN01/02与RNN01/02 Task/Strict/machine均true；MLP01 Task/machine true但撤回前未越棍回位；MLP02 Task true，行为顺序实际通过（9.60s越棍、11.48s持续回位确认<12.80s撤回），但安全门失败。MLP02外穿透峰0.219492mm超过原0.2mm，第一次超限4.74110s、峰4.74165s、26子步共1.3ms；并非执行器超限或actor/filter部署错误。不能放宽门槛消除失败，也不能把两条失败均归为没有蹭棍。

新增 `CONTACT_YIELD_FIRST6_DEVELOPMENT_REVIEW_20261030.json`：逐条METRICS与原独立actor/filter审计、qualification输入hash核验；重新读取六条各400000子步并独立复算穿透峰/首次超限/时间。Task6/6、Strict4/6、machine5/6仅为固定开发前缀，不是最终成功率或家族排名；六条完整、失败均保留，不算开发SPT。原服务同PID/Invocation继续第三seed ESN，OOM/swap0，final108后继仍等待/零派发。完整27结束后再形成公平修复方案。

## 2026-10-30：前四条完整，MLP首条失败已定位到行为门

原诊断PID1838688/Invocation6e4b70f18e2646e1b3dced9c0b0f5f9b持续active，完整4/27：rod00的ESN01/RNN01/ESN02 Task、Strict、machine均true；MLP01 Task/machine true、Strict false。MLP接触4.76635s、让位4.88s均有效，但12.80s棍撤回前没有越棍/持续回位；完整20s、500动作/400000子步、actor/filter replay均通过，峰矩39.105Nm/穿透0.037771mm，无数值或执行器违规。失败完整保留，不能当双成功/SPT样本。

只读前3条开发rod00轨迹，在各学生保存观察序列上重放teacher作为反事实动作比较：接触至撤回窗口requested-action MSE，ESN01 1.10263e-5、RNN01 3.23786e-5、MLP01 .00202966。MLP逐维输入均未超出整个训练集的min/max，不能以此排除联合状态组合偏移；不能把反事实teacher输出当实际可恢复的物理示范。当前证据支持优先调查MLP动作拟合/历史依赖与闭环累计偏离，尚未证明各因素因果份额，也不能据单开发身份改选模型。证据 `CONTACT_YIELD_FIRST3_CLOSED_LOOP_DIAGNOSIS_20261030.json` 含真实指标、行为审计、逐通道误差/反事实均值、逐维包络、输入与源hash；无新物理、拟合或unseen读取。全27仍按固定顺序继续，最终108后继等待/零派发；全27 review后决定共享开发数据/公平修复方案，不修改活协调器。

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
