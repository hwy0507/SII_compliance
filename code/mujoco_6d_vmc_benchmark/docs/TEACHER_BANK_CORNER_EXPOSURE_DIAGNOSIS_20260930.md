# 被动训练场景 v4 的曝光失败：几何定位诊断

2026-09-30。仅训练域诊断与初态预检；未修改冻结综合测试或接触筛选门槛。

## 已确认的原因

v4 首个 VMC passive_corner 完成完整 55 s，task/旧 strict 为 true，但新增真实边缘曝光为 false。
其 550,000 个物理子步没有 lift/carry 期间的 face/bridge 承载接触，正确保留为失败。
机器人事件只有 `office_v5_corner_top`，不能替代上抬撞边。

离线读取 XML 与保存的 qpos、object_position，按 payload quaternion 将方块包围盒转到世界坐标。
实现为 `tools/teacher_bank_corner_trace_20260930.py`，不 import MuJoCo、不构建环境：

| 几何 | v4 中心 / 半尺寸 m | 与 payload 保存帧的最小分离 |
|---|---|---|
| face | `(.475246,-.146582,.521273)` / `(.012,.010,.020)` | lift 至少 26.16 mm；carry 至少 29.41 mm |
| 北向 bridge | `(.475246,-.113291,.510)` / `(.006,.039291,.006)` | lift 至少 32.39 mm |
| 东向 connector | `(.524623,-.080,.510)` / `(.055377,.006,.006)` | lift 至少 77.74 mm |

lift payload 中心 x 在 `.53910–.54191`、y 在 `-.19036–-.18893`，face 和连接段偏左/偏北。
25 Hz 保存帧的 AABB 分离是离线辅助证据，不单独冒充物理子步接触审计；这里与实际曝光缺失相符。

对照旧 `teacher_repair_followup_20260930/corner/velocity025_stiff2`：其 face 位于 `(.650,.300,.440)`，
半尺寸 `(.012,.095,.080)`，也远离上抬路线。该回合的 robot contact event 同样只有 top。
所以旧 corner 的 task/strict 通过仅能证明原放置任务与其旧 gate，**不能追认“已经验证上抬碰 face”**。

## 训练域修正建议与初态证据

先由 nominal lift payload 的左边缘确定可接触的右边界，再根据各形状尺寸和 yaw 反算中心，
避免统一中心导致大尺寸 shape 向机器人初态内部扩张：

```text
face_y = -.190
right_x = .519  # 首个动态 pilot 建议值，之后须预注册训练分布
top_z = .535
extent_x = abs(cos(yaw))*half_x + abs(sin(yaw))*half_y
center_x = right_x - extent_x
center_z = top_z - half_z
```

保留各 shape 厚度、yaw 与摩擦；连接仍沿北向到 y=-.080，再向东连 top。
该方案的 purpose 是确保新训练障碍落在 nominal 上抬 swept volume，不是在筛选中降低真实接触要求。
若最终有尺寸/位置变化，必须冻结新的 source/fixture snapshot，保留 v4 失败。

独占本机单环境，仅执行 initial `audit_initial`，MuJoCo 3.11.0，1 线程，3 GiB 地址上限：

- 固定 face 中心三种方案 × train `0,1,2,333,666,999`：15/18 通过；thick_edge 三次均与 hand 初态穿透约 1.90–6.04 mm，全部保留失败。
- 边界对齐三种方案 `right=.517/top=.535`、`.519/.535`、`.520/.533` × 同六个 train：18/18 初态通过。
- 所有初态检查 `data.time=0`，没有物理步进；本子任务没有验证动态接触、滑开、任务成功。

## 小型证据

以下证据已逐文件SHA256核验归档；服务器目录：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_archive_20260930/evidence/`。
表中路径是本地执行来源，服务器使用同名文件：

| 文件 | SHA256 |
|---|---|
| `outputs/teacher_bank_geometry_preflight_20260930/v4_payload_trace.json` | `b2e4af6428dc1c040b854fdd49a1a931c106bccf517794445907c1b662d454cf` |
| `outputs/teacher_bank_geometry_preflight_20260930/original_corner_payload_trace.json` | `ffd0a76b13dc19498275a679a1844b4d8ceca607e1c65cca0b7e4a848da12179` |
| `outputs/teacher_bank_geometry_preflight_20260930/mid_lift_face_candidates.json` | `324f2ee350fc881e15ed756d427f8cd7a18f1ed563ee7334288478046a4d3d9a` |
| `outputs/teacher_bank_geometry_preflight_20260930/edge_aligned_face_candidates.json` | `e4ff7006eb8370fca414f98b0f60c5bdc7400ca3eec9f0b554fca20252d5c777` |

下一步必须由动态 pilot 检查：是否发生上抬碰边而非抓取前卡住，是否通过 task、安全和曝光联合 gate。
不能根据 18/18 初态通过宣称这些环境已经可完成。
