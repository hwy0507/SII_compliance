# 固定 actor 的 critic 时钟诊断与完整回放后续验证

两方法、三配对采样 seed 的有限诊断已完成，12万次辅助critic更新、0新增物理步、0 actor更新。
时间输入相对无时钟对照改善部分误差，但没有修复后一轮终端误差增长；不用于正式控制器，Goal未完成。

## 完成的对照及科学边界

冻结fresh cycle1的Direct/VMC checkpoint；只用cycle0回放更新，cycle1仅诊断。
**cycle1已被原checkpoint训练见过，只是没有参与本次辅助更新，不能称未见条件验证。**
两臂采用相同父online/target critic、同维度额外输入、零初始化新列、fresh Adam、原Bernoulli mask，
相同replay/random-two采样流，固定actor/alpha，gamma=.9995、tau=.005、batch256、lr3e-4。
每臂每seed1万更新，三seed来自相同父权重，不是三次独立在线训练。
控制臂额外输入为0，处理臂为已知剩余时间；actor仍49维=canonical48+自身mixing context。
不编码未来中止、接触真值或任务标签。保留原done零bootstrap；CHEQ回放context固定，
因此也不是完整混合控制策略的on-policy价值估计。

以下是三seed均值，箭头为无时钟→已知时钟：

| 方法 | 拟合cycle0的in-bag终端MAE | 本次未更新cycle1的全终端MAE |
|---|---:|---:|
| direct | 17.682 → 15.734 | 130.799 → 123.232 |
| vmc | 40.882 → 33.003 | 150.348 → 138.577 |

后一轮误差分别相对控制下降约5.8%/7.8%，但两臂都高于诊断起点；图中Direct仍上升，
VMC时钟臂约138附近趋平且误差较大。固定actor/alpha的条件下也出现这个现象，
说明不能只归咎于同时更新actor；不过这并不识别正式训练全部误差增长的原因。
不把终端MAE必须为0当作收敛门槛，也不因全局Q上界未超限就宣称校准正确。
当前证据不足以推广时间critic或原样延长已结束Direct阶段。

三个守卫测试通过：额外列保持初始函数且可学习、早停不编码未来、终端无bootstrap/熵。
完整核对12臂/120个诊断点、配对初始函数与采样hash、actor/replay/原checkpoint不变；图已目视检查。
首次v1因诊断依赖缺失在加载checkpoint/更新前失败，保留收据；v2补齐并冻结依赖后完成。
两个进程3666074/3666075和只读review session73879均已退出，不重启。

## 用户再次要求避免空闲后启动的完整回放诊断

依据前述“拟合旧回合但后一轮误差增长”，后续检验全部历史数据覆盖是否改善critic拟合。
四方法全部使用各自冻结cycle1全replay（约8.2万条），时间/零输入两臂、三采样seed，
每臂5万更新，合计120万辅助critic更新的有限预算。每条transition期望被抽约155次，
原mask不变；这是新的全数据拟合与较长窗口诊断，不是重跑上一项cycle0-only实验。
本次全部诊断数据均被拟合，字段明确使用fit_all_replay/replayed_cycle1，**没有heldout分数**。
不保存/推广辅助权重，不自动延长预算，不改正式学习器、physics/MJB、gate、actor输入、
公共filter、执行器限制或dt。原三路正式参数RL继续。

八进程，每卡两个，使用已释放CPU0–7，三个seed按2+1分片避免重复；每项已核验真实更新，
首份STARTUP_REVIEW八项均已7000更新。登记和PID以配套JSON/原LAUNCH为准。
完整结果未完成，尚不可给出成功或收敛结论。

## 其他在途证据

contact math候选新增Impedance短期和长期两例完整55s/110万子步精确复核通过，
两者Task/Strict均真且与参考完全一致；现在6/12已独立复核，原协调已完成第7例并继续，
候选未部署、不称全矩阵验证或整体加速。
固定fresh cycle3 Direct的三个代表条件已完成，原协调已做3项审计，Task/Strict均假；
参数方法评估继续。不是最终30条件矩阵，更不是ESN比较。

## 服务器产物

基址 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/`：

- `runs/fresh_critic_clock_probe_v1/`：首次导入失败，0更新。
- `runs/fresh_critic_clock_probe_v2/`：完成结果、REVIEW、六面板图及60秒GPU记录；冻结工具同名runtime。
- `runs/fresh_full_replay_critic_clock_v1/`：8份登记、LAUNCH、STARTUP_REVIEW和在途结果；冻结工具同名runtime。
- `runs/contact_math_validation_v1/FIFTH_CASE_REVIEW.json` / `SIXTH_CASE_REVIEW.json`。

前项GPU0的60秒均值89.3%，其他正式卡5.97/3.32/5.48%，不能当四卡正式训练达标。
新完整回放诊断与正式任务共同运行的60秒实测：四卡均值89.37/91.87/94.62/96.12%，最低88/88/89/89%；这是混合工作负载，非纯在线训练吞吐。八原诊断任务继续，勿重复启动。
源码/小型报告提交Git；checkpoint、raw replay、运行日志与环境留服务器，不提交Git。
远端main/baseline已重新fetch并核对，发布状态与本地提交分别记录。
充分收敛、最终冻结策略矩阵、SPT_empirical和指定ESN比较仍未完成。
