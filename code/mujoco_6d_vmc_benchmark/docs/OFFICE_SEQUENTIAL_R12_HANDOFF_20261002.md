# 综合场景顺序扰动修复：sequential-r12-v1

2026-10-02 用户授权修正人手与推杆驱动重叠。开工远端 main 为
`5dc538b452e2b31cbd52172446f5beadb09f9b56`，baseline 为
`699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0`。未合并或修改 baseline 分支。

## 共同评估契约

新评估 ID：`office-combined-v4-sequential-r12-v1`。
配置：`configs/office_combined_v4_sequential_r12_20261002.json`。
相对前次 combined-v4，唯一物理行为改动是 `rod_start: 7 → 12 s`。

| 事件 | 推进 | 保持 | 撤回 |
|---|---|---|---|
| 人手 | 3–5 s | 5–8 s | 8–10 s |
| 推杆 | 12–13.5 s | 13.5–19.5 s | 19.5–21.5 s |

球仍在2秒发射；人手计划撤回完成后保留2秒恢复间隔。保持原55秒总时长、几何、
材料、驱动力、任务/gate、actor输入和执行器限制。2秒是固定的计划间隔，不是根据
接触真值触发的等待，不保证每个控制器都已恢复或已实际脱离。接触真值仅供事后审计。

所有已有ESN、MLP、RL权重和经典控制器参数可直接复用；本次不训练、不重新调参。
重新评估是必要的：旧结果保留在旧协议下，不能改标签、挪视频时间或混入新版本排名。
此变更不解决此前缺少柱子接触、ESN载荷转移停滞等独立问题，也不证明strict成功。

## baseline接入

使用配置中 `shared_cli` 的完整参数；神经策略另加
`--esn-model <原checkpoint> --esn-mode control --hybrid-vmc-blend 0`。
其他控制器保留其原适配器，只使用相同world时序。新验证器参数为：

```text
--interaction-schedule sequential-r12-v1 --person-start 3 --rod-start 12 --rod-hold 6
```

该标签会检查3/12/6，若旧脚本误带7秒则在初始化前报错，不静默覆盖。历史`legacy`
入口及旧配置不变；新评估必须显式选新配置，不能仍调用旧campaign的硬编码7秒。
独立baseline适配器若不支持该标签，应传入相同数值并在其执行记录保存完整scene ID、
配置hash和解析后schedule；不能只换标签而不换驱动起点。

冻结运行时仍为MuJoCo 3.11.0，开发dt=1e-4；本机解释器为
`/home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python`。
开发模型SHA256仍为`5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9`。
模型hash无法区分外部驱动时序，必须同时记录配置hash/schedule。
正式dt=5e-5仍需开发strict准入，不把本次短检查当作解锁。

## 已验证与未完成

- 已验证0–55秒每1毫秒的两路指令幅值无同时非零；解析时拒绝错误person/rod起点或rod保持时长。
- 顺序运行两个80毫秒物理检查（legacy和新配置），同一ESN checkpoint，
  所有保存的轨迹数组逐项相同、MJB hash相同、checkpoint hash未变。
  实际cgroup MemoryMax=3221225472、SwapMax=0、单线程；执行成功。
- 检查checkpoint SHA256：`9f4b5a8168142595873ff1c8fdcaa3b2186b7a1d1edab916d2bbd38fe5988023`。
- 未进行新55秒闭环评估；实际接触间隔、推杆有效暴露、三指标和strict结果均待评估。
  无训练或长时campaign运行；旧自动化保持暂停。

## 已核验共享证据

主机：`arm1@192.168.31.70`；目录：
`/home/arm1/sii_shared/SII_compliance/runs/main/office_sequential_r12_check_20261002_v1/`。

目录内 `configs/` 是共享配置，`scripts/`、`tools/` 是本次执行源码快照，
`outputs/office_sequential_r12_check_20261002_v1/execution.json` 包含命令、源/配置/权重hash和检查结果。
计算在本机执行，服务器为归档副本；原历史路径不改。
完整 `evidence.tar.gz` SHA256：
`b2d10aa5d0f2d271c3bd514ebad3ad8e46f92d364b50ea744a0aa04811b0008b`。
配置SHA256：`3140d8e9ad1aa8f28141e1d5a7f9b6dc4139e2020d0414371a1292d0ee9007af`。
