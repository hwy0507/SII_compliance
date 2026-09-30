# v5 抓取前卡住：手掌扫掠与厚边候选

## 动态失败的准确归因

v5 首条 passive_corner/VMC 完整运行 55 s，最终仍在 align，payload 未上抬；task/strict 均 false。
不是手指夹不到物块：现有物理接触统计明确 `office_v5_corner_face.robot_parts=['hand']`。

- face 首次手掌接触 `0.6108 s`，累计 `44.4124 s`，接触峰值约 `1668.10 N`。
- 随后 top 也与 hand 接触，累计 `40.6694 s`，峰值约 `1584.89 N`。
- 末端最终约 `(.54506,-.19472,.55702)`，应接近的拾取参考高度约 `.5279 m`；上方边缘挡住下降路径。
- 电机峰值力矩约 `34.52 Nm`、外部穿透约 `0.00703 mm` 并不意味着接触温和。低电机峰值不能替代接触力检查。
- 旧 strict 的 contact_required 在 settle 中为空，而新增真实曝光仍正确拒绝本回合；不能删除曝光条件来晋级。

## 离线计算方法与证据边界

新增 `tools/teacher_bank_hand_clearance_20260930.py`：只读取已存 XML、STL、qpos；无 MuJoCo import 或环境。
用 XML 运动链复算 FK，手部中心与已存 hand 最大差异约 `6.16 µm`（包含原日志时间取样差异）。
对手掌/腕部 STL 构建 SciPy convex hull，再把三角面裁剪到候选障碍的 XY 盒，计算真实表面高度范围。
这比仅用整体 AABB 更准确，但仍是离线几何依据，不能替代 MuJoCo 动态验证。

### 低矮 payload 边缘方案

在旧 face XY 盒 `[.493,.519]×[-.199,-.178]`：

- 正常 v4 的 align+grasp 期间，手掌 convex hull 最低表面约 `.482383 m`。
- payload 初态顶面约 `.450 m`。
- 因此 `top=.475–.478`、`bottom>.451` 的局部薄边有约 4–7 mm 手掌净空，允许约 20–25 mm 总高度。
- 原 face 总高度 40–56 mm 不能在该局部窗口原样放入：底部过低会与初始 payload 相交，顶部过高会挡手掌。

这是可研究的较薄边训练子类，但不宜拿它冒充原本的厚桌角。没有修改阶段、下降轨迹或碰撞 mask。

### 保留厚度的上方掌翼方案

直接把原 XY 的 face 往上抬并不可行：初态 link7 在该处占 `.600–.655 m`，link6 占 `.656–.789 m`。
它们填满所谓“手掌上方”的窗口，会初态相交。

把目标移到手掌向南突出的翼部（约 y=-.270），可离开腕部投影：

- 广域 XY `[.505,.530]×[-.280,-.260]` 内，初态 hand 上界 `.61760`，lift 上界 `.67409`；
  link6/link7 在该域的 approach/grasp/lift 保存帧无覆盖。
- 必须进一步检查实际窄边：`right_x=.515` 的窄盒未与 hand 相交，虽然初态通过，却可能没有曝光，故不推荐。
- `right_x=.519` 的实际窄盒内，初态 hand 上界 `.58624`，lift 上界 `.64916`；
  `underside=.633` 落在两者之间，是更合理的动态 pilot 起点。

候选规则（尚未宣称动态成功）：

```text
face_right_x = .519
face_y = -.270
face_bottom_z = .633
center_x = face_right_x - (abs(cos(yaw))*half_x + abs(sin(yaw))*half_y)
center_z = face_bottom_z + half_z
```

原 shape 总厚度 40/56 mm 保留。静态结构不能往北穿过腕部，因此采用 `outer_south`：
face 沿 y 到 `-.480`，沿 x 到 top 中心 `.650`，外侧竖柱下降到 z=`.510`，再沿 y 接回 top 的 `-.330`。
整个结构均为真实刚体碰撞几何，始终存在，不用阶段开关、teleport 或禁用碰撞。

## 初态预检与后续

在 root 暂停占用后，独占一个 MuJoCo 环境，1 线程、3 GiB 地址空间上限，执行原 10 μm `audit_initial`：

- 三个上方候选 × train `0,1,2,333,666,999`，共 18/18 初态通过，所有 `data.time=0`。
- 推荐 `.519/.633/-.270` 是其中第二组，6/6；不是由 `.515` 的通过结果推断而来。
- 尚未动态验证是否真实上抬接触、是否能侧滑以及能否完成放置。水平 underside 可能使缺少侧向响应的 teacher 停住，必须保留这种失败。
- 没有实施抓取后新增横移或任何训练 task 阶段修改；上方掌翼方案优先保留原任务。
- 本子任务已释放仿真槽位，交由主 agent 跑 versioned pilot。

所有小型证据位于本地研究目录 `outputs/teacher_bank_geometry_preflight_20260930/`，服务器归档待主 agent 核验：
`v4_hand_clearance_convex.json`、`v5_hand_clearance.json`、`v4_upper_{hand,link5,link6,link7}_window.json`、
`v4_wing_{hand,link6,link7}_window.json`、`v4_wing_shallow_hand_window.json`、
`v4_wing_right{519,523,527}_window.json`、`upper_wing_face_candidates.json`。
这些文件保存输入与 mesh SHA256；原 v5 失败未覆盖。
