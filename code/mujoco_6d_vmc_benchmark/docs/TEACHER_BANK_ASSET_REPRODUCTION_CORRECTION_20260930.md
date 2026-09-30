# 资产清单遗漏修正与模型静态复现

2026-09-30准备Spark复现时发现：v10原清单只含85个Panda文件，但场景使用FR3本体与
Panda手。此前“已核验全部实际运行资产”的说法不准确，应更正为“当时只核验了清单中的
Panda文件”。旧plan、manifest、execution和审计记录保留原样，未改写或重启稳定作业。

完整清单为133文件：FR3 48、Panda 85，共95,795,982字节。保存XML实际引用两树中的
44份mesh，清单另含生成用XML及辅助资源。清单SHA256：
`56b0e9d07c2b0e5636f38fb228dbd077980d2ea14c2ea26bc8987be11a304523`。
133文件已逐项核验共享到新目录，旧85文件归档未覆盖：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_runtime_inputs_complete_20260930/menagerie/`。

## 已完成的静态复核

三类×训练anchor 0/337/671共九个原始模型，用冻结source、原fixture/request及完整当前资产
重新走真实初始化，截获第一次`mj_saveModel`即退出：**9/9 MJB与历史文件逐字节一致**。
这证明这些资产及冻结初始化能复现本机实际使用的模型；没有复制历史模型数组来凑匹配。
`mj_step/mj_step1/mj_step2`全部设置为拒绝调用，九次调用计数均为0；未运行动态回合，
未读取validation轨迹。各进程独立、单线程、MemoryMax=1GiB、MemorySwapMax=0，
地址空间上限2GiB；最高RSS570456KiB。冻结runner要求3GiB地址上限的请求被记录并保持
更严格的2GiB限制。静态退出的finally产生空exposure文件，不把它当有效轨迹。

相应源码：`tools/teacher_bank_static_source_rebuild_20260930.py`；完整资产解析及历史
XML-only诊断：`tools/teacher_bank_asset_audit_20260930.py`。重建使用本机原Python3.11.15、
MuJoCo3.11.0、NumPy2.4.6/SciPy1.17.1运行环境。每个case保存脚本、request、原始/重建MJB
SHA及完整资产hash。已有跨方法/候选MJB配对证据仍有效；未借此声称未执行的3300环境均有效。

## 为什么直接重编译保存XML没有通过

先前以保存`rollout.xml`重新编译的9次结果全部不逐位一致，失败产物继续保留。不是通过
修改XML追认成功，而是另走真正初始化路径验证。已定位：

- 原FR3 XML的collision默认`mass=0,density=0`未被导出的XML完整保留。短撞anchor0
  重编译时固定基座质量从2.820672变为5.817141kg；mesh数组本身一致。
- `audited_velocity_env.py:971`在初始化禁用原rod_geom的碰撞mask；MJB记录0/0，而
  保存XML仍为16/31。另有浮点数序列化精度差异。

因此保存XML不是完整模型状态的无损恢复入口；应使用原MJB，或冻结source与匹配资产重建。
validator先保存MJB再导出XML，成功的source重建解释了为什么XML复编失败不等于历史物理
模型改变。首次1GiB地址空间的XML审计在保存模型时内存分配失败，也已保留；随后2GiB
地址空间的XML诊断最高RSS953284KiB，没有继续抬限反复尝试。

## 代码修正与尚未完成

工作副本的未来`prepare`现在校验FR3/Panda必需模型XML及引用mesh，冻结两树全部文件；
`verify_assets`明确返回覆盖范围，旧Panda-only清单标为覆盖不全。新plan的资产共享地址
在核验前为pending，不能再自动指向旧85文件目录。资产与原选择相关12项测试通过。
本次仅修审计覆盖和复现工具，不改变物理、gate、actor或执行器，未修改v10冻结源。

Spark与本机架构及NumPy/SciPy不同。首个`active_short_train_0000`冻结源码静态重建零积分，
但MJB不一致：22个数组存在差异，包含约1e-16至1e-13浮点差、mesh normal最大1.79e-7
及BVH排列。BVH数组差不能直接解释为物体位移；也不能声称仅路径变化或物理等价。
其余八个ARM anchor未运行，动态补充采集没有启动。原MJB在ARM可无损加载/重存，
但这不证明从source编译或闭环数值等价。独立collection driver拒绝
`compatible_for_collection=false`；本轮继续原本机单环境，不放松兼容性条件填满算力。

本机静态审计、XML失败证据、资产工具/测试及当时的采集/展示工具112文件已逐项核验至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_1104/evidence/`。
ARM差异和阻断证据已核验至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_spark_static_source_20260930_v1/`。
1104快照是归档时版本，后续补充说明与公平指标共同缺失处理以Git新提交为准，不冒充已经
包含在此前归档中。上述133文件资产目录另有逐项核验凭据。
