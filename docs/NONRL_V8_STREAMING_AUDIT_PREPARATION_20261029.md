# 低内存独立审计准备：已验证，新增派发未执行

新分块审计代码完成验证；第五条件审计尚未启动。原108与现有完整后处理继续，
03:08:42 UTC完成48/108，原主PID1172675与后处理1201537均loaded/active。
上一轮是verified wait，本轮解决审计一次加载大数组的问题，属于准备进展；主矩阵仍未修复。

## 内存与验证范围

原审计一次加载完整dt/力矩/误差/twist/接触/穿透数组。在本机可用内存不足的情况下，
新`tools/audit_special_condition_streaming_20261029.py`每次读取4096个子步，
仍遍历完整记录。来源、checkpoint/config/MJB/协议、原actor/filter收据、成功标签及
终态保持时间检查，直接使用SHA锁定的原函数前缀；未修改原函数文件或正在运行的后处理。
分块计算保留原门槛/分母/公式，以稳定部分和汇总；不是逐bit相同的浮点求和顺序。
额外检查NPY形状、格式和截断，旧数值容差`rel_tol=abs_tol=1e-10`保持。

`tools/check_special_streaming_audit_20261029.py`通过：

- 10001行明确的合成软件数据，257/4096/12000三种chunk与全数组算术对照；
  非有限值、错误dt、长度不齐、错误shape、截断zip五类拒绝。
- 四条已有真实条件003（第四组）的原审计逐项复核：ESN seed1提前abort、MLP seed1无接触、
  RNN seed2舒适100%、ESN seed3舒适0%。全部旧检查字段在原容差内一致，最大绝对差
  `6.821210263296962e-13`，主要为求和顺序；未用这些回归样本训练或选模型。
- 实际测试服务`sii-streaming-audit-check-20261029.service`自然exit0，runtime42.817s、
  CPU7.449s；实际CPU affinity=[6]、MemoryMax134217728bytes、swap0，
  memory.peak37941248bytes（约36.18MiB）。无cpu.max，因此不声称CPUQuota50%生效。
- 唯一待用八球v5的全部198绑定源保持。无新物理、数据采集、拟合、gate改动。

[检查证据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_STREAMING_AUDIT_CHECK.json)，
SHA256 `b0517cb20f036daf2125c46d6a2d5224af52ed8f08214384361dcfc57d042c9d`。
新auditor SHA256 `c0e65e64f63a9bfef0eb84a91dd52461266597a164db95709b236864da0792e8`；
checker `18b710dfc572cbc2941a46074e4ebf220d9a741efb7371aab8e15df622c67848`。
原完整auditor `98bd7a7c0ae89ba6b282d2f4e5e5c6e64ef2aa4da115e8b70207426257ae95fe`、
原条件auditor `64eae236f16b1973e93f8388f6737a5ffd29d5f7b451c5c3ee3dc739269e0fdc`未改。

## 派发状态

执行第五条件单CPU/128MiB/禁swap只读审计的自动权限复核两次超时；工具允许的一次重试已使用。
这是审批超时，不是安全性结论或科学审计失败。只读查询确认该unit为not-found/MainPID0，
`V8_CONDITION004_AUDIT.json`不存在。已向用户请求再次启动的明确回复，记录时尚未收到；
不要无回复再次派发同一动作。详见
[派发状态](evidence/NONRL_INTENT_RECOVERY_20261029/V8_STREAMING_DISPATCH_STATUS.json)。

已存在的原108/自动完整后处理不依赖这次可选条件审计许可，继续运行，不标记goal暂停/完成。
若用户允许，使用同一固定unit和输出执行已验证的新auditor，保持防重复；否则保留源码，
由原完整后处理在原108自然结束后覆盖全体。第五条件现有runtime快照仍是待独立审计，
不能拿四条旧记录的等价检查冒充第五条件通过。

后续主路线仍是原108完整审查归档→八球v5真实方向控制→三场景共享数据修复→公平重训→冻结回归。
开工main `334835c93d5de14b318fed673cb2182b2d3c11c7`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`实际fetch/read。无RL/子agent/服务器计算或用户数据删除。
四成员源码/检查/派发记录包已逐成员对本机、暂存及最终大小/hash核验，共享于
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_streaming_audit_preparation_20261029_v1/SOURCE_AND_CHECKS.tar.gz`。
6453bytes，SHA256 `4294f6e6df5b0f6502c505f675c5a58390ec9538d699fd1326f094b80dd7ff34`。
包不含本报告、未来第五条件审计或在途物理全集。
