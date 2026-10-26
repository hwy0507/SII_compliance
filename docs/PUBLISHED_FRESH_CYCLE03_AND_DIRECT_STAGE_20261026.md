# Fresh第四轮科学复核、Direct六轮结束与固定策略检查

四路fresh cycle3（第四轮）完整科学复核已完成。成功率未随critic loss/Q误差改善，
不能宣称健康收敛。Direct已正常完成原登记六轮，原PID4055508退出，不应原样重启；
其余三路继续原阶段。持续Goal保持进行中，六轮结束不是充分训练结论或总步数上限。

## 同轮比较与优化健康

下表每种方法显式筛选cycle==3的30回合，全部完整55秒；避免混用恢复前后日志的历史范围。
末1000更新critic loss比较cycle1→3；终端MAE分别基于各checkpoint累计replay终端，非同一固定样本。

| 方法 | 第四轮末累计真实步数 | Task/Strict，各30 | 第四轮平均reward | critic loss，第二→第四轮 | 终端Q MAE，第二→第四轮 |
|---|---:|---:|---:|---|---|
| direct | 165000 | 0/0 | -33.25034 | 25.869 → 119.043 | 72.259 → 144.124 |
| impedance | 164484 | 18/17 | -2.37092 | 53.403 → 1173.444 | 81.622 → 247.539 |
| admittance | 165000 | 13/12 | -12.11673 | 79.790 → 830.029 | 115.690 → 332.196 |
| vmc | 165000 | 17/17 | -2.87507 | 49.420 → 720.415 | 104.931 → 431.386 |

四路被动条件均0/10。Impedance短期10/9、长期8/8；Admittance短期9/8、长期4/4；
VMC短期10/10、长期7/7。所有失败保留。Imp/Adm短期0600分别外穿透0.2325018/0.2074650mm，
超过原0.2mm门槛；各1375保存区间峰值复算一致，终端奖励仍−25、效率项0。

四路样本Q均值212.911/341.286/371.405/414.961，in-bag终端MAE119.985/228.612/303.268/410.321。
mask=0样本刻意未参与对应critic拟合，终端误差还可能受样本年龄和隐藏时钟影响；这些限制不等于
critic健康。当前不能将reward曲线平坦、有限loss或entropy接近目标当成收敛。
固定当前alpha的必要全局Q上界超限比例0/37.915/0/10.181%；不超限不等于值已校准，
上界也不是未来变化alpha的保证。没有据此作值裁剪或修改训练目标。

4份checkpoint原archive/snapshot/诊断副本hash、完整周期边界/replay长度/更新数、120个终端/
实际MJB/fixture/plan/dt、reward分量和网络未更新核验；780source hash通过，六面板图已查看。
复核0新physics/optimizer updates；区间安全核验不冒充原始物理子步重审。

## Direct六轮结束，不满足改善及优化健康要求

最终247500真实步、242501梯度更新，六个完整30条件周期。原恢复进程FINISHED的
cycles_completed=5指恢复后五轮，加已保留父cycle0，合计六轮；不是只训练五轮。
最终checkpoint/archive/独立snapshot SHA256：
`1f43dda8c7963f781837e6c0400cac9b0144a48018fc085886e0301c4cbfb3c8`。

第六轮30回合全55秒，Task/Strict0/0，平均reward−32.96507。
六轮Strict成功数依次0、0、2、0、0、0；第三轮两个成功没有稳定保留。
最后三轮reward均值范围0.47627，小于登记的0.65993容差，但相对最初两轮改善仅0.09068，
不满足至少2的登记改善条件，plateau candidate=false。

最终末1000critic loss390.695、样本Q均值367.934、终端MAE247.853，
in-bag/out-of-bag MAE211.452/389.499；终端诊断含六轮180终端×5critic。
原诊断图只显示恢复后的日志，与累计replay的六轮范围不同。图已查看，最后一轮30终端/
模型/时长/reward重新核验通过；0新物理/更新，未修改失败回合。

**决定：不以reward平稳为由宣称收敛，不自动原样延长这一已结束的Direct阶段。**
保留最终完整状态，结合下述固定策略证据和其余方法完整阶段结果，另行登记后续诊断/训练。
这不是取消或暂停持续Goal，也不是认定RL不适用；正式充分训练与最终比较仍未完成。

## 固定cycle3策略的12回合检查已实际启动

为了把变化中策略的训练成功与冻结策略能力分开，先记录PREPARATION，固定选择cycle3、
每类首个0000条件，未按成绩挑checkpoint或挑场景。原审计2472115完成四路cycle3后，
有限readiness进程3005171才核验四份不可变snapshot、全部源码/资产、12条既有名义参考，
写入精确hash注册并启动；readiness现已结束，session66123退出，不重复派发。

新run：`runs/fresh_cycle03_fixed_representatives_v1`。
注册SHA256：`8ce8f780392cf7ee137f7547db8e09af7b164277850b8f9e38cc00cc95ca8a26`。
冻结协调工具：`runtime/fresh_cycle03_fixed_representatives_v1`；复用原evaluation_audit_v6。
正式运行源码仍source_train16，**没有使用尚在验证的contact_math_candidate_v1**。

- 4接口×3条件，共12回合、最多1320万物理子步，确定性actor，0optimizer updates。
- 每方法使用其原GPU0/1/2/3，串行单回合；协调/推理/physics绑定预留CPU54。
- 同源canonical48转换及CHEQ自身mix context、动作接口、参数mapper、公共filter、原MJB/gate/dt保持。
- 名义参考复用已完成120回合矩阵中的同接口同条件12行，实际MJB、fixture、plan、物理审计证据hash
  与共同力矩阈值核验。无人接触记NA，失败留分母；不选择最终Tref/SPT，不代替ESN。
- 逐回合完整原子步审计、公共filter及力矩投影重放；中期代表条件结果不是完整30条件排名。

协调3148346、Direct evaluator3148347、首physics3152099已实际运行；启动核验实际GPU0、
冻结checkpoint fa9ebcd0…、165000步、actor49/raw48/common7、CPU54、无truth、模型/plan/dt一致。
当前未形成完整12行结果，不能预先判断固定策略成功。首回合身份以后以PROGRESS和子进程为准。

## 接触性能候选与剩余工作

原性能验证2273688继续，Direct被动/短期/长期三例均完整55秒/110万子步精确通过，合计330万子步。
新增THIRD_CASE_REVIEW.json复核第三例并引用前两例hash；三例Task/Strict均假，与参考一致。
随后Impedance被动例也完整55s/110万子步精确通过，FOURTH_CASE_REVIEW.json留证，合计4/12/440万子步。
旧首child3047099已正常结束；当前Imp短期child3298289继续。4/12不是全矩阵等价、整体加速或部署批准。
CPU53与固定策略CPU54分开，原三个训练learner继续；没有修改正在运行的reward/batch/UTD、
physics/MJB、gate、actor信息、公共filter或执行器限制。

GPU50%仍未解决；Direct阶段结束后GPU0承担上述有限推理，不能将其称为仍在正式训练。
需要完成当前完整周期/固定策略和性能验证，再决定可审计的下一阶段；不为占用率制造重复梯度更新。
指定ESN仍缺；最终训练集矩阵、SPT_empirical和实际人接触舒适审计尚未完成。

所有产物基址：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/`。
新证据在`runs/fresh_cycle03_scientific_review_v1/`、`runs/fresh_direct_final_cycle05_review_v1/`、
上述固定策略和contact_math验证目录；配套JSON引用hash与摘要。
远端main=a52dfba4486af8d263d5cd0a976c3102482ff249、baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d已核对。
本地提交和实际GitHub推送状态分开报告。
