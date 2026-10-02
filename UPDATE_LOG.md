## 2026-10-02 — baseline 发布与交接归档核验

- 最终结果/协议提交 a788be958486b5b24bc546737d44f690763521ba 已正常push到baseline；远端main仍7cd5f4b。只读归档 /home/arm1/sii_shared/SII_compliance/source/a788be958486b5b24bc546737d44f690763521ba/ 的2748个文件、64,416,368字节逐Git blob核验一致；清单在 /home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/PUBLISHED_SOURCE_ARCHIVE.json。
- 同一runtime根新增 FINAL_HANDOFF.json，汇总13方法的选定checkpoint、测试/展示/office目录、归一化/推理hash与16项证据文件hash；明确当前bridge只适配7cd5f4b，新WBC须另建共同cohort，不因48维形状相同就默认语义相同。
- 高速失败的额外针对性核验 HIGH_SPEED_EFFORT_LIMIT_AUDIT.json：5条旧桌角>4m/s回合的实际7关节驱动力矩仍在模型[87,87,87,87,12,12,12]Nm幅值内；不据此声称速度、slew、无源或整体安全通过。原穿透/task/strict失败不变。
- 共享checkout后续的22a59a3属于另一agent的视觉/WBC更新，未接入本轮冻结实验。原五小时窗口剩余时间用于交接与归档核验，没有新训练、改测试门槛、定时任务或删除失败。本日志是新增交接索引，实际实验实现与结果源码快照仍精确指向a788be9。

## 2026-10-02 — Make PickPlace objects visually explicit in the FR3 benchmark

- Fixed the user-visible PickPlace ambiguity in experiments/robosuite_style_fr3_benchmark_20261002/run_benchmark.py: the static pick object is now a saturated orange front-edge cube with a yellow beacon, and the static place target is a green ring with a raised flag. The pair is positioned away from the storage bin and rendered from a front camera so both are identifiable.
- Updated the benchmark panel to state PICK orange cube -> PLACE green flag, and updated the server detail page plus the main FR3 page to describe the actual task pair and its static-object limitation.
- Re-ran the independent FR3 + FLASK + computed-torque WBC benchmark with the robosuite virtual environment and --time-scale 2.0: 31 scene collision geometries, 23 sensors, HOME-to-GOAL direct edge unavailable, 2 route segments, 8.1329 s trajectory, 176 frames, 0 maximum contacts, 31.81 Nm peak command torque, 0.00960 rad peak joint tracking error, and 0.00922 rad final joint error.
- Server media: /home/arm1/vmc_mujoco_runtime/robosuite_style_fr3_benchmark_20261002_pickplace_v5.mp4 (copied to /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/robosuite_style_fr3_benchmark_20261002/robosuite_style_fr3_benchmark_20261002.mp4 and /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/flask_fr3_20261002/flask_fr3_realtime_plot_complex.mp4) with JSON report /home/arm1/vmc_mujoco_runtime/robosuite_style_fr3_benchmark_20261002_pickplace_v5.json.
- Validation: python -m py_compile passed; the mid-frame was inspected and shows both colored task markers; HTTP-served MP4 replacement completed. This remains a development visualization: no finger actuator, free-joint object, grasp state machine, or physical pick/place success claim.
- Source main inspected: ba84ed8a39ed743f603aa5d60e901bdf87090e1d; baseline before this batch: e7c970118c0114e65d8d2f897e9472ae58cbe7af. GitHub fetch/push remains blocked by missing HTTPS credentials; this commit is retained locally on baseline.

## 2026-10-02 — 四视频 baseline 终评完成与最终环境六组建议

- 原五小时窗口07:36:31–12:36:31 UTC；训练已按11:40 cutoff结束并保存末回合。13模型×12保留条件=156/156、13模型×4展示锚点=52/52、固定main综合迁移11/11均完成；未用测试选权重，全部失败保留。最终报告 docs/PRIMITIVE_BASELINE_RESULTS_20261002.md；完整矩阵和逐场景结果均有实际接触、task/strict、时长、RMSE、实际峰矩/峰速及数值/穿透通过数。
- 共同周期checkpoint：直接SimbaV2两reward×两seed均60000；在线导纳/阻抗/VMC均40000，按截止前共同可用周期选择。三参数训练最终61175/61175/47475。第一seed原CLI失败恢复导致各多1525物理交互；PHYSICAL_EXPOSURE_FINAL.json明确实际曝光61825，恢复不是精确运行中环境续接。
- 保留task/strict：zero3/3，grid导纳3/3，grid阻抗6/3；统一BO先验固定导纳3/3、阻抗6/6、VMC5/5；在线调参3/3、6/6、4/4（各分母12）；四个直接RL均0/0。旧桌角有5条>4m/s失败，参数导纳11.98095m/s、VMC14.45098m/s；物理检查均失败，HIGH_SPEED_FAILURE_REVIEW.json保留原生复算证据，不宣称局部能量账本保证实际运动安全。
- 新office同一归档MJB11条迁移全部完整55s且task/strict=false；固定/调参停carry、直接RL停approach。原ESN历史参考也失败，但训练经历不同。全扰动zero不是无扰动可行性对照。docs/FINAL_ENV_BASELINE_PROTOCOL_20261002.md新增N0/B1/H1/R1/E1/C1明确设置、共同抓稳初态、正式步长/难度冻结及动作空间差异；±20%激励范围仅提案，未改冻结场景或另一agent WBC。
- 原四视频球是实际手位置相关的首次发射，非完全相同入射状态；52条原生球轨迹非发射速度跳变为0，最大位置积分残差1.80e-15m，动量残差1.37e-16Ns。208条测试/展示的72,384,000子步指标复算通过。这证明日志一致性，不证明接触材料真实。旧球9mm柔性层/.012s solref，新office零margin/.0004s，实际模型清单BALL_CONTACT_MODEL_INVENTORY.json明确两者差异及内核穿透语义。
- 三个独立注册3s名义步长探针1e-4/5e-5/2.5e-5完成；最细相对最粗冲量-0.99%、峰速-0.57%、峰力-18.09%。峰力仍敏感，不冒称完整正式dt结果。参数限幅/限速/局部账本、48维观测/7维公共输出、模型和配置配对及推理归一化冻结均通过；阻抗的力矩控制律差异保留。
- 所有代码/数据/媒体在Spark。根 /home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/ 下 final_evaluation01、final_reference01、final_report01、parameter_rl/final_diagnostics01、office_bridge/{transfer01,transfer_report01,numerical01}、FINAL_NATIVE_AUDIT_SUMMARY.json、MEDIA_METADATA_AUDIT.json、HTTP_PUBLICATION_AUDIT.json。52个四场景完整视频及11个综合完整视频全部导出；98完整/近景文件编码元数据与首帧检查通过，232页面/媒体链接HTTP200；代表接触拼图、参数/轨迹图、综合全过程代表帧已目视核对，未声称看完所有视频。
- 页面 http://192.168.31.70:8765/primitive_baselines_20261002/ 与 results.html、office/ 已更新。代码位于 code/mujoco_6d_vmc_benchmark/experiments/{primitive_baselines_20261002,parameter_rl_20261002,office_baseline_bridge_20261002}/。本次新源码是审计/展示/汇总及3s独立数值诊断，未热改训练快照。
- 收尾核对main仍7cd5f4b7ac0a3056df76ac62bc690ded0724b104；此前已发布baseline068f0bf，共享HEAD含另一agent已提交WBC工作e7c9701。只暂存本任务文件，保留其未提交run_benchmark.py；只push baseline。当前本轮仿真/导出均结束，四个历史暂停训练PID1150890–1150893保持暂停，无定时任务。正式完整dt=5e-5、新WBC统一cohort及文献全文复现仍未完成。

## 2026-10-02 — FR3 hand asset and collision audit correction

- 修复用户指出的末端穿模和 hand 建模问题：upstream fr3v2.xml 只到 link8，wrapper 现在注入 menagerie 的官方 Franka hand/finger mesh，使用 Panda 官方 link7→hand 旋转；本轮固定为 open-gripper 几何，不声称已有夹爪 actuator。
- 将旧的绿色 target marker 从可能与运动臂视觉重叠的 [0.32, 0.25, 1.10] 移到后方层板区域 [0.78, 0.32, 1.10]。
- robot / obstacle collision audit 均收紧为 contype != 0 的几何体，视觉 mesh 不再被错误地当成碰撞障碍。
- 0.2 s hand asset audit：13 个机器人碰撞几何，其中 hand/finger 5 个；13 个场景障碍几何；23 个传感器；最大接触数 0；HOME 时末端 site 世界坐标约 [0.55565, 0.00023, 0.53595]。
- 修正后的 robosuite-style FR3 视频重新生成并替换网页 MP4：<http://192.168.31.70:8765/flask_fr3_20261002/>；详情页：<http://192.168.31.70:8765/robosuite_style_fr3_benchmark_20261002/>。
- 代码涉及 `experiments/flask_fr3_env_20261002/run_sensor_wbc.py` 和 `experiments/robosuite_style_fr3_benchmark_20261002/run_benchmark.py`；未删除既有实验输出。
- 限制：固定 open hand 解决资产和穿模显示问题，但真正 PickPlace 仍需后续加入 finger joints / actuator 和 free-joint 物体。
- 本轮基线为 `185eb9e4430ad0096a5c3715db9397d3c3fbeb41`；GitHub push 仍因 HTTPS 认证无法读取用户名而失败。

## 2026-10-02 — FR3 robosuite-style tabletop benchmark

- 新增独立实验目录 `code/mujoco_6d_vmc_benchmark/experiments/robosuite_style_fr3_benchmark_20261002/`。它保留 upstream FR3、FLASK joint planner 和 computed-torque WBC，并加入按 robosuite Stack/PickPlace 组织的工作台任务层：带边沿收纳箱、工具托盘、两个堆叠方块、可拾取圆柱、绿色目标位、柜体侧板/层板和桌面围板。
- 参考脚本：`run_benchmark.py`；说明：`README.md`。脚本同时提供 MuJoCo offscreen render、右侧 WBC 指标面板和碰撞几何审计。
- 服务器运行环境：`/home/arm1/vmc_mujoco_runtime/robosuite_wbc_venv`（MuJoCo 3.3.7）；运行输入：`/home/arm1/vmc_mujoco_runtime/mujoco_menagerie/franka_fr3_v2/fr3v2.xml`。
- 2026-10-02 reference run：31 个场景碰撞几何、23 个传感器；HOME→GOAL 直达边为 false；FLASK 生成 2 段轨迹；2x retime 后轨迹时长 8.133 s、176 帧；最大命令力矩 27.41 Nm；峰值关节跟踪误差 0.00980 rad；最终关节误差 0.00940 rad；仿真最大接触数 0。
- 结果媒体：`/home/arm1/vmc_mujoco_runtime/robosuite_style_fr3_benchmark_20261002.mp4` 和同名 JSON；网页：<http://192.168.31.70:8765/robosuite_style_fr3_benchmark_20261002/>。本轮网页视频和页面均通过 HTTP 200。
- 限制：Stack 方块和 pick object 当前是静态任务物体，用于验证场景、碰撞、轨迹和 WBC 数据通道，不声称完成抓取成功；下一步再接 free-joint 物体和抓取/放置阶段。
- 开工基线：baseline `b1f26846a08c622b3c9d7f47a60e8d23c1c9c6e4`；工作树保留其他 agent 未提交修改，未清理、未覆盖。GitHub push 仍因 HTTPS 认证缺少用户名而失败。

## 2026-10-02 — robosuite 1.5.2 WBC 场景参考运行

- 开工检查：baseline 当前 HEAD `c9a4e94a68a243e98970dcb82323b999a24f42c6`；已 fetch `origin/main` 和 `origin/baseline` 并读取两份 UPDATE_LOG.md。工作树已有其他 agent 的修改和未跟踪文件，本轮未覆盖或清理。
- 新增参考脚本：`code/mujoco_6d_vmc_benchmark/experiments/robosuite_reference_20261002/render_stack_reference.py`。
- 新增调研记录：`docs/WBC_SIM_ENVIRONMENT_SURVEY_20261002.md`，比较 robosuite、Isaac Lab、MuJoCo Menagerie、Drake、Pink、ManiSkill、RoboCasa，并说明 FR3 接入路线。
- 独立运行环境：`/home/arm1/vmc_mujoco_runtime/robosuite_wbc_venv`，robosuite 1.5.2 + MuJoCo 3.3.7；官方 Stack + Panda + BASIC composite / OSC_POSE 正常创建并运行。
- 参考媒体：`/home/arm1/vmc_mujoco_runtime/robosuite_wbc_reference_20261002/robosuite_stack_reference.mp4`；288 帧、20 Hz、最大 MuJoCo contact=13、末端误差均值=16.6 mm。网页：<http://192.168.31.70:8765/robosuite_stack_reference_20261002/>。
- 该视频是场景和数据通道的 reference run，使用 waypoint 控制，不声称 learned stacking policy 成功；Panda 也不等同于最终 FR3。
- 验证：robosuite Stack headless/offscreen run 成功；参考视频和 HTML 均通过 HTTP 200；未向 GitHub 推送（当前认证仍无法读取 HTTPS 用户名）。

## 2026-10-02 — 首批保留测试、分场景报告与接触公平性方案

- 两reward×两seed直接SimbaV2主训练均完成，第一seed60300/第二seed61175实际计数；统一采用60000步周期checkpoint。导纳参数RL也完成61175步；阻抗与VMC继续，VMC已在metric第二seed结束后接替空闲槽位，仍最多四路仿真。
- 首批完整保留测试：zero task/strict=3/12、接触12/12；metric seed74001 task/strict=0/12、接触10/12；office_task seed74001 task/strict=0/12、接触11/12，均完整时长。三模型共36回合原始子步指标复算通过；发生球撞的原生动量残差约1e-16 Ns。这只支持记录数值一致，不是材料真实性或硬件安全证明。
- 新audit_protocol.py核对保存的48维观测、7维公共输出动作、40ms周期、实际模型hash配对和推理归一化冻结；首批30条快照通过，其余将随完成补齐。新增publish_report.py和office plot_transfer.py，结果页 http://192.168.31.70:8765/primitive_baselines_20261002/results.html 明确未完成分母、分场景结果与新综合迁移分组。zero/历史ESN物块路径已目视检查。
- FINAL_ENV_BASELINE_PROTOCOL新增共同抓稳初态/共同前缀的接触诊断建议：保留任务监督器与共同lift历史，不向actor增加真值，不根据方法追赶球或改场景。当前学习策略存在无球接触且任务失败，不能用这类样本宣称碰撞恢复成功；本轮冻结测试不改。
- 原始展示条件单独注册REFERENCE_TELEMETRY_AMENDMENT01：frozen_reference04只增加球1kHz状态记录，用于明确1/40倍速真实近景，不插值、不改物理。测试仍frozen_evaluation03，训练快照不动；编译通过，实际1kHz/100Hz状态对应检查将随展示回合执行，尚不提前宣称通过。有限前台render_campaign随已完成展示导出视频，无cron/定时任务。
- Spark证据均在 /home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/：final_evaluation01、final_report01、FIRST_BALL_TEST_AUDIT.json、office_bridge/transfer_report01、REFERENCE_TELEMETRY_AMENDMENT01.json、frozen_reference04、parameter_rl/frozen_reference04、dispatch、media_render01。原五小时截止12:36:31 UTC；最终13模型矩阵、共同参数checkpoint和媒体仍进行中。
- main核对7cd5f4b；只更新baseline，不接入另一agent独立FLASK/WBC环境，不把开发结果写成统一dt=5e-5正式结论。

## 2026-10-02 — 综合环境zero完整失败证据与最终评估工具

- main再次核对7cd5f4b7ac0a3056df76ac62bc690ded0724b104；共享baseline的独立FLASK/WBC提交保留，不混入本轮固定office接入。原五小时截止12:36:31 UTC不变，无定时任务。
- 精确归档MJB下zero已完成55秒/550000子步：task/strict=false，停carry，抬升.128606m；RMSE27.5569mm、实际峰矩36.9007Nm、峰速.398633m/s、外穿透.158694mm。原始子步独立复算通过。球/人/棍均接触hand；凸边综合统计含物块，机器人手指接触33.7344秒才开始，不将两种统计混说。
- 新office report/summarize/render_clips/gallery保存完整和分窗诊断、1倍速55秒视频、.25倍球近景和原速棍近景及帧时序核验。发布 http://192.168.31.70:8765/primitive_baselines_20261002/office/ ，已目视核对球接触拼图。zero全扰动不是无扰动任务可行性对照；未声称综合任务成功或正式dt通过。
- dispatch_evaluation.py准备固定测试/原始展示/综合迁移命令和原窗口超时限制，拒绝覆盖旧结果；测试矩阵仍按预注册12条件/模型。最新三类参数RL共同checkpoint尚未锁定，VMC待仿真槽位，未提前报最终成绩。
- 新audit_parameters.py检查已实际执行的参数上下界、.04秒限速和局部储能账本；导纳50550更新/阻抗30750更新快照通过，约束真实触发（3/460次）；不是整体无源证明。训练及后续测试仍进行中。
- Spark证据：/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/office_bridge/{transfer01/zero,source_esn_review,transfer_report01}、parameter_rl/{admittance_applied_audit.json,impedance_applied_audit.json}、FINAL_EVALUATION_CATALOG.json、FINAL_REFERENCE_CATALOG.json、PHYSICAL_EXPOSURE_SNAPSHOT.json。两reward第一seed学到60300步，原失败恢复额外1525物理交互保留并计账；比较固定60000步checkpoint。

## 2026-10-02 — Replace artificial pillar with realistic workbench clutter

- Replaced the central orange pillar demonstration with a blue storage tote (active collision geometry) and a black tool tray on the tabletop. The scene now presents a workbench layout with shelves, bins, boxes, a cylinder object, target marker, and moving capsule rather than isolated vertical posts.
- The direct HOME-to-GOAL edge remains invalid because of the tote; FLASK finds a 2-segment route in 5.0 ms. Full 24.0 s / 12,000-step sensor WBC validation reports zero contacts, `0.00628 rad` final joint error, and `31.29 Nm` peak command torque.
- Re-rendered the realistic workbench video at 3x retime (209 frames, 8.36 s) and replaced the web page at `http://192.168.31.70:8765/flask_fr3_20261002/`. Local evidence: `outputs/flask_fr3_realistic_workspace_wbc.mp4` and `outputs/flask_fr3_realistic_workspace_wbc_mid.png`.

## 2026-10-02 — Add explicit central-pillar obstacle-avoidance demonstration

- Added a collision-active central orange pillar that blocks the direct HOME-to-GOAL FLASK edge. The deterministic planner now reports `direct_edge_available=false` and produces a 4-segment route in 37.1 ms. Added brighter key/head lighting and an `obstacle route` title so the render is easier to inspect.
- Moved the dynamic capsule farther outside the work area and reduced its slide amplitude after the first pillar test revealed a real link-5 contact. Full 24.0 s / 12,000-step sensor WBC validation now reports zero contacts, `0.00719 rad` final joint error, and `39.78 Nm` peak command torque.
- Rendered the raw 5.71 s, 1x route into 157 frames with visibly changing speed/acceleration traces. Published replacement page/video at `http://192.168.31.70:8765/flask_fr3_20261002/`; local evidence is `outputs/flask_fr3_obstacle_avoidance_wbc.mp4` and `outputs/flask_fr3_obstacle_avoidance_wbc_mid.png`.

## 2026-10-02 — 经典搜索锁定；综合环境原始MJB接入核验通过

- 原四视频经典搜索96/96完成：12候选×8训练条件，模型hash全部配对；独立区间聚合误差RMSE<2.4e-12m、峰矩0。导纳锁k150/zeta1.4，阻抗锁k600/zeta1.4；只用训练集。LOCK_AUDIT.json和原SELECTION/ROWS保留，尚非测试成绩。
- 两reward seed74001都完成60300步（按规则补完末回合），保存相同60000步checkpoint用于比较；seed74002继续。导纳/阻抗在线参数RL运行中，VMC等待空闲槽位，原训练截至11:40 UTC，五小时总窗口仍截至12:36:31 UTC。
- office_bridge/interface01在积分前拒绝服务器重编译MJB：458数组一致，其余包括网格BVH排列、路径和微小浮点差异；完整MODEL_MISMATCH_AUDIT01.json保留。修复为在相同源码初始化前加载原始归档MJB，仍严格检查 b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1，不放宽模型或物理gate。
- interface02七个80ms检查全部完成，名义/zero/固定导纳阻抗VMC/5维参数RL/直接RL均匹配原始MJB；zero状态、qvel、ctrl、canonical48逐元素一致。INTERFACE_AUDIT.json显式比较诊断NaN位置；原初版审计NaN字段保留，不假装物理量非有限。临时冻结一路本任务训练约24秒为检查让出槽位，finally中原状态恢复，INTERFACE_SLOT.json记录；未动四个历史暂停进程。
- 评估新增完整归一化统计hash（mean/var/count/累计回报），离线加载测试通过且能检测“计数未变但均值改变”。冻结评估03只增只读检查，不热改训练；综合接入原始MJB与执行源码patch/hash均记录。80ms不是接触或完整任务成功，完整综合迁移预算单独注册且尚未执行。
- 新增 summarize.py / report_training.py，按显式catalog汇总配对MJB、任务/strict/接触、提前终止和全时长指标，训练曲线不当测试成绩。docs/FINAL_ENV_BASELINE_PROTOCOL_20261002.md明确阻抗更换的是其力矩控制律，公共名义WBC参考/约束一致，避免“全部低层控制律不变”的误读。
- Spark产物：/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/ 下 campaign01/classical/LOCK_AUDIT.json、campaign02、parameter_rl/campaign01、office_bridge/interface02、office_bridge/FULL_NORMALIZER_AUDIT.json、office_bridge/TRANSFER_BUDGET.json、frozen_evaluation03、parameter_rl/frozen_evaluation03、office_bridge/frozen03、training_report01、reference_diagnostic_report。源码在 /home/arm1/SII_compliance_baseline/。
- main已核对7cd5f4b，baseline上一发布f5e5397；所有新结果是开发检查，最终评估/媒体仍进行中，另一agent未提交WBC修改不纳入本提交。

## 2026-10-02 — Fix visual target-cylinder interpenetration

- Corrected the complex-scene render after visual inspection showed the green target cylinder intersecting the end-effector. The target body was at `z=0.94 m` while the goal end-effector was at approximately `z=0.86 m`; it is now placed at `z=1.10 m`, leaving visible clearance while preserving the target marker.
- Re-ran the sensorized WBC validation: zero contacts, `0.00796 rad` final joint error, and `28.06 Nm` peak command torque. Re-rendered 144 frames at 8x and replaced the web-served MP4 with the corrected video.

## 2026-10-02 — Complex standalone FLASK FR3 scene and live traces

- Expanded the generated `flask_fr3_env_20261002` MuJoCo wrapper with a cluttered tabletop, four table legs, rear/upper/lower shelving, three colored objects, a visual target, a moving capsule obstacle, accelerometer, gyroscope, and touch sensing. The wrapper remains independent of existing SII benchmark scenes.
- Fixed the initial-state infeasibility caused by the original lower shelf and moving obstacle intersecting HOME. The rear/lower shelves and moving capsule now leave a valid corridor; the target marker is visual-only for this tracking run.
- Increased the FLASK search budget to 8,000 iterations and 40 samples per segment, then retimed execution by 3x. Arm1 validation: 0.73 ms planning, 1.95 s retimed trajectory, 6.0 s / 3,000 steps, 12 checked obstacles, zero contacts, 0.00796 rad final joint error, and 28.06 Nm peak command torque. JSON: `/home/arm1/vmc_mujoco_runtime/flask_fr3_env_20261002_complex_sensor_wbc.json`.
- Rendered a 3x validation trace and a longer 8x user-facing trace with the video-style right-side `Speed + limit` and `Acceleration + limit` panels. The 8x render has 144 frames, a 5.2 s retimed trajectory, and a 5.76 s encoded video. Server frames: `/home/arm1/vmc_mujoco_runtime/flask_fr3_env_20261002_complex_plot8.frames/`; local encoded video: `outputs/flask_fr3_realtime_plot_complex.mp4`; inspected middle frame: `outputs/flask_fr3_realtime_plot_complex_mid.png`.
- This is a development simulation result; it does not claim hardware safety, continuous swept-volume guarantees, or contact/grasp success.

## 2026-10-02 — 在线参数 RL、训练恢复与最终环境接入协议

- 用户确认每种导纳/阻抗/VMC控制器只有一组统一先验（旧三类BO物理参数几何均值），四特化场景共用。参数RL动作7/5/7维、25Hz、log空间限速/夹紧与局部储能预算；不是新BO最优或整体无源证明。新增 experiments/parameter_rl_20261002，原helper版本/hash和先验均保留。
- shield1800次更新及空tank限制检查通过；零参数动作与固定先验球回合、原生球遥测开关逐元素相同。5维阻抗梯度pilot完成750交互/1470更新；首次元数据构造失败发生在仿真前，保留不隐去。admittance seed75001主预算运行中。
- 原两reward直接RL在21525步被负科学计数法CLI解析共同中断。adapter02修正为--key=value；从20000步恢复agent/replay/RNG并跳过未完回合，明确不是物理状态精确恢复。旧campaign01失败和campaign02恢复分别保存，现均已继续超过40000步。经典96回合搜索仍运行。
- 新增确定性评估、子步三指标独立复算、球动量审计、真实时长MP4和页面。zero球原生动量残差峰值8.48e-17 Ns，只说明数值一致性。早期10k验证RL四场景任务均失败，保留且不冒充最终成绩。
- 用户提供main 7cd5f4b7ac0a3056df76ac62bc690ded0724b104后已fetch/read源码、交接和配置；已有v5完整ESN task/strict仍false，最大外穿透.653202mm。新增 docs/FINAL_ENV_BASELINE_PROTOCOL_20261002.md 和 office_baseline_bridge_20261002/evaluate.py，直接使用公共canonical48/动作链；目前只导入/编译检查，无新office仿真或接入等价性结论。不改另一agent的WBC工作。
- 本轮main最初f3437ad，后复核b75ef8e及上述7cd5f4b；远端baseline e564e09，共享checkout另有WBC提交01b50e1。实际计算主机Spark；源码在 /home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/experiments/，产物在 /home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/：parameter_rl/frozen_train02、gradient_smoke02_impedance、campaign02、RECOVERY02.json、CLI_REGRESSION02.json、evaluation01、MEDIA_CATALOG.json。页面 http://192.168.31.70:8765/primitive_baselines_20261002/。
- 五小时原窗口截至12:36:31 UTC，无定时任务、四路以内持续计算。正式保留集、三参数方法主训练、最终媒体/报告尚未完成；旧特化步长不一致，只是开发结果，不冒充正式dt=5e-5综合结论。

## 2026-10-02 — reference-style real-time speed/acceleration plot added

- 根据用户提供的视频，新增 `experiments/flask_fr3_env_20261002/render_realtime_plot.py`：左侧逐帧渲染独立 MuJoCo FR3，右侧在线绘制 `Speed + limit` 与 `Acceleration + limit` 两个面板；显示 fastest-joint speed、末端速度、fastest-joint acceleration、torque usage 和限值线，并用移动竖线标记当前时间。绘图使用 Pillow，不给服务器研究虚拟环境增加 Matplotlib 依赖。
- `FlaskTrajectory.retime(scale)` 新增时间缩放，保持几何路径和端点不变，同时按时间尺度缩放速度/加速度。参考视频复现命令使用 `--time-scale 3`，规划时长从约 2.08 s 变为 6.246 s；arm1 生成 170 帧/25 FPS，帧目录为 `/home/arm1/vmc_mujoco_runtime/flask_fr3_env_20261002_realtime_plot.frames/`，统计 JSON 为 `/home/arm1/vmc_mujoco_runtime/flask_fr3_env_20261002_realtime_plot.json`。由于服务器无 ffmpeg，脚本按设计回退为 PNG 帧；本地已将帧编码为 `outputs/flask_fr3_realtime_plot.mp4`（6.8 s）。
- 可视化运行结果：peak speed ratio 0.3170、peak acceleration ratio 0.1147、peak torque ratio 0.3318、final joint error 0.00916 rad。该视频是独立 FR3 仿真和在线绘图展示，不是硬件或实时性认证。
- 验证：重定时回归、可视化脚本 `py_compile`、EGL MuJoCo 渲染和 170 帧生成通过；未修改历史训练作业。

## 2026-10-02 — standalone sensorized FR3 FLASK/WBC environment completed

- 按用户要求新建独立环境 `code/mujoco_6d_vmc_benchmark/experiments/flask_fr3_env_20261002/`，不加载仓库已有 benchmark scene，也不继承原有“无传感器”限制。`run_sensor_wbc.py` 在运行时从 `/home/arm1/vmc_mujoco_runtime/mujoco_menagerie/franka_fr3_v2/fr3v2.xml` 生成全新 wrapper：7 个 torque motor、两个障碍物、末端 frame/force/torque 传感器、7 组 joint position/velocity 传感器。
- 新环境中实际运行 FLASK 规划 + sensorized computed-torque WBC：2 段无碰轨迹，规划 3.86 ms；4.0 s、2000 步 MuJoCo 仿真，峰值命令力矩 48.57 Nm、最大接触数 0、末端力/力矩传感器为 0（该场景没有人为接触）、最终关节误差 0.0644 rad。结果 JSON：`/home/arm1/vmc_mujoco_runtime/flask_fr3_env_20261002_sensor_wbc.json`。
- 运行命令和传感器/WBC 设计记录在 `code/mujoco_6d_vmc_benchmark/experiments/flask_fr3_env_20261002/README.md` 与 `docs/FLASK_FR3_20261002.md`。这只是独立 MuJoCo 开发结果，不是硬件、实时性或接触力响应认证。
- 验证：新 runner 和 planner `py_compile` 通过；独立环境 runner 实际完成；此前 planner 三项回归继续通过。未修改运行中的历史训练进程。

## 2026-10-02 — 注册四视频特化场景 baseline 五小时连续实验

- 用户新授权07:36:31–12:36:31UTC，当前线程连续推进，无定时任务。最终环境/WBC由另一agent负责。开工fetch main f3437ad、baseline699e317，不改main/旧作业。
- 四MP4 SHA匹配原teacher_eight_20260918，恢复ball-v7/push-core/corner-v6/legacy-table各自命令与原始轨迹。新experiments/primitive_baselines_20261002包含prepare/worker/train/classical/campaign；协议docs/PRIMITIVE_BASELINES_FIVE_HOUR_20261002.md。
- 每场景1000训练+12验证+12测试定义，非4096条已完成数据；按原采样范围、互斥split、场景均衡replay。SimbaV2两reward×2seed目标60k；导纳/阻抗各6候选×8训练条件，留出条件不选参。
- 实测球6.4s审计开关状态/动作全相同；三指标raw复算通过；RL750步1470更新接口通过但任务失败。固定阻抗球试跑成功、导纳失败；两厚桌角放置失败，不把旧抓取task字段当放置。
- 代码/数据/媒体留Spark /home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/，原场景source_scene_20260918及新frozen_adapter01均独立快照，原结果不改。训练主结果待真实运行，不宣称完成或收敛。

## 2026-10-02 — FLASK-style fixed-base FR3 motion-planning extension

- 参考论文 `2603.16059v4.pdf` 的机械臂差分平坦性特例：把 `q` 作为 flat output、`(q,qdot)` 作为 flat state、`qddot` 作为 pseudo-control，实现闭式 cubic Hermite/LQ 最小加速度 steering，并在其上加入确定性采样树。新增 `code/mujoco_6d_vmc_benchmark/scripts/flask_joint_planner.py`、`flask_wbc.py` 和 `run_flask_fr3_smoke.py`；新增聚焦回归 `tests/test_flask_joint_planner.py`。
- `FlaskJointPlanner` 对每条候选边按有限采样检查 FR3 关节位置、速度、加速度及可插拔碰撞回调；`MuJoCoFR3CollisionChecker` 提供固定基座 MuJoCo 场景适配；`FlaskTrajectoryWBC` 将轨迹转成既有 `WBCCommand`，不改变 scaledWBC/VMC 的安全和观测边界。
- 服务器开发 smoke 使用 baseline 检出 commit `699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0`、`/home/arm1/vmc_mujoco_runtime/simba_v2_venv/bin/python`，命令和配置记录于 `docs/FLASK_FR3_20261002.md`。合成 7-DOF keep-out 条件找到 2 段轨迹，规划耗时 2.79 ms、总时长 3.09 s、采样碰撞 0、终点误差 0、峰速度 2.5602 rad/s（限值 2.61）、峰加速度 8.8921 rad/s²（限值 10）。证据 JSON：`/home/arm1/vmc_mujoco_runtime/flask_fr3_20261002_smoke.json`。这是 development smoke，不是 MuJoCo 几何、真实 FR3 或硬件成功结论。
- 验证：三个 planner 回归函数由服务器研究虚拟环境直接执行并通过；三个新增 Python 模块 `py_compile` 通过；`git diff --check` 通过。服务器 `pytest` 未安装，因此没有冒称 pytest 结果。
- 本轮起始同步受服务器 GitHub HTTPS 凭据缺失影响，未能重新 fetch；可读的 `origin/main` 为 `ba84ed8a39ed743f603aa5d60e901bdf87090e1d`，baseline 工作区起点为 `699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0`，且起点存在远端已有未跟踪目录 `code/mujoco_6d_vmc_benchmark/experiments/primitive_baselines_20261002/`，本轮未触碰。
- 局限/后续：尚未在现有 FR3 MuJoCo 几何场景完成成对 scaledWBC 对照，也未做连续 swept-volume、真实动力学或硬件验证；部署前应显式提供 robot/obstacle geom 名称并提高/自适应碰撞采样密度。

## 2026-10-01 — 记录 RL 球碰撞视频疑点，用户下班暂停至明日

- 用户要求先记问题、明天再说；停止排查，不启动实验/自动跟进。新 docs/RL_BALL_REPLAY_AUDIT_20261001.md 保存已确认项、未决项和精确证据位置。
- campaign_01/seed61001/case0 的 task 撞 hand/link7，metric 无 >0.05N 球—机器人接触，ESN/zero 撞 link6；不同受撞条件不能直接作柔顺性响应对照。未证明 RL 存在额外非物理踢球。
- 原 MP4 每帧跨200ms、2倍速；高频球日志错误地只覆盖0–0.3s，漏掉2s发球。纠正此前仅凭接触短判断自然性；记录缺口未修复。
- 新只读 audit_ball_replays.py 成功提取四方法数据并校验原媒体/MJB manifest hash；JSON：/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/report/BALL_REPLAY_AUDIT_20261001.json。原数据不改，无新仿真。
- 原视频撞击窗口拼图/慢放：/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/assets/ball_replay_audit_20261001/；浏览页 ball_replay_audit_20261001.html。慢放为原速度1/4、仿真0.5倍速，不恢复缺帧，已目视检查。
- 开始检查main ba84ed8a39ed743f603aa5d60e901bdf87090e1d与baseline17d00a9；不动main、旧暂停作业与旧heartbeat。

## 2026-10-01 — 新线程接管并完成熵/有界奖励评测，行为修复仍失败

- 开工核验main ba84ed8与baseline8b48192，未操作main及旧heartbeat。接管既有1818576，未重复启动；旧四路SIGSTOP不变。
- 熵48/48、修复36/36完成，raw审计errors=[]。共同预算40k/20k分别报告，不混主100k；修复12/12完整55s物理有效但任务0，12条原始物块位置最大抬升/水平位移均0。尺度缺陷修正不等于可靠抓取baseline修好。
- 新docs/SIMBAV2_REPAIR_RESULTS_20261001.md/json；证据在 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/{entropy_diagnostic_02,reward_scale_repair_03}/report；修复media/bounded_metric_seed61001有完整MP4/GIF、输入输出hash。
- 网页 http://192.168.31.70:8765/simbav2_repair_20261001.html；未完成稳定抓取/搬运/放置、抓持后接触验证。两seed有限预算开发诊断，不能宣称收敛或SimbaV2本质弱于ESN。

## 2026-10-01 — 修复监督器已实际启动并冻结939f176

- reward_scale_repair_03实际启动2026-10-01T12:20:51UTC，supervisor PID1818576（1818575为启动shell）；PROTOCOL.json绑定源码939f176aebdf1ea26c361faaa9e8ead357cd0b6f与四文件overlay SHA。STATE当前waiting_for_predecessor，尚未启动仿真或声称新策略成功。
- 冻结路径 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/frozen_reward_repair_03/code/mujoco_6d_vmc_benchmark；launchlog /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/reward_scale_repair_03.launch.log。原entropy监督器完成48条后，自动无扰动检查→2seed有界metric训练→共同step≤30k、6策略36评测→专用report。
- 复查旧低熵训练排除warmup后仍大多approach，metric61002有1个grasp阶段记录但无完整task；不能把仅调熵称修复有效。后续从实际夹起/搬运证据验收，保留失败。已核GitHub baseline源码SHA一致。

## 2026-10-01 — 实现有界指标奖励修复并注册独立同step对照

- 基于main ba84ed8/baseline8e541d5，新增--error-transform bounded：每物理子步e²/(.12²+e²)训练积分及一致失败补偿界；旧quadratic默认保留。峰矩/时间/平滑/任务±20不改，原始三指标不裁剪。
- 21项奖励回归通过（含可加性、原始误差、极端提前失败/所有截断位置、terminal与非法输入）；新增bounded_reward_repair.py与report_reward_repair.py及docs/BOUNDED_REWARD_REPAIR_20261001.md。物理无扰动测试由监督器在真实训练前执行，尚不冒称已通过。
- 用户要求优先修复后，核cmd向旧entropy四worker发SIGUSR1，均rc0并保存checkpoint，实际约48.5–50k，共同40k进入原48条评测；不伪称完成原60k。supervisor1797525保持运行，不恢复其他暂停训练。
- 独立reward_scale_repair_03规划2seed新metric从零30k，与旧low_entropy同seed同step任务/指标共36条正式步长开发条件对照；LR计划100k，entropy-2，其余不变。新监督器等旧评测释放算力，先6.4s物理无扰动，再训练；13:12UTC安全停、13:41UTC真实交付。尚无新学习效果。
- 新冻结源预定 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/frozen_reward_repair_03，结果reward_scale_repair_03；源hash和实际PID由启动协议记录，不热改既有frozen_main_01。报告必须显式36矩阵与raw复算，保留失败，不以阶段冒充抓持。

## 2026-10-01 — 定位奖励尺度缺陷，明确当前RL不满足baseline交付要求

- fetch读取main=ba84ed8、baseline=140f71a。用户ESN视频取0/4/10/16/22s画面核看，可见抬升/搬运/释放撤离，task=True；未混作本轮固定checkpoint的同条件结果。
- 新audit_reward_scale.py扫描六路100k控制日志；排除warmup/跨界回合，metric30次提前失败补偿-178至-1810，normalizer分母364–366，office约5。原因是3m误差上界用于整个剩余时间；防逃避数学界不等于适合学习的尺度。
- 末5k动作分量RMS .38–.64，过滤后平移残差RMS .118–.269m/s，显著大于warmup；metric学习后226个结束回合均approach/align。未将随机训练动作当确定性测试速度，也未把相关性写成唯一因果。
- 新docs/RL_REWARD_SCALE_DIAGNOSIS_20261001.md及主报告明确不满足稳定抓取baseline要求、修复准入条件和未完成项。JSON在 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/report/REWARD_SCALE_AUDIT.json；原数据与冻结源不改。
- entropy_diagnostic_02 PID1797525–1797529正常，仍只检验熵，未修复reward；不重复启动或热改。剩余预算优先奖励尺度与确定性抓取验证，新训练须独立版本；尚无修复效果结论。

## 2026-10-01 — 低熵诊断运行中，补充48回合独立审计入口

- 读取main=ba84ed8、baseline=92f2f3a；entropy_diagnostic_02 supervisor1797525及四worker1797526–1797529正常，约19k步；无报错，无学习后完整任务成功。冻结训练源码与协议未改。
- 新report_entropy_diagnostic.py按8策略实例×6条件显式48回合检查，独立于主54矩阵；复用子步复算但不误用all54_present，核对checkpoint共同step/seed/path/hash、manifest、实际MJB、normalizer诊断和raw记录。分两个训练seed统计均值/SD，保留提前终止、物理无效和逐类事件分母。
- 无评测时的partial smoke通过：0/48、八组pending、没有伪造零指标或完成状态；尚未进行最终48条审计。源码/报告路径分别为 /home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/report_entropy_diagnostic.py 和 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/entropy_diagnostic_02/report/。训练→评测仍由已有supervisor自动接续，不重复启动。

## 2026-10-01 — 100k主矩阵54条完成并发布；注册独立低熵诊断

- 核对远端main=ba84ed8、baseline=107b21e；不合并同期main学生新权重。六路100k/190002更新和九组54条评测均rc0；52条55s，metric seed61002 case2/5仅0.44s提前2mm穿透终止。两RL组task/placement0；office物理18/18，metric14/18，ESN/混合/zero各6/6。
- 全54条实际子步复算通过，最大RMSE/峰矩/峰速差1.122e-11m/1.891e-6Nm/1.107e-8m/s；六条件跨方法MJB一致，记录的normalizer诊断冻结，审计无错。不能做混合时长统一排名。
- 新中文主报告 docs/SIMBAV2_BEHAVIOR_BASELINE_RESULTS_20261001.md 与publish_delivery.py；网页 http://192.168.31.70:8765/simbav2_behavior_20261001.html。三图PNG/PDF和五方法同case0状态重放媒体在campaign_01/report与media，web_demo/assets/simbav2_behavior_20261001/发布副本；每GIF276帧、三处帧不同、manifest hash核验，HTTP200及13媒体路径检查通过；UI打开队列未冒称已目视核验。
- 冻结全覆盖行为联合验收均0，但ESN人手局部6/6、棍2/6；zero人手也6/6。报告将任务/局部行为/曝光/unknown分开，不以未曝光概括柔顺失败。任务RL正式停approach，ESN到carry，混合多到load_transfer；不能称充分收敛或ESN全面优势。
- 剩余预算预注册独立entropy_diagnostic_02：仅entropy coefficient-.5→-2；两reward×2配对seed61001/2目标60k，LR总计划100k，其余不变，从头训练。现有主60k作为相同步数对照；共同最大周期step、八组×六已见参数条件评测。12:45UTC训练cutoff，13:41UTC交付截止；这是看过主结果后的诊断，不是独立确认或主结果替换。源码entropy_diagnostic.py，协议/状态/PID在 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/entropy_diagnostic_02/（启动后生成）。
- 主报告路径 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/report/FINAL_REPORT.md；全54审计RAW_METRICS_AUDIT.json。新脚本编译、diff检查通过；旧四路仍T暂停。新诊断效果尚未知，不暂停heartbeat直至诊断或截止真实交付。

## 2026-10-01 — 六路100k训练结束，36条RL正式步长评测完成并独立复算

- 本次fetch读取main=ba84ed8a39ed743f603aa5d60e901bdf87090e1d、baseline=4dad929；main已新增teacher学生/平滑/增益/seed开发实验，本批保持预注册ESN checkpoint与冻结源e71a512，不混用其不同模型结果。
- campaign_01六路训练均正常结束、各100000 transitions/190002更新；共同checkpoint_step_0100000，TRAINING_STATUS.json和COMMON_BUDGET.json留存。六个RL评测进程均rc0、36条输出已生成；ESN/hybrid/zero仍运行，尚非完整比较。
- 新增独立只读审计源码 code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/audit_raw_metrics.py，按物理dt加权重算RMSE、实际qfrc_actuator整体及逐关节峰矩、末端线速度峰值；检查时间连续性、样本数、完整时长并绑定raw/NPZ SHA。
- 不等dt/负力矩/线速度分量/提前时长/错误时间序列断言通过；已完成36条全部复算通过（不是36条任务或物理全通过）。审计仅读取完成的summary，跳过尚在写入的三组，需最终54条结束后重跑。
- 代码与全部产物仍在Spark。审计 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/report/RAW_METRICS_AUDIT.json；原始评测 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/evaluation/。未改训练、冻结源、环境或行为阈值；最终报告尚待完整矩阵与敏感性验收。

## 2026-10-01 — 主批次已实际启动，冻结e71a512

- pilot02 4×10k全部正常完成；修正后的两个warmup放置回合实际获得+20，但postwarmup仍无grasp。两个初始温度在预注册训练覆盖分数上均为0，按平局规则选.01，不能称已解决学习或已充分调优。
- 最新source绑定的telemetry_invariance_02通过，time/qpos/qvel/ctrl/hand/stage/object/observation/action逐元素最大差均0，物理MJB与三指标一致。
- bootstrap PID1736362、主supervisor启动PID1737384；首批1737387–1737390分别为两reward×seed61001/61002，seed61003两路排队（操作前核对cmd，PID可能过期）。已见每路600真实transitions，约12.1–12.3steps/s，尚在5k warmup。
- 冻结源 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/frozen_main_01/code/mujoco_6d_vmc_benchmark/，source commit e71a512e6fe01eb4e0456c3dfb7d6c6b88afcb54。主协议 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/PROTOCOL.json SHA256=733675507e1cf4aabaeaa17d3562af2c759204a245c2554cc46d5046f08b8773。
- 真实状态读取同研究根BOOTSTRAP_STATE.json与campaign_01/STATE.json，各run的progress.json。自动共享评测、敏感性报告已接续；本条是启动验收，不是最终性能结论。20分钟heartbeat已更新精确路径和预算。只改本日志，不改正在运行的冻结源码。

## 2026-10-01 — 八小时基线接续：修正终末奖励混淆并实现事件时序验收

- 开工fetch并读取main=3336864、baseline=c918548；main十小时teacher-bank已收尾且无新ESN。本轮不合并main，旧四路训练保持SIGSTOP。用户授权窗口约05:41–13:41 UTC（北京时间13:41–21:41），不是收敛保证。
- 撤销上轮未提交的stage+lift成功草案。旧三个ESN摘要缺连续NPZ，行为unknown；含杯combined_v4_development的carry早于碰柱，cup要求不得删除。修正源码、定义与小证据；历史原始rollout和旧奖励实验不覆盖。正确审计路径 /home/arm1/vmc_mujoco_runtime/SII_compliance_eval_2e37ddc/outputs/behavior_success_audit_20261001/。
- 新behavior_telemetry_20261001.py每物理子步累积、4ms保存，只离线使用接触真值；behavior_evaluate.py区分冲击停稳恢复、碰撞后原目标重入并继续运动、承载接触中切向净滑移及任务净进展。保留placement/physical/exposure/unknown；局部推进不等于完整清障。20项时序/振荡/参考跳变/竞争碰撞/掉落反例通过。
- exploration_pilot_01实际4×10k：std=.02 warmup访问抓取及放置，开始学习后新回合退回approach。独立审计发现真实放置且物理有效仍因contact_coverage不足获-20。新增task_physical目标按placement_complete AND task_success AND physical_valid，不强迫碰遍障碍；旧legacy_strict仍可用。7项目标断言及4项旧证据断言通过；真official agent精确episode-boundary resume回归通过。
- exploration_pilot_02已启动4路，两reward×initial temperature(.01/.0001)，gamma=.9995、entropy-.5、std=.02，terminal均task_physical。.01分支单独检验终末修复，.0001分支检验过强熵项；只用完全在warmup后的训练回合选择共同配置。主实验计划两reward×3seed×100k，共同checkpoint，新冻结6参数条件55秒/dt5e-5重评RL、ESN纯学生、75%VMC+25%ESN及零动作控制。计划不冒称已完成。
- 10秒logger开关对照的物理状态/动作/模型/三指标均完全相同；主批次前bootstrap再检查最新source的invariance_02。有限时长与earlyabort分开；report_campaign.py检查原始dt/MJB/normalizer/seed，均值SD以训练seed为单位，支持空间阈值敏感性和partial报告。
- 所有新代码 /home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/；全数据 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/；pilot_01/02与冻结源分开保留。BOOTSTRAP_STATE.json接续pilot→最新日志无扰动检查→campaign_01→共享评测→报告。正式报告预定campaign_01/report/REPORT.md；尚未生成的文件不是结果。
- 文档 docs/BASELINE_EIGHT_HOUR_PLAN_20261001.md、docs/BEHAVIOR_SUCCESS_DEFINITION_20260930.md（已更正）、docs/TRAINING_OBJECTIVE_AUDIT_20261001.md。源码仅baseline提交；权重、媒体、raw在Spark。heartbeat已恢复，每20分钟核验实际运行，预算到期交付实际证据后暂停。

## 2026-09-30 — 奖励主实验与40k补充诊断全部收尾，保留失败并交付审计报告

- 收尾前通过Git transport relay fetch并读取远端main 2581451cc9c471b19c67286457bea8d3b8a4b2b7及baseline e47da59日志；main的teacher-bank任务独立继续，未合并或操作其作业。Spark HTTPS无凭据，GitHub发布沿用Mac /tmp/SII_compliance_baseline仅作Git传输中继；代码、训练与大产物均在Spark。
- 主实验保持冻结：8×100k transitions、40候选验证、90最终评测。验证选模两主组各18/18完整55s且物理有效，task/placement/strict均0。metric相对office_task的RMSE降低59.24%、平均回合峰矩降低10.06%，但峰速增加60.58%，不称全面提升。fixed100k的7条提前物理终止单列，不能作为完整55s排名。
- 独立补充 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/progress_dense_diagnostic_04/ 已完成4×40k from-scratch与24最终回合，全部进程rc0、共同step40000、实际全55s/dt5e-5；两奖励各2seed×6case。office_task RMSE19.1963±8.7552cm/峰矩39.5328±0.5060Nm/峰速0.1537±0.0571m/s，物理11/12；metric68.9315±9.3659cm/51.1195±1.5965Nm/0.3341±0.1010m/s，物理12/12；两组task/placement/strict及所需接触覆盖均0/12。保留所有失败计算均值。
- 新连续势函数增加了数值上有效的进度信号，但117已结束训练回合仍无grasp，未解决探索。它是查看主开发结果后的40k诊断，学习率衰减预算也与100k主实验不同，不能当单因素严格消融/独立重复验证。结果不支持“充分收敛”或“已排除人为弱baseline”，更不能宣称SimbaV2本质弱于ESN。
- 独立审计补充全部24回合原始子步：RMSE/实际力矩/峰速复算最大差1.86e-11m/1.87e-6Nm/1.47e-8m/s；实际模型、manifest、checkpoint metadata hash与时长核对通过，记录的normalizer diagnostics不变。审计范围与边界见 diagnostic/report/DIAGNOSTIC_AUDIT.json及.md，源码/模型/raw仍在上述服务器目录。
- 更新完整报告 docs/SIMBAV2_REWARD_STUDY_20260930.md、docs/evidence/simba_reward_20260930/小证据和服务器网页 http://192.168.31.70:8765/simbav2_reward_20260930.html；publish_report.py支持补充结果独立表。plot_results.py将648条训练记录命名修正为ended_episodes（含提前结束），不改数值或冻结源。
- 主报告 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/report/FINAL_REPORT.md；网页资产 /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/assets/simbav2_reward_20260930/；全部实验接续状态见study根ACTIVE_EXPERIMENT.json。主与补充checkpoint均保留，旧四路1150890–1150893复查仍T暂停。
- 本轮计算与评测已结束，报告发布核验后暂停simbav2 heartbeat；不恢复旧作业竞争算力、不新增超出本轮时间预算的训练。尚未达成可宣称充分训练的强baseline，也没有同协议ESN新排名。

## 2026-09-30 — 100k奖励主实验完成、发现训练覆盖瓶颈并启动独立修正诊断

- 开工读取main e1d815c390d1221ee0bf80293e2b8179d2e1d3f8 与baseline日志；main的teacher-bank任务独立进行，未合并或修改其作业。
- 主实验 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/ 完成8×100k transitions、每条190002更新/40000000物理子步；40候选验证、90最终回合和全部进程均正常收尾。冻结frozen_v3/source32d2ea5不变。
- 主selected测试每组3seed×6条件、全55s/dt5e-5、物理有效全通过，但task/placement/strict皆0。office_task RMSE10.4868±4.8930cm/峰矩41.9397±12.3139Nm/峰速.0936±.0363m/s；metric4.2742±2.4923cm/37.7209±1.2178Nm/.1503±.0214m/s。不能说三指标全面更好或已充分收敛。
- fixed100k有7提前global_penetration>2mm终止（office6、metric1），只作混合长度失败诊断；仓库report.py补实际时长、55s完整率与abort，3项报告测试通过。独立审计86回合原始时长、21回合raw三指标复算通过（含7abort）；plot_results.py逐90回合核对实际MJB与模型/manifest/hash。小证据和已视觉核验图见docs/evidence/simba_reward_20260930/。
- 648个已结束训练episode（含提前物理终止）无一进入grasp：起点与初始waypoint重合，旧potential退化为ready/.2，随机残差打断停稳后Phi=0占主组约72.6–99.95%。nominal_zero同环境可完成1/6任务（strict0），不能归咎环境不可达。当前结果不能排除训练设计人为弱化baseline，报告明确承认这一限制。
- 剩余预算启动独立progress_dense_diagnostic_04：两reward×2seed各40k从零训练，shared连续pose/speed potential、UTD2；不改actor/任务gate/物理/filter。新快照 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/frozen_v4_progressdiag/，协议/patch/hash在其根；supervisor /home/arm1/vmc_mujoco_runtime/reward_study_20260930/PROGRESS_DIAGNOSTIC_PID_04.json；结果 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/progress_dense_diagnostic_04/。6项势函数测试+真实4step smoke通过。该补充在主实验诊断后注册，非独立确认，不混入100k主结果；正在运行，尚无效果结论。
- 仓库实现位于code/mujoco_6d_vmc_benchmark/experiments/simba_reward_20260930/；完整报告docs/SIMBAV2_REWARD_STUDY_20260930.md；服务器主报告和曲线 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/report/。公开展示入口 http://192.168.31.70:8765/simbav2_reward_20260930.html，媒体仍留Spark。
- heartbeat已更新接续补充诊断，约18:30前交付实际完成结果。旧四路训练保持SIGSTOP，不重启；现有主实验负结果、旧pilot均保留。

## 2026-09-30 — 主训练实际启动与自动验收安排

- 有效主实验为 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/；
  source commit 32d2ea5，source快照 frozen_v3，不热更新。
- supervisor PID1385951，首批worker1385964/1385965/1385966/1385967（仅为启动时记录，
  操作前必须再次核对PID命令）。首批实际进入随机warmup，约26–27 policy steps/s/worker；
  GPU更新与完整checkpoint roundtrip已单独验证，学习效果尚待主训练与评测。
- 主实验2奖励×3seed共6条；2条no-smooth消融；100k transitions目标/条、UTD2，
  8000s/run墙钟上限。若预算先到，选共同实际完成checkpoint，不伪称满100k或收敛。
- 每10k步存checkpoint，另外存跨间隔后首个episode-boundary checkpoint以支持精确恢复。
- 自动顺序：训练 -> validation候选选择 -> 55s/dt5e-5 test ->
  主组六条共同训练步数fixed_final评测；报告和曲线数据由report.py汇总。
- 已建立本会话20分钟heartbeat（ID simbav2），检查真实进程/日志/失败，正常进展安静；
  目标2026-09-30 18:30前提交真实结果与限制。新增报告仍保存Spark并push baseline。
- 接续入口 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/ACTIVE_EXPERIMENT.json。
  旧四路暂停、pilot01/02保留；不得误把这些旧进度当作本轮主实验进度。

## 2026-09-30 — 训练侧随机动作审计后冻结主实验

- campaign_02 的配对随机warmup物理轨迹、reward子步积分核对通过，但 smooth=.005
  在55s累计约32.94，超过误差1.47/峰矩3.10，不符合弱辅助约束。
  未读测试策略结果；将主实验smooth固定为.0002（无平滑消融为0），从头配对训练。
  pilot保留至 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_02/。
- 主实验 campaign_03：Office task vs metric 各3seed，目标100000 transitions/seed、UTD2，
  2seed无平滑消融，最大4并行；单run墙钟上限8000s，报告共同实际完成checkpoint预算。
- 冻结源码 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/frozen_v3/，
  输出 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/。
  validation-only选checkpoint；另外所有主组在共同训练步数重测，避免各自最优选择掩盖预算。
- 训练和验证dt=1e-4，最终全55s评测dt=5e-5；所有结果必须注明stage-waypoint参考。
- report.py按训练seed作统计单元，报告三指标及strict/task/physical/placement；
  不跨reward比较总回报，不把零成功归因算法本质，不声称固定预算已证明收敛。

## 2026-09-30 — 修复 campaign 子进程解释器路径

- 首次 campaign_01 在导入 numpy 前退出：对虚拟环境 Python 使用 resolve() 将软链接解析成
  /usr/bin/python3.12，丢失 venv。已改为保留 venv 绝对路径，算法与环境未运行，无学习结果。
- 失败日志完整保留在 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_01/。
- 重启使用独立 frozen_v2 快照与 campaign_02 输出，不覆盖失败记录。

## 2026-09-30 — GPU 官方算法验证完成，冻结配对训练方案

- 新隔离环境 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu：
  JAX 0.7.2/CUDA13, MuJoCo3.11；官方update约122.26次/秒，CPU大核7.37次/秒。
  GPU normalizer/optimizer checkpoint save-load动作差为0；仅补jax.tree_map API别名。
- 冻结两主奖励组各3种子41001/41002/41003，目标各60000 transitions、UTD2；
  另配对2种子metric无平滑项消融；最大4仿真并发。
- 新main几何检查：训练原计划variants3/4及val5/6初始柱座与物块穿模，全部排除；
  合法训练variants -4/-3/-2/-1。验证layouts0/1与6条最终评测manifest提前固定。
  测试中旧三布局属于已看过开发条件，另三条仅新物理参数draw；不称盲测新办公室泛化。
- 物理子步reward/trace、normalizers、replay与RNG以及episode-boundary恢复已验证。
  4步连续训练与2+2恢复的111个网络/优化器叶子完全一致。
- 默认validator与新增hooks零动作6.4秒重放，模型hash和所有轨迹/指标完全一致。
- 运行源将冻结到服务器 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/frozen/，
  训练输出 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_01/；
  此日志是执行计划，具体已启动/完成状态以CAMPAIGN_STATE.json与各progress.json为准。
- 评价只使用raw物理指标和严格任务门槛。运行归一化/discount后不能把reward恒等式直接当作目标指标等价性。
  当前尚无长训练效果或收敛结论。

# Baseline update log

## 2026-09-30 — 官方 SimbaV2 奖励对照：接口修复及开跑前审计

- 开工已读取 main 38caf3152282df4963435bb65c11c93a1e4fffa5 与 baseline 5934200 日志，
  整合当前 main 源码到 baseline；不修改 main，保留双方日志。
- 修复 Spark checkout 的 Git 历史：初始镜像根提交 d386341 保留在
  snapshot_initial_20260930，当前分支使用 GitHub 原始提交历史。
- 原论文与官方 commit 86899c277cdc697b2b02d827243de1ea93f20a1d 核查：
  没有通用 Office reward；官方采用环境 reward + 动态奖励/观测归一化。
  两主组为 Office task（成功/失败、势函数进度、时间成本）与 metric（在相同 task 上增加
  全子步平方误差积分、实际归一化力矩峰值平方增量、弱 requested action 平滑）。
  稀疏 task_only 仅为可选诊断，不能冒充论文原生 Office 奖励。
- 新源码：code/mujoco_6d_vmc_benchmark/experiments/simba_reward_20260930/。
  validator 新增可选 policy override/训练侧 metrics hooks；默认命令行行为与既有物理、任务 gate 保持兼容。
- 服务器开发与运行目录：/home/arm1/vmc_mujoco_runtime/reward_study_20260930/；
  Git 源码：/home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/。
  论文 PDF 与提取文本：上述运行目录 paper_sources/。
- 旧四路CPU训练经用户明确授权 SIGSTOP 暂停（未终止，内存保留），PID与checkpoint证据及恢复方法：
  /home/arm1/vmc_mujoco_runtime/reward_study_20260930/PAUSED_OLD_RUNS.json。
- 已验证 reward 15项单测；真实6.4s/64000子步误差积分与共同 evaluator RMSE复算相对差
  2.58e-10；峰值增量累计与最终峰值平方一致。
  证据：reward_interval_smoke_64s/VALIDATION.json。
  官方agent更新、网络/优化器/normalizer/RNG保存恢复与raw replay不被污染检查：
  official_agent_validation.json。train_smoke_01 为160步随机期管线检查，不是学习效果。
- 旧比较发现fixture偏移（RL内部再次+101*variant）、RL专用额外残差包络、外载荷误当执行力矩：
  新接口统一 canonical slowdown action7，移除旧RL额外包络，使用完整子步actual qfrc_actuator。
  不能将旧矩阵列作本次论文排名。
- 未完成：GPU隔离环境吞吐验证、配对多seed长训练、验证集checkpoint选择及最终共同评测。
  当前没有新学习效果结论；开发 dt=1e-4 与正式 dt=5e-5 明确区分。

# 更新日志

本文件记录每次对话交付的文件修改、验证和结果边界；最新记录在前。对应提交号由 Git 历史
查询：`git log --oneline -- UPDATE_LOG.md`。持续提交约定见 [AGENTS.md](AGENTS.md)。

## 2026-09-30 — 协作 skill：双分支开工检查、本地计算与服务器归档

- 新增 `skills/sii-research-sync/SKILL.md` 与 `agents/openai.yaml`，安装至
  `/home/airpig/.codex/skills/sii-research-sync/`，允许自动选择。开工先 fetch/读取远端
  main、baseline 的 `UPDATE_LOG.md`；收工重新读取 `AGENTS.md`，记录并发布本轮进展。
  同步更新根目录 AGENTS 与 README，让未自动加载 skill 的后续 agent 也有入口。
- 本轮远端检查（2026-09-30，Asia/Shanghai）：main=`f098678ad1532f1b87c7e2ac803faa301c4c65ca`；截至本轮查询，
  远端没有 baseline 分支，因此无 baseline 更新日志可读。没有擅自创建分支或合并代码。
- 新默认偏好：尽量本地计算，服务器共享持久文件。共享目录为
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance`，源码按 commit 隔离，
  实验按 branch/run-id 隔离；先同步并校验，再把服务器绝对路径写入更新文档。
  本地缓存和实际执行来源保留，不改历史 execution.json，不覆盖别的 agent 或 runtime。
- 本轮归档的是已发布研究源码，服务器代码位置：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f098678ad1532f1b87c7e2ac803faa301c4c65ca/code/mujoco_6d_vmc_benchmark/`。
  此路径对应本轮开始时的研究代码；本轮 skill/文档更改以 GitHub 新提交为准。
  未全量迁移历史 outputs、原始大轨迹或 checkpoint，不声称它们已在新共享目录。
- 验证：仓库版与安装版 skill 均通过 skill-creator 的 quick_validate，目录内容一致；
  使用现有 `.venv-canonical-rl` 中的 PyYAML 完成校验，未安装新依赖。文档差异检查通过。
  本轮没有修改算法、环境或启动仿真。
- 已完成：skill 编写安装、双分支状态检查、共享目录创建与研究源码归档。2026-09-30
  03:10:53 UTC 逐文件校验服务器快照：2,592 个文件 SHA256 全部一致，无缺失或额外文件。
  本轮没有运行中的新实验；历史大文件仍在原位置，后续按实际任务逐批归档。

## 2026-09-30 — 积累成果同步与每轮自动提交约定

### 文件更新

- 新增根目录 `AGENTS.md`，落实用户“每次对话结束前 commit、push main、记录更新”的授权。
  新增本日志，README 增加当前状态与入口。此次同步的起点为 `2e37ddc`。
- 纳入 9 月 23 日至今未提交的研究代码、配置、测试、报告与小型证据：统一物理子步指标、
  经典控制器预算实验、canonical48D/action7 及参数动作 RL 对照、ESN 记忆消融、
  VMC＋ESN 联合优化、延迟球撞、综合环境的版本化开发、纯 ESN 与 MLP 比较和动作重放审计。
  各历史实验的冻结配置、失败原因与结论以各自报告为准，不合并为一个“全部成功”的结论。
- 纳入独立 teacher 修正实现 `scripts/vmc_teacher_stable_readout_20260930.py`、
  `tools/teacher_repair_campaign_20260930.py`、`tools/teacher_repair_followup_20260930.py`、
  `tools/audit_teacher_repair_20260930.py`，以及 `docs/TEACHER_REPAIR_20260930.md` 和进度、周报。
  上述路径均相对 `code/mujoco_6d_vmc_benchmark/`。
- 新增 `tools/export_publication_evidence_20260930.py`，导出 teacher 的小型审计 JSON、运行配置、
  源码快照及哈希索引到 `docs/evidence/publication_20260930/`。原始大文件不进入普通 Git：
  `results/` 下 NPZ/MJB、证据目录编译模型，以及原本已忽略的 outputs、视频等仍在原处。
  本次清单覆盖 results 大文件、证据 MJB 和三轮 teacher 输出，不覆盖所有历史 outputs 或服务器。
  小型 docs/evidence NPZ 仍纳入版本管理。没有删除原始数据；需要完整重放时还须取得清单中的本地产物。

### 已有实验结果（与本次发布检查分开）

- teacher 两轮完成 12 条有效 55 s、dt=1e-4 开发回合；动作、内部状态及过滤链独立重放误差为 0，
  每条 550,000 个物理子步复算指标。此前误用 MuJoCo 3.14 的四条诊断保留，不混入有效结果；
  有效实验固定 MuJoCo 3.11，并核对综合模型 SHA256。
- 当前候选 `velocity025_stiff2`：corner-placement 的 task/strict 均通过；综合单柱 v4
  task=true、strict=false（缺少要求的柱接触）。综合 waypoint RMSE 37.406 mm，峰值实际力矩
  48.127 Nm，峰值末端速度 0.070574 m/s，外部穿透 0.144922 mm。
  相对同模型原版，放置阶段动作差分 RMS 0.306187→0.042031，降低约 86.3%。
- 尚未完成：特化场景全协议与跨条件验证、综合 strict、正式 dt=5e-5，以及稳定 teacher 数据上的
  新纯 ESN 蒸馏。此次发布没有新训练，没有改冻结环境或 gate。
- README 中 9/29 的 delayed-ball 正式通过结果和早期 cup/pillar 综合失败属于不同版本；
  不可与当前单柱 teacher 开发回合互相替代，也不能据此声称 ESN 已全面优于 baseline。

### 发布验证

发布内容扫描：814 个 Python 文件（包含归档源码副本）语法通过，1,216 个 JSON 可解析；
已检查的私钥、GitHub token、AWS key 和含密码 URL 模式无命中。相关既有测试
`test_esn_load_gated_20260929`、`test_esn_impact_response_20260929`、
`test_office_canonical_audit_20260927`、`test_physics_substep_metrics_20260923`
共 9 项通过。发布集合约 60 MB，最大单文件约 7.6 MB，无超大单文件。
产物索引含 1,642 项、17,382,062,868 字节（含保留在本地的原始数据和已复制的小型证据）。
本次不重复运行已经完成的长仿真实验。
发布整理同时移除了八份历史 Markdown 的行尾空白或多余末尾空行，不修改实验内容。
`git diff --cached --check` 通过；推送前 fetch 确认远端 main 与此次同步起点一致。


## Baseline branch workflow history

# Update Log

This file tracks code and experiment updates on the `baseline` branch. New entries go at the top. Large experiment artifacts remain on DGX Spark; each entry records their absolute server paths so another agent can inspect them without downloading them to a workstation.

## 2026-09-30 — Initialize baseline workflow

- Created the `baseline` branch from GitHub `main` at commit `2e37ddc95d94a4a01d531ae1bf2625a454826d2a` (`Add office-v5 ESN baseline handoff`).
- Inspected `main`: it did not contain an `UPDATE_LOG.md`; therefore this is the first log entry and there are no prior main-log entries to reconcile.
- Added the project workflow skill on the research Mac at `/Users/hwy/.codex/skills/sii-compliance-repo-workflow/`.
- Spark canonical branch checkout: `/home/arm1/SII_compliance_baseline`.
- Existing simulation/runtime and experiment artifact root: `/home/arm1/vmc_mujoco_runtime/`.
- This entry records workflow setup only; no experiment, model, or benchmark result was modified or claimed.
