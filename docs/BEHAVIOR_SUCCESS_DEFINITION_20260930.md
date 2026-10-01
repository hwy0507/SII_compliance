# Office 行为成功定义修订（2026-10-01）

撤销未提交的stage+lift草案：进入carry并发生接触不能证明接触后恢复。原始task_success和placement_complete保留，新增局部compliant_progress_success；strict再要求完整时域、原physical_valid及无明确落地掉落证据。

## 开发操作定义

- 球撞后停稳恢复：真实偏离后，在接触起点后5秒内回到12mm、0.12rad、0.025m/s并保持0.2秒。未偏离单列，不捏造零秒恢复。
- 球撞后继续推进：接触后真实重入接触起点冻结的原目标位姿带，再有至少1cm末端净位移和1cm实际有符号路线净进展并保持0.2秒。允许正常切换waypoint，单纯改参考/阶段不算。
- 承载接触中局部滑移：5秒窗口内至少0.4秒接触，相对障碍切向净位移、末端任务方向净投影、实际路线净增都至少1cm，保留到窗口末端至少0.2秒。
- 最多0.08秒间隙合并为交互窗口，另报占空比与最大间隙；不冒称严格连续受推。
- 后续独立冲击、竞争障碍、参考跳变、接触身体集合改变限制归因。证据不足unknown；接触不足not_exposed；有证据但未恢复failed。
- 局部成功不要求最终放置，也不证明完全绕出或之后不再卡住。clearance目前unknown，不能把局部指标叫端到端任务成功。
- 0.5/1/2倍空间阈值对全部方法复算，固定时间与物理门槛，不挑最有利阈值。

4ms日志累加全部物理子步接触时长/冲量/峰值/法向，保存末端与参考位姿、速度、相对障碍位置、实际路线进展、物块位置。真值仅用于离线评估，不给actor。力评价与post-step位姿有一个物理步以内时间差，数据中明示。原physical_valid只检验既定数值物理门槛，不独立认证低力安全；峰值力矩/速度/接触力仍另报。

## 旧证据修正

旧三条ESN在Spark镜像中缺原始连续NPZ，新行为均unknown。combined_v4_development实际是含杯combined_contact_v2：carry在9.68秒，柱首次接触12.9168秒并持续到55秒，缺cup接触不能删掉。corner-only手碰角发生在抓取前，不能据此宣称持物蹭角已验证。
审计保存在：
/home/arm1/vmc_mujoco_runtime/SII_compliance_eval_2e37ddc/outputs/behavior_success_audit_20261001/

新复评为明确不同的无杯single-pillar v4；所有方法共享新条件，旧含杯结果不混算。纯ESN模型与显式75%VMC+25%ESN也分别命名。

## 训练终末目标

新增task_physical：literal placement_complete AND task_success AND physical_valid且无abort，不要求contact_coverage。这样真实稳定放置不会因为少撞一个障碍获得失败奖励；旧legacy_strict保留用于重放。
两奖励组仍优化完整物块任务，没有偷偷把离线局部行为判据变成训练奖励。曝光、局部柔顺推进、完整放置分别汇报。

代码目录：
/home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/
记录器：
/home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/scripts/behavior_telemetry_20261001.py
审计：
/home/arm1/SII_compliance_baseline/docs/TRAINING_OBJECTIVE_AUDIT_20261001.md

20项事件反例、7项终末目标断言、4项旧证据反例通过。10秒开关logger的物理轨迹、动作、指标差为0；正式冻结前再次按最新source hash验证。这是已实现的开发协议，尚不代表最终排名。
