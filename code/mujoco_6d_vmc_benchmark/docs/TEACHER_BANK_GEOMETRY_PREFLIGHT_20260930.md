# 训练厚桌角连接段初态几何预检

2026-09-30，独立训练场景，不修改冻结综合测试。这里只检查初始几何，**没有物理时间积分、任务成功或动态接触通过结论**。

## 原失败

`teacher_bank_three_domains_20260930_v2/pilot/passive_corner/vmc` 的直线 bridge 从 face 沿 x 连接 top，
与机器人 geom 60/61/64/65 初始穿透约 1.60–7.80 mm，被未修改的 `audit_initial`（10 μm 阈值）拒绝。
原失败记录保留在本地研究目录 `outputs/teacher_bank_three_domains_20260930_v2/pilot/passive_corner/vmc/run.log`。
未降低门槛、未关闭碰撞、未覆盖失败。

## 可行初态构造

实现：`tools/teacher_bank_geometry_preflight_20260930.py::routed_training_xml`。
先应用当前训练场景参数，再移除原训练 bridge，添加两段刚性 world-body box：

1. 从变动后的 face 中心 `(face_x,face_y)` 沿 y 到 `route_y=-.08`。
2. 从 `(face_x,-.08)` 沿 x 到 `top_min_x+.004=.574`，与原 top 有实体重叠连接。

两段中心高度均 `.510 m`，半厚/半宽均 `.006 m`。纵向端部多伸 `.006 m`，确保两段及 face 连接。
两段命名为 `office_v5_corner_training_bridge` 与 `office_v5_corner_training_bridge_connector`；
训练曝光审计显式识别这两个名称，仍不接受 top 放置支撑冒充碰撞。
face 的角度、形状、偏移和摩擦继续采用原训练 fixture，最终 top 与放置任务不变。

## 验证结果

使用 canonical Python 与 MuJoCo 3.11.0，单线程、进程地址空间上限 3 GiB。
每次只构建一个环境，执行现有 `audit_initial`，关闭后再下一个。所有检查 `data.time=0`。

- 首批 train 索引 `0,1,2,333,666,999`：6/6 初态通过，约 1.04 s。
- 扩展 train 索引 `3,17,41,59,83,101,137,167,197,227,257,287,317,347,377,407,437,467,497,527,557,587,617,647,677,707,737,767,797,827,857,887,917,947,977,998`：36/36 初态通过，约 5.42 s。
- 合计 42 个不同训练 fixture，覆盖三个 face 形状；没有读取 validation 或封存测试条件来选择几何。

本地小型证据（相对研究目录），服务器归档待主 agent 校验，不声称已共享：

| 文件 | SHA256 |
|---|---|
| `outputs/teacher_bank_geometry_preflight_20260930/route_north08.json` | `477af805d68be73d020842424a5ade9fd52ce8de7d43ba54113c573d21e3d4dc` |
| `outputs/teacher_bank_geometry_preflight_20260930/route_north08_expanded.json` | `e2e8e891a653dd2cc78a5a4f1626acde5dfc2fc7a44a39b4a66c052246a9c904` |
| `tools/teacher_bank_geometry_preflight_20260930.py` | `9f44527f483873afab9bb21ba92c254cd06a73d3bce658d8bde489de80d4ec1d` |

每条 JSON 记录保存 fixture-id、seed、route、XML hash、初态手位置和通过/失败原因。
这不是对全部 1000 个被动训练条件的初态认证；尤其不能据此声称完整上抬碰撞、滑移、放置已成功。
下一步由主 agent 将相同构造纳入新的不可覆盖 run snapshot，执行三类动态 pilot；仍保留 v2 失败。
