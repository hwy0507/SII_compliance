# 参数46完整审查、正式47接续与Direct29冻结前瞻登记

2026-10-27，Goal active。上一轮48静态准备属于实质进展；本轮完整46/实际47恢复与启动、新保存结果证据和固定29评测选择继续推进目标，未整体健康收敛。沿用sii-research-sync，无子agent。

共享SSD B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；源码B/repository/SII_compliance。开工实际查询/fetch/read远端main74e2d160fac79d5591d3c9434391d75241de2715、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，环境/冻结物理和原算法未变，保留远端非RL工作。

## 完整46结果

原review与health、FINISHED均完成；独立保存算术 `parameter46_saved_review_20261027_v1` 核对所有episode/optimizer数值及hash，诊断图已目视检查。每方法30×55秒、无abort、新增41250、全部旧回放/history保留、新reward重建0误差，网络/优化器有限，health不改变网络。

|方法|累计步数|Task/Strict|平均reward|末次Q loss|首/末1000次Q loss均值|
|---|---:|---:|---:|---:|---:|
|impedance|1934930|18/17|-2.325234431|2.073591232|2.351719 → 2.649884|
|admittance|1934750|11/10|-15.465870987|4.113139629|1.398245 → 1.540451|
|vmc|1935750|17/16|-4.626437823|0.419053078|0.613869 → 1.174260|

I/A/V末1000loss均高于首1000，VMC后段波动和均值增高尤其明显；有限值不等于健康收敛。原43–45未稳定，已登记46–48窗口待完整48，不改5%/近零1/5000bootstrap或因结果选择窗口。

完整checkpoint：`B/runs/parameter_capacity_pool30_cycle46_archive_20261026_v1/<method>/cycle_00046.pt`，SHA逐方法见完整review/saved review。

## 45→46保存配对结果

`parameter45_46_saved_outcomes_20261027_v1`；核验原conditions/MJB/实际evaluator及physical-valid gate，0新物理、0优化，全部输入hash再次一致。

- I成功情况未变，均值+0.097686。
- A均值−3.376413，成功变化条件的算术贡献−3.373592；long0300/0900丢Task与Strict，short0600恢复Task但Strict仍失败，外部穿透.202446mm超过原.2mm门槛。Task12→11、Strict12→10。
- VMC Task仍17，Strict17→16；short0600外部穿透.169418→.215310mm，Strict真→假。该条件贡献−1.758115/总−1.859658。

这些是保存结果的算术分解和原gate核验，不是loss导致退化或学习/随机性的因果分解；没有修改gate或重跑物理。

## 正式47与48准备

原46三learner已退出，归档/审查原进程完成；47准确46全learner/optimizer/replay/RNG及next65536 check-only、独立科学PRELAUNCH通过。正式47 PID I3184892/A3184893/V3184894，GPU1/2/3、原CPU组13–25/26–38/39–51、每方法30sampler。保留原2m/历史entry23、terminal128、I-min/A-V-mean、actor-min、batch65536、UTD1和学习率，单有限周期。

实际startup3184896已通过，新增步数I/A/V 1000/1000/2000；全部旧行/history/optimizer超参精确保留、30MJB/30sampler/动作/时钟与新增reward0误差通过。archive3184897、fullreview3184898原进程继续。

48仅准备waiter3192792：`B/runs/parameter48_preparation_20261027_v1`，绑定实际47 PID/start_ticks和上一轮10文件SOURCE_MANIFEST，最多等7200秒，完整47review/health且父退出后进行最多1000秒check-only（内部三恢复共同900秒）；超时只清理自己的check-only组。无自动训练、无实际47checkpoint或4m部署。正式48需要实际恢复检查和独立PRELAUNCH，双marker/entry23保留与真实2m边界审查要求不变。

原参数46→47 observer2735669、保存审查2735670已结束。只读原review在父全部退出后移到释放CPU13，未改变在途训练/冻结任务。进程退出观察→Popen时间界：I228.284–230.286秒、A288.335–290.336秒、V288.336–290.338秒；不是整卡精确GPU idle或首更新延迟，不隐藏低利用。

## Direct29冻结前瞻选择（仅计划）

`B/runs/serl_take29_frozen_full30_20261027_v1/PLAN.json`，SHA `0bcdf58d087370c424801b7f1037131638ee20a56c1c0305f43101163397b7dd`。在原Direct28 learner1978250 live、29未启动/完整29不存在时固定现有27–29窗口终点29。全部30原训练条件/顺序、外部独立动作seed2026102626与已完成冻结16一致；固定30×55秒、最多41250动作/33000000子步，0优化/replay写入，CPU52推理/GPU0、CPU53/54两交错15条件分片。物理派发须等原冻结41三evaluator和rootreview全部结束且通过。

已核原30fixtures/固定16收据hash和当前28真实进程。**本轮只冻结评测选择/预算，尚无新evaluator源码验证、准备waiter、实际29恢复或物理评测。** 原26计划保留为中断后未执行，不改名或盲目复用旧26入口。后续专用入口必须验证原中断25历史、930隔离pending、连续完整26..29、全learner/optimizer/RNG/raw+derived replay/history；同动作外部RNG与前后状态不变检查。

16→29含容量1m→2m、partial25曝光/中断恢复和take等价gather边界；是单训练seed/单动作seed/训练条件上的描述性冻结比较，不是held-out泛化、无干预因果、最终ESN/SPT或收敛证明。

## 持续任务与交接

原Direct28 1978250、29准备2044155、Direct27–29统计336744、参数46–48统计1908379继续；冻结41原316550/316551/316552继续，不重复启动。当前身份和进度见LIVE_STATUS；旧PID行动前必须重验。下一优先完整28审查→实际29接续、47→48真实扩容恢复、冻结41完整90审查，以及恢复感知的29冻结入口准备。

小证据 `docs/evidence/RL_PARAMETER47_FROZEN29_20261027`，62文件逐大小/hash与Python AST核验。大checkpoint/raw/runtime仍共享SSD，HDD满仅更新已有LATEST指针；本轮小包/commit/push收据另记，不称HDD或arm1全备份。

发布前远端前进到9f48bbe（非RL传统36/72）。已读取并通过b704574安全合并，保留非RL AGENTS修订、全部远端日志/收据；初次push非fast-forward拒绝后正常合并重试，未force push，正式运行源未变。
