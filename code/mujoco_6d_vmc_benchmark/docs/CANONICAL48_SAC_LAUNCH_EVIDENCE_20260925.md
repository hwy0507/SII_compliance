# canonical48/direct7 SAC 两分支启动证据

本阶段是固定预算 standard SAC 与 uniform demo-prefill SAC baseline；不是论文算法复现，也不代表任务成功。两支 seed 都是 20260923，各采集 8192 条在线 transition，后者另加入固定 train-only r2 demo 600 条、不做离线预训练。原 PPO 多 seed 的 25 项部署队列保持独立。

DGX stage：`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/canonical48_sac_20260925_r1`。本机归档位于 benchmark 的同名 `outputs/` 目录。201 个 readonly source 文件基于原始归档构建，原 163 个执行文件逐字节保留。预检实际 simulator steps=0、gradient updates=0，核对 DGX 与本机已审阅 SB3 实现的文件 hash，验证 proof、demo、fixture、asset 和初始 RNG 一致性。

| 证据 | SHA-256 |
| --- | --- |
| BUILD.json | `e13c350033469820f8125ca0f5bc2706c8f763e7fda816dde71e33df75153a6b` |
| PLAN.json | `2a47e065b2fd8055ec67624a56e0942347e3d7a428f065d131803bdc284f4734` |
| PREFLIGHT.json | `0b26d09fed4e92d02f5498ecf2836a49100919b2b805529edd5cea2fd55cf297` |
| 独立 supervisor | `5de6a8284d279c1a725729289ea8793161277f933d2c0ab040c41a71292e4409` |
| 独立 startup audit helper | `6eea0e5eaba57f76c3b495e4e1b1f2d91ffbaffbe983dc928bd1be57cc2e709e` |
| startup_pair_audit.json | `137ccefa7bfecbd3b5032cb05fa44dae55af604e6b611992e9bc8de8ed15f97c` |

两个独立 helper 均在 stage 根目录，未加入或修改训练 frozen source。对应本机工具是 `tools/supervise_sac_two_branch_20260925.py`、`tools/audit_sac_startup_pair_20260925.py`。上述 startup report 与 helper hash 由本表绑定，未修改已保存报告。

启动前检查只存在 2 个原部署物理 worker；root 审阅具体命令和 supervisor 后明确授权启动。Supervisor 开始 Unix 时间 1790275209.278331，PID 569894，当时系统可用内存 122271277056 字节。online_only timeout/Python PID 分别为 569895/569896；demo_prefill 为 569897/569898。两支分别 CPU5/6、单环境、单计算线程、CUDA；实际 2 SAC + 2 deployment 合计 4 个物理 worker。完整命令、环境、资源和开始时间保存在 stage `supervisor/status.json`。

每支固定 timeout 7200 秒、15 秒 TERM→KILL；记录真实 exit code，区分 timeout124、137/SIGKILL 但不武断认定 OOM。某支执行/启动失败时继续保留已启动 peer，不自动重试；supervisor 自身异常仅有界清理自己创建的进程组。7 项 supervisor 生命周期测试通过，包括真实 child exit124，以及第一支 spawn 失败后第二支仍成功完成。

启动验收实际通过：两支 `sac_initial.zip` 中 policy/alpha 的所有 tensor fingerprint 均与预检、彼此完全相等；两份初始 RMS 完全一致且与预检相同。两 ZIP 整体 hash 因路径/元数据不同而不同，不以 ZIP 文件相等代替 tensor 比对。两份 `vecnormalize_initial.pkl` 的 SHA 都是 `d8c70077fe197cf02c7e9b8083101493f2eb71a7ddf4e617e16be44f42ce5c5b`。

前 100 条 warmup 和第 101 条首次更新前 transition 的 raw observation、raw next observation、valid mask、buffer/environment action、reward、done、episode step 与全部 actual post-add replay 数组逐字段完全相等。demo 分支 slot 固定多 600，episode 绝对路径不同，这两项不要求相等。首 entropy/critic/actor optimizer posthook 均为 online_step=101、completed_steps=1。时序依据是已审阅的 SB3 collect→store→train 顺序。预检验证 prefill 不消耗 NumPy/Torch/CUDA RNG；实际 run 未插入额外 RNG 抽样或追踪。第 101 次更新之后的分歧是合法结果。

本文件仅记录启动通过；最终 8192/8092 预算、4 项评估、全量回放/奖励审计、归档 checksum 和任务指标仍需由最终证据确认。周期 2048/4096/6144/8192 checkpoint 仅用于诊断，不用于选优或重训。

## 后续完成与回放记录

Supervisor 于 Unix 1790276044.6127627 完成，持续835.334秒；两支真实returncode均0、均无FAILED且COMPLETE存在。`supervisor/COMPLETE.json` SHA为 `2556d0d2918aa342e9758e9774c8191cfc0269dd0954b282ffb11cf7077341bd`。两支2048/4096/6144/8192共8个checkpoint的实际zip均核seed20260923、updates=step−100与3个optimizer计数，不只依据文件名。

| 分支 | 固定最终SAC SHA-256 | 自身最终normalizer SHA-256 |
| --- | --- | --- |
| online_only | `732b70b491f9fc18592387abd0f90dda2124f2500f5bab9798d72e24ff4012b6` | `069db8b74dcd94171a73f17d3de9253db25bcae6ccce5be06a47debad0d352c2` |
| demo_prefill | `390e33db9db3eaa434825ec5131f9d2fd97bfc2a049bdc1a1610cc29893e6392` | `d9a74906ac5d19a1229753d8bf1ec637da47180b2536431a2e4979f67d2f0a48` |

两支train/validation实际SAC eval均为600帧，task和development gate均失败；没有用结果改预算或换checkpoint。online最终stage均0，demo均1，不能跨stage将endpoint误差直接排序为任务性能。

新独立SAC adapter通过原`PairedExecutionPolicy` direct7层；两branch的train/validation各600帧同DGX CUDA离线回放全部请求/执行动作、reset重放与RMS冻结精确相等，均未使用fallback。这是原轨迹输入回放，不是额外物理部署。两branch train/validation zero对原seed23 direct7 zero的完整raw、MJB及transition逐值精确。

| 只读证据（`docs/evidence/canonical48_sac_20260925/`） | SHA-256 |
| --- | --- |
| online_only_deployment_replay.json | `8d0a62e5fced028e6832c2c630a07aca29e4e98bdabda109bc5d6cd3b9233d12` |
| demo_prefill_deployment_replay.json | `3a758be6ff2643049c576991786ee4b412043342da6241664f58070993fc34eb` |
| online_only_zero.json | `5176c3e69dcf8e8a3a3f9d48b25e9dc7c6973c011464e8b200035159179a3340` |
| demo_prefill_zero.json | `e0d8d5832031245f6599b29d51fe50a31ae4ba9b19dc4d425e11d74d29ae08c7` |

回放独立readonly快照 `outputs/canonical48_sac_replay_source_20260925_r1` 保留训练201文件、显式加7文件，共208；BUILD SHA `be148d798ca2f335c5233d886485c5410731aecfb83e686c9e6bbe4d9c2169f1`。该快照内的早期13job协议草案误写nominal zero6 parity，未用于新增物理；root后来明确覆盖为direct7 zero7/9400 parity，最终部署必须采用workspace新版 `CANONICAL48_SAC_DEPLOYMENT_PROTOCOL_20260925.md`，不能使用旧草案。adapter/replay本身不含该zero6草案路径，两份回放报告的20项输入hash已由另一agent独立复核。

这些完成记录不替代两branch完整8192步replay/sample/奖励/optimizer独立审计或整根归档checksum；相应证据单独保存。
