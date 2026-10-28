# 原67连续观察与导纳66终端误差诊断

2026-10-28 18:42 UTC，Goal active。主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD根 `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `B/env/bin/python`。前序完整启动、冻结协议及等待器见 [67早期交接](RL_PARAMETER67_EARLY_ANCHOR_20261028.md)。本轮没有重启科学训练、修改优化器/replay/物理/奖励/gate/LR/mask。Direct33仅原训练队列经验数值收敛、Task/Strict0/0，不启动34。未启动68。

## 原67保持与GPU

原三learner PID3260038/3260039/3260040，start ticks40649438/40649438/40649439。18:31:54–18:41:54共21次观测，steps2777890/2778739/2779727→2785405/2786354/2787455，均严格增加，所有原身份及归档、全loss、V终端、标签、68仅恢复、65–67窗口和五guard保持，无完整/失败。600秒观察自然完成，不是科学作业退出。

同期117条guard采样，四卡min67/68/70/69%，mean78.743590/88.931624/89.632479/89.401709%，低于50样本均0，最大间隔5.261581秒。包含合成保载，不是纯科学吞吐或每瞬时保证。用户明确要求科学全部完成后也持续保载，v5保持运行；当前为脱离终端的进程，不是跨重启服务。历史09:03–09:04全零事件仍见GPU_GUARD_V5报告，不掩盖历史空档。

证据 `B/runtime/parameter67_verified_wait_1830_20261028_v1`，REVIEW/GUARD_REVIEW完成。新增A67等待器单独核验在ADDITIONAL_IDENTITIES.json，没有改写原观察名单。

## 完整66导纳：只读事后诊断

`B/runs/admittance66_terminal_diagnosis_20261028_v1` 全2004终端前向与独立标量复算、全新增30终端/rollout/model/evaluator标签和实际optimizer时间线核验完成，真实diagnosis.png已检查。checkpoint SHA256 `2d2ac343a670f5737e5083769d35d7d6eea4801ded319d2d6d0a28a909678a6a`。网络/前向RNG保持，0优化/物理更新。

全2004 masked SSE8178.095842997081，其中旧1974为2086.939079359558、新30为6091.156763637523；全replay terminal128贡献分别.433884071232240/.110711943779110/.323172127453130。该贡献不是日志中的随机minibatch完整critic loss。

最大项 `active_short_train_0600`，replay index2752093/global step2752094/轮内33594。Task true、Strict false、physical false，穿透.230421531mm；真实terminal reward−28.443449312817，float32 replay−28.443449020386，episode reward−34.919579213858。masked SSE5517.734270163241，贡献.292782231338724，占全部终端SSE67.46966991%、新增30的90.58598365%。五head SSE738.124021/2280.545228/0/866.408460/1632.656562，mask0的head2排除。

该事件之前33593行critic均值1.184860889/max4.668558121，事件及以后7657行均值1.661067486/max29.879505157；图中密集有限尖峰与终端写入时间接近，末checkpoint误差集中在该终端。**时间对齐与最终误差集中不证明历史minibatch因果**；没有重建旧minibatch，也没有新增尖峰阈值/零终端误差停止门。其余新终端long0100/short0000/short0100 SSE430.594387/49.350091/28.963590均保留。

PLAN SHA ce5835d29d005870f7a2b8fc00e196562992807a15c877810765b5b065c404a7；REVIEW SHA2189fc3e2a90814813159e00d037b2a6e28ab3940361e7eaa589eeb2d64e7c13；values SHA2232c5cdfd606cf74f9f1c32838282b7a6069440613aa0d18f73f02adaa34f83；SAVED_REVIEW SHAaf234259dcdc1bfc41819976e0ff8beb1bed9411bbe0ff0511b1e325c8767a0f。

## 新67导纳固定全2004对照，等待完整结果

`B/runs/admittance67_terminal_anchor_followup_20261028_v1` 已保存完整66的2004×57特征、indices/rewards/masks/Q，独立SSE8178.095842997081。anchor66 SHA256 `70d64ebf71665626e1dcdee698ef03c0204934afba9245be0824930ec4b44be4`，ANCHOR_REVIEW/ANCHOR_SAVED_REVIEW通过。

从VMC67对照复制后仅换controller和图描述，逆变换/AST/SOURCE_REVIEW通过，VMC原件保持；全体2004→2034和公式不变。focus[2752093]是66事后选取、67完成前固定；全体结果仍须报告，不以focus替代收敛。waiter132612/start40839836，18:38:02启动，CPU53/7200秒，PLAN SHA256 `d11fb5e24957f37e1c9d84125f7ed4c5840cda872939cb86bac856bc9d0bb283`。18:41独立身份核验live。完整67前向、独立保存复核及实际图仍待。

接着收齐67完整loss/health图、全标签、VMC和A固定终端、原65–67窗口与68准确恢复检查，才作有限68决定；DECISION68须纳入新增A诊断/对照。条件性68–70已提前登记但未启用。原65–67端点、59–61/62–64失败和历史I56–58/V53–55通过均保持，不提前宣布整体收敛。

## 保存与远端同步

共享SSD小包 `B/repository/RL_PARAMETER67_WAIT_ADMITTANCE_20261028_184215/SMALL_EVIDENCE.tar.gz`，32成员/1003832字节，SHA256 `33bf8c25497f9dbfd6fca2b78f536490ccc15e52d5f3f5e3f5a1888cb2ad78f5`；逐字节、Python AST、tar成员核验通过。见[收据](RL_PARAMETER67_WAIT_ADMITTANCE_SAVE_20261028.json)与[清单](evidence/RL_PARAMETER67_WAIT_ADMITTANCE_20261028/MANIFEST.json)。这是观察/诊断与在途对照快照，不是完整67结果。大checkpoint/replay/raw仍共享SSD，非HDD或arm1全备份；HDD只原地重写≤1506字节既有LATEST入口。

实际fetch/read main从d8131828到b79ac855832d226a4893482f93c8efe07b1e7903，baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。已读非RL原机制失败/保存边角状态/阻尼六项在途的新报告并fast-forward完整保留，无本机冻结RL协议变化，无子agent。
