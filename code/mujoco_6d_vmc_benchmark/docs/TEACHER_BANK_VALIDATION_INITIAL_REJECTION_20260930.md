# v10 长推验证初态拒绝：独立静态核对

2026-09-30。本核对不启动 MuJoCo 环境、不积分、不修改源、场景或失败记录。
审查对象是已终态失败的 `active_long_validation_0001/vmc`，seed `20470931`，
锁定 VMC 候选 c05。它是场景初始几何无效，不能解释为控制器在运动中失败。

## 证据

- 原 `execution.json`：`failed`、returncode `1`，耗时约 0.7164 s。
- 实际 `run.log` 最终异常为 `office_task_v4_20260917.audit_initial` 拒绝初态交叉。
  杆与 link3、link4、link5 的重叠分别为 45.448110、60.098841、14.147345 mm；
  link5 有两条同深度接触记录，未去掉重复接触点。
- 冻结 evaluator 的 `audit_initial(m,d)` 位于原源第 92 行；`run` 自第 60 行开始，
  经 `adapted_run` AST 重编译后对应堆栈相对第 33 行。第一次 `env.step` 在原源第 400 行。
  adapter 替换球运动、曝光采样、调度及 teacher 调用，不移动初态审计。
- `make → create_environment → reset/IK` 构造路径使用 `mj_forward`；
  已读构造、reset 及初始化源码，没有前置积分。环境实际 `mj_step` 位于之后的
  `_physics_step`（第 1478 行），由后续 `step` 调用。
- `exposure.npz` 的 terminal_time 为 0，time/dt/contact_runs/person_physics 全空，
  内嵌 fixture 与 request 完全相同。空文件来自 runner 的 finally 保存，不能算一条轨迹。
- 没有 rollout NPZ/JSON/MJB、teacher 动作轨迹或阻抗 servo 轨迹。没有 MJB，因此不能
  对这个拒绝回合声称已完成编译模型 hash 配对，更不能填造 RMSE、力矩或速度。

这是冻结源码顺序、实际异常堆栈和空曝光的联合静态证据；本次没有独立运行时 step 计数器，
也没有做动态或零积分模型重建。它支持“初态审计在动态执行前拒绝”，不把源码检查夸大成重跑。

## Hash 绑定

| 内容 | SHA256 |
| --- | --- |
| teacher_bank.json | `1cafd43556f754df0595027c6aa1a358520038bbd5a3f742b9ef3b2a2f287945` |
| fixture physical config | `eb4f47b35b12922c4cc580aa33a4cebd1e6590d19e5a053576326371e1e3cc90` |
| execution.json | `318210c8f07fb5699728fda38a1ca1dbc5950da3705e2c4e33269326d97d026e` |
| request.json | `a00c4730b5dadd7cc3d37641cb0cdd097d0344a8a6514fe4ecc048549041c0c7` |
| command.json | `258a2b4ea78a758933e9dedc97a53477efacbc295a9c1988c51827d2003e8712` |
| run.log | `92793847edec6d929c3cfd3e98ab2843cd4674d60ad795704e9e1bdc83e01fe9` |
| exposure.npz | `8fead3629bfa3a322f1fb7aab0e264e8d4ab6b79b737b64630ef0095d6b2461b` |
| 冻结 evaluator | `9450355dad81ba983e09d3d8b601a4cb69b08ca8a7c2ac590819e702f4ffe7a0` |

源与证据当前本机检查路径：
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/teacher_bank_three_domains_20260930_v10/`。
服务器归档由主控核验，本文不声明尚未独立核验的远端副本。

## 最终验证报告的处理

工作副本 `teacher_bank_validation_audit_20260930.py` 已支持独立识别这个明确的初态异常：
同时验证锁定 request、实际 command、空曝光、源码审计位置与失败日志，记录
`invalid_initial_scene`，保留原计划分母并将物理指标置空。其他基础设施异常仍单独保留，
不会因 returncode 非零而自动改称场景无效。该分类不构成替换场景、回头调参或放松 gate 的授权。

初稿仅审查首个 VMC 拒绝。此后三种方法由主控按原预注册设置执行，
`teacher_bank_continuation_20260930_v2/validation_finished.json` 已记录全部 27 条有交代：
24 动态完成、3 初态拒绝，不能称为 27 条动态完成。

最终独立审计于 UTC 12:56:07–12:56:48 完成：
`outputs/teacher_bank_validation_independent_20260930/final_1255/review.json`，
SHA256 `1ce3797d9f22be7891592e92cb0335d491151adee9e5390a42c058f0c16ad25f`。
三种方法各自请求和执行身份已核对，均在相同初态以同一 60.098841 mm 最大交叉拒绝。
三份失败日志 hash 和空曝光 hash 相同；各自的 command/request/execution hash 在最终报告逐项记录。
这是初始几何一致的证据，仍不等价于不存在的 MJB hash 配对。

最终独立审计保留全部计划条目：24 条 `audited`、3 条 `invalid_initial_scene`，
0 条 `audit_failed`、0 条 `skipped`。有效的 8 个 fixture 三方法 MJB 均配对一致。
审计脚本的 16 项测试含 signal/timeout 遗留日志误分类保护和任意 rollout/动作链残留保护。
