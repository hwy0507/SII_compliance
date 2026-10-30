# 完整81、冻结loss配对诊断与有限82续训

2026-10-30T07:12:24.975580+00:00。Goal active。完整81全审通过但未验证整体收敛；已基于完整原79–81结果登记并启动一个有限82，实际startup通过，当前steps `{'impedance': 3362035, 'admittance': 3364279, 'vmc': 3365495}`。没有自动83、没有Direct34。GPU保活在科学计算结束后仍持续运行。

计算主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。大checkpoint/replay/raw和诊断512×65536索引保存在共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，不是HDD或arm1完整备份。开工及发布前核对main `1c5154e18ff6fb45d7775f1a71d0cdf3bb15db47`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；最终发布以本轮PUBLICATION.json中的实测远端为准，保留另一主机非RL工作。

## 完整81

|方法|steps|reward均值|Task/Strict（30）|critic首→末1000|critic最大|
|---|---:|---:|---|---|---:|
|阻抗|3358948|−2.412238584|18/17|2.795769→2.032017|28.399206|
|导纳|3361250|−10.248240876|15/13|1.193168→1.809006|39.658913|
|VMC|3362250|−2.827427950|17/17|1.091015→0.955214|14.953114|

三路全30×55s、各41250新增、无安全中止；旧回放所有字段精确保留，新reward按冻结实现与interval日志重算误差0，网络/optimizer全部有限。不是独立重建全部物理子步。完整loss、health、180标签/90reward对、V/A两终端跟踪均已核验保存算术及实际图。

阻抗标签保持，actor23.732548→23.204547且critic仍反复尖峰；导纳末段critic升高及actor漂移，VMC actor呈先降后升。导纳short0900改善至Task/Strict成功；short0600 Task改善但physical退化、Strict仍失败；short0000因穿透约0.231342mm退化为Strict失败；long0900再次Task/Strict失败。VMC short0600本轮Strict通过，相关穿透0.179766mm；上轮失败保留，不称根因修复。原79阻抗long0000真实27s中止/global97.689mm继续保留。

健康度sampled Q超全局上界比例I0%、A0.01953125%、V0.09765625%，终端mask内MAE0.235272/0.330264/0.296023，mask外3.480634/2.422459/1.989522。mask外未参与对应critic训练，不设新零误差门槛。

完整81 checkpoint SHA：I `6dae48a98001e836fe37e59cb27c8de2c66839c91af1a5802d1234f23ed52106`；A `c0fa1f332b07ea867fc63b2ac5f38a9bbdb558330ba7b967fb9f4e8c44476f81`；V `5a434e45a4d8720833c6b68f4b11c2799f30081bf491c07a78eebf592a748356`。完整归档在 `runs/parameter_partial75_recovery_cycle81_archive_20261029_v1`。

## 原79–81与冻结loss诊断

原79–81 PLAN及seed2026102855/bootstrap5000/nearzero1/relative5%保持，完整结果和独立保存算术已审、统计图已实际查看。阻抗描述性5%通过（相邻4.8285%/0.9120%、首尾3.9606%）；导纳失败（相邻16.2642%/20.6832%），VMC失败（59.6307%/38.3836%）。三路均未触发nearzero。I通过包含不同条件收益相抵和79安全失败，不能等同策略或loss健康；saved reviewer没有独立重跑bootstrap区间，不夸大独立核验范围。保留79真实短回合，原74–76不完整不可判、原76–78 I近零不可判/A5%失败/V仅reward通过而loss未证。

冻结80 VMC使用实际原learner.train，在第一次q_optimizer.zero_grad前截获，512批×65536，seed2026103080，terminal128、原mask/target计算保持。原模型/optimizer/alpha/counter/replay摘要前后相同，无backward/更新/新物理，只有独立诊断RNG推进。loss均值0.923267、最大7.782040；9批抽到旧short0600终端3318758，均值7.576754，其余503批均值0.804218、最大1.744786。该条平均贡献这9批loss约89.9%。独立复核全部512索引/分母/终端贡献，与既有CPU Q计算最大差4.73e−6；非终端完整标量复核限保存的首批/最大批/首focus批。实际图已看。

在81结束前登记冻结81-on-fixed80配对：固定完整80回放、512索引和target pair，模型使用完整81；完整81/80前缀相同，整个81状态与80回放摘要保持。两轮actor、critic、target、alpha同时变化，不能解释为单独critic因果效应，也不额外声称原始动作噪声逐字相同。cycle80新增30终端与cycle81新增30明确区分。两轮诊断、独立saved复核和配对图均已完成；配对均值结果：

```json
{
  "native_loss": {
    "mean80": 0.9232666618190706,
    "mean81_fixed80": 1.0191300401929766,
    "paired_mean_change": 0.09586337837390602,
    "paired_min_change": -6.941478908061981,
    "paired_max_change": 4.140442967414856,
    "decrease_batches": 61,
    "increase_batches": 451
  },
  "terminal_contribution": {
    "mean80": 0.22641368297849906,
    "mean81_fixed80": 0.29476287109722726,
    "paired_mean_change": 0.06834918811872821,
    "paired_min_change": -6.959508235768393,
    "paired_max_change": 4.152733683701922,
    "decrease_batches": 83,
    "increase_batches": 429
  },
  "nonterminal_contribution": {
    "mean80": 0.6968529889600242,
    "mean81_fixed80": 0.7243671691264052,
    "paired_mean_change": 0.027514180166380953,
    "paired_min_change": -0.09051602733528263,
    "paired_max_change": 0.13726444583647335,
    "decrease_batches": 69,
    "increase_batches": 443
  },
  "new30_contribution": {
    "mean80": 0.13019153503203054,
    "mean81_fixed80": 0.004757262707156627,
    "paired_mean_change": -0.12543427232487392,
    "paired_min_change": -6.9062598774664465,
    "paired_max_change": 0.011986521996482164,
    "decrease_batches": 113,
    "increase_batches": 129
  },
  "focus_contribution": {
    "mean80": 0.11972381261776524,
    "mean81_fixed80": 0.0002602849180846058,
    "paired_mean_change": -0.11946352769968063,
    "paired_min_change": -6.91816191673428,
    "paired_max_change": 0.0,
    "decrease_batches": 9,
    "increase_batches": 0
  }
}
```

这些诊断解释冻结条件下的采样波动，不重建历史在线74.12尖峰，不制定“所有有限尖峰都异常”的新门槛，不宣称健康收敛或策略性能提高。两份268MB采样索引仅保留SSD，其路径/大小/SHA列于LARGE_DIAGNOSTIC_ASSETS.json；首/最大/focus张量、所有512标量记录和源码已纳入小证据包。

完整81新增终端逐episode映射与保存Q/mask标量复算在NEW81_TERMINAL_CASE_REVIEW.json。V/A新增30贡献分别 `0.0017941858912167527` / `0.4414690546461265`。A short0600/short0000/long0900分别占新增30贡献61.0398%/28.9170%/7.8880%。V旧2394 masked SSE5563.107010→6034.491314，A1538.721694→3046.945864，两分母都保留。这是末checkpoint分析，不能作历史minibatch归因。

## 有限82及下次接续

DECISION82绑定完整81/五实际图/精确恢复、原76–78及完整原79–81。三路full learner/replay/next65536恢复精确、原9拒绝检查与实际startup通过。科学协议不变：4m append-only、历史23/47容量marker、terminal128、batch65536、UTD1、LR/reward/masks/physics/filter/gates不改，每路一个30条件×最多55s周期。所有partial75历史保留。

运行 `runs/parameter_partial75_recovery_cycle82_20261029_v1`，完整archive/replay/reward/health/loss/标签/两终端后续已部署。V/A终端锚点完整81共2424，未来完整82预计2454。新82–84窗口在82启动前登记，相同数学/判据，等待器仅审计且顺序执行独立saved reviewer，不自动训练83/84；原窗口结论保留，不作事后挑窗口。下次先核原PID/start/实际进度、guard样本年龄和全部FAILURE/FINISHED，再完成82审计并依据结果决定有限下一阶段。

Direct33数值阶段已接受、冻结30条件Task/Strict0/0；原28最终内存不变证明缺失继续披露，不启动34。用户指定ESN尚缺，不拿另一主机非RL模型或历史ESN替代；最终冻结比较仍未完成，Goal保持active。

## 保存与GPU

本轮GPU连续保存408样本，最低[59, 67, 68, 67]%，低于50次数[0, 0, 0, 0]，末值[80, 95, 70, 96]%。含合成保载，不是科学吞吐；历史v6低谷/v7预热0保留。guard `/tmp/sii_gpu_util_guard_20261030_v7` 原PID/start核验，完成科学工作后继续运行，但不是重启自启服务。

SSD小证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY81_COMPLETE82_FROZEN_LOSS_20261030/SMALL_EVIDENCE.tar.gz`，387成员/15855326字节，SHA256 `6815bb646d378fcd163fcecf9363068f2fb73f15785a8a1e663e244299e0e210`，全部成员字节/hash/源码AST核验。Git证据含ignored nested runs显式force-add；发布还须核index与commit blob、成功push及实测ls-remote。既有HDD LATEST为254字节原位更新，非完整HDD备份。
