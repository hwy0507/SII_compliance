# GPU持续守护v4验证（2026-10-28）

当前运行守护为`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/gpu_util_guard_20261028_v4`。本补充覆盖旧交接中v2/v3为当前版本的叙述，旧版进程均已停止、证据保留。原Direct33/三参数53继续，Goal active。

用户明确要求全部训练/评测结束后仍保持GPU占用；独立合成矩阵负载仅实现此运行偏好，不读写正式checkpoint、0科研更新、不算训练结果。当前进程在前台Codex退出和训练结束后继续运行，至STOP/系统关机；没有安装跨重启系统服务。

## 问题与改动

v2最后状态查询捕捉GPU3瞬时48%。v3将计算/休眠周期200ms改为20ms，最小duty60%改70%，固定60样本均值81.90/90.05/89.90/82.42%，最低48/68/69/46%，GPU0/3各4个低于50样本。不能隐去或重采当作v3通过。

v3 GPU0/3守护均绑CPU52，进程查询各约49%CPU，共用核饱和；另两worker约75%/73%CPU。v4改为`torch.cuda.Event(blocking=True)`事件同步，取代每批的自旋同步；四worker允许在审查CPU52–54间调度，正式CPU0–51分配未改。保留20ms周期与70%最小duty。v4实际CPU快照见证据CPU_SNAPSHOT，约8%–9%/worker，避免此前CPU争用。

## 固定窗口实际结果

v4等四worker真实心跳后，按预写PLAN采60次，实际73.046秒。保存原样本与GPU进程列表，均值/最小/低于50计数已独立复算。

| GPU | 均值 | 最低 | 低于50%的样本 |
|---|---:|---:|---:|
| 0 | 93.2167% | 85% | 0/60 |
| 1 | 88.9833% | 69% | 0/60 |
| 2 | 89.1667% | 70% | 0/60 |
| 3 | 90.2000% | 69% | 0/60 |

所有原正式learner身份全窗口存活且有进度。该窗口含合成负载，不是纯训练利用率；只证明观测窗口全部采样达标，不承诺永久每瞬时或平台永不关机。D/I/A/V观察吞吐8.05/12.72/12.91/12.94steps/s，保底仍有GPU计算开销，不宣称训练提速。

## 运行与保存

supervisor PID1629438，worker1629439/1629440/1629441/1629442；下次先核`LAUNCH.json`、`worker*.json`、真实/proc与`CONTROL.json`，勿重复运行旧版。停止该守护用`touch /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/gpu_util_guard_20261028_v4/STOP`，不停止正式训练。下次机器重启按交接重新检查后启动，不能拿旧PID当新进程。

源码/政策/固定样本/算术证据在`docs/evidence/RL_GPU_GUARD_V4_20261028`；共享SSD归档`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_GPU_GUARD_V4_20261028_040202/SMALL_EVIDENCE.tar.gz`，13544字节，SHA256 `d9754d0046c7283f74152ea4f4fcd8cba41755fa663f119fd988b3b157a23b98`，14份源/样本成员逐大小/hash核验。守护不改变研究协议；完整训练和恢复准备见[主交接](RL_RESUME33_PARAMETER53_20261028.md)与[早期loss补充](RL_EARLY33_PARAMETER53_20261028.md)。
