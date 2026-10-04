# Teacher与经典控制器：完整八条件开发确认

## 名义规划＋WBC补充参考

10月4日01:53:05UTC，未调参的nominal_zero八条共同开发身份全部55s完成，独立源/物理子步/零动作回放/
公共过滤/执行器幅值与变化率/穿透sidecar核验通过。task/strict均0/8，全部停在carry；这八条另计，不改下方64确认分母。
平均阶段goal RMSE26.697mm、回合峰力矩均值37.532Nm、回合峰速度均值.36838m/s、最坏外穿透.18533mm。
低RMSE与较小穿透同时伴随任务停滞，不能当作更好柔顺性；也不据此推断只有ESN可完成，因为teacher已有成功。

本轮服务器根下`additional_development_v1/nominal_development/`：
SUMMARY SHA256 `6c2c6ec9784bcdbedcf0a742e607a46f874873279eef6ed2fce8142806062718`（Git同字节NOMINAL_DEVELOPMENT_SUMMARY.json），
execution SHA256 `f801ff972ba0299f9254cc587a76d4576ece5bcda21f34ea8277dcd5a89908c5`；
queue_0_analysis/INDEPENDENT_AUDIT.json SHA256 `3f95269cb8b63b51d2a034f013dfe1c912be955d871c7d112c98ba7bcf61ca87`，
其完整输出集合已逐hash复核。增强MLP/RNN开发已接续等待租约；此处仍是公开开发，不是最终24身份结果。

## Teacher与经典参数确认

2026-10-04 00:21:42UTC，96回合参数筛选后的8候选×8公开开发条件全部完成，64条均55s、50μs。
四队列各16条独立物理子步、动作过滤/执行器及接触审计通过。按预登记规则选择配置，不是最终保留条件结果。

| 候选 | task/8 | strict/8 | 平均阶段goal RMSE mm | 平均峰力矩 Nm | 平均峰速度 m/s | 最坏外穿透 mm |
|---|---:|---:|---:|---:|---:|---:|
| teacher09，选定 | 8 | 7 | 41.333 | 50.197 | .38235 | .31387 |
| teacher07 | 8 | 3 | 41.699 | 52.715 | .38235 | .58066 |
| admittance03，选定 | 0 | 0 | 31.472 | 39.903 | .36732 | .17476 |
| admittance09 | 0 | 0 | 29.749 | 39.669 | .36750 | .17611 |
| impedance02，选定 | 0 | 0 | 54.034 | 38.849 | .37316 | .16880 |
| impedance10 | 0 | 0 | 38.562 | 33.611 | .39002 | .17541 |
| vmc11，选定 | 0 | 0 | 31.778 | 38.130 | .36456 | .16198 |
| vmc08 | 0 | 0 | 32.100 | 38.034 | .37053 | .17481 |

原teacher相同8身份为8task/4strict。teacher09的7/8是开发改善；development006仍因
office_v5_pillar/fr3_link6_collision外穿透.313866810mm超过.2mm失败，不能写成完全安全。
其桌角穿透.0818402mm；任务本身成功。两阻抗共16条停lift，导纳/VMC共32条停carry，全部保留。
排序依次优先strict、task、完整回合、最坏穿透、RMSE、力矩、名称，因此选定经典配置不一定RMSE最低。
这是有限参数域/预算内搜索，不证明经典控制器的普遍上限，也不是ESN胜出证据。

teacher09只调整恢复参数：threshold_n=.7825162594，attack_s=.1875694089，release_s=1.1720038092，
offset_m=.0349179300，gain_per_s=3.1452852406，velocity_mps=.0860970956，activation_mode=progress，
progress_distance_m=.0141140060。环境、执行器、actor字段和原门槛不变。
该teacher的32训练＋8验证实际轨迹采集中；不能把开发确认轨迹作为新增训练数据。

服务器主机arm1@192.168.31.70，根目录
`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：

- `followup_v1/CONTROLLER_CHOICE.json` SHA256 `9a9c687847cac5d58ac24c4e43036ee0960dc0943e333ad756c1bf36c1ca833c`。
- `controller_confirmation_v1/SUMMARY.json` SHA256 `645efae204d694891618068aba1bfa6ba4fa66469bc60299b900d1cbed336fdf`。
- 规范SHA256 `96fb673c85df0967164fabdc874382bcbf1a8216b76fa25f5b1776e3802cea9b`；Git evidence含选择和汇总同字节副本。
- 四队列独立审计SHA256依次为`aec05f645520dab11a830b7cc65c945beff7e9aa0e74705dacbcad1722654e72`、
  `593cce6a8ae61ae9719d72f50bd24f3f1b220c6ed90183524e489a3cac21e21c`、
  `c4f9c51265217b78614a5abe66c1d045c59f4671b4d0df6de9a8931d5a6e6ee4`、
  `2549f4ea025b46fa26fc886b7ca2b0eb1ff5bbc097c03b4f42b9f4dc04634bbb`。

00:35UTC真实RL调导纳/调VMC各首条训练回合完整结束，仍为warm-up、梯度更新0；不得称收敛。
两个实际训练子服务峰内存约1.93/1.94GiB、OOM/max事件0；第三队列等待租约。
此前只读取父调度服务内存不足以代表learner资源，后续检查须读取实际queue cgroup。

已知train000通过最终执行入口55s重放，00:26:54UTC完成：观测、动作链、qpos/qvel、子步指标及接触相关数组逐值一致，
rollout SHA256与原始完全相同`785c075ced8fcc30ca470030b84166f1c0fb6607dfe3fa87b701a052bb791d67`。
`final_rehearsal_v1/REHEARSAL.json` SHA256 `2035c77283031b3c495599f07ede87b015ddeb1e5c07b6a8d99ecbee2ef9b755`；
独立审计SHA256 `d16eadb8c640c9af0e47cce478ca7838265bcfb8adb5e7a93f709af31f660fc8`。
这只验证一个已知teacher的入口，不是38模型全部入口或24最终条件验证；真正保留集未开封。
