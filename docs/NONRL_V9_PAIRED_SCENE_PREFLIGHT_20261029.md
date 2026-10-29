# v9配对场景接续：执行入口校正与最终指标缺口

## 当前状态

原108组合迁移回归在2026-10-29 14:32UTC快照为40/108，Task3、Strict0、双成功0，SPT为NA；宿主scope active，OOM0、实验swap0。最新18条开发配对尚未启动物理，唯一等待器为`sii-v9-paired-closure-handoff-v3-20261029.service`，PID1636845、Invocation39a747c69fe447dd83cc9d2eb2dc88dd；只在原108 complete及scope inactive后派发，12h等待限时、CPU6/1线程/3GiB/禁swap。

上一轮为progress，本轮为progress：发现并在派发前修正待运行配对检查的球场景入口错误，补充物理worker等价性守卫和审查工具；没有重训或新学生成功证据。持续Goal尚未完成。

## 入口错误及修复范围

v1/v2原拟使用`run_video_reference_vmc_20261028.py`，但v9正式球示范通过`run_registered_special_coverage_20261029.py`调用`run_primitive_coverage_20261029.py`，显式设置初始位置、搬运位移、球角度。旧入口不消费全部coverage参数，因而不能声称同条件配对。此错误属于**尚未运行的后继检查器**，不能倒推说v9训练数据或已完成的108结果因此生成错误；它们保留原来源和真实语义。

v2仍在等待、无student execution时已停止。v3改用已有`run_video_reference_coverage_20261029.py`及对应`qualify_ball_coverage_demo_20261029.py`。没有改这些既有物理文件或采集wrapper。v1/v2服务宿主查为not-found/inactive，v3唯一active；旧登记和收据原样保留，不依据陈旧HANDOFF的waiting字样误报仍在运行。

准备器新增的AST核验仅允许正式采集专用guard、不可达的collection validator导入与归档collector名称差异；剩余worker必须一致。另核make_actor、verify_actor、main函数AST相同，并逐一比对六个teacher身份实际执行wrapper SHA和其SOURCE_HASHES中的全部scripts。新登记共18case（3scene×train00/validation08×3family、固定seed2026102801）。

正向原源码等价通过；三个物理差异突变（dt5e-5→1e-4、公共动作尺度减半、球入口改回旧primitive）均被拒绝。v3全部登记源hash核验通过；在原108在途时执行派发入口，实际前置拒绝且未创建student execution。证据见`docs/evidence/nonrl_v9_paired_scene_preflight_20261029_v3/`。没有把静态核验称为物理复现成功。

## 已准备的18条完整审查

`tools/review_v9_paired_scene_closure_20261029.py`拒绝不完整18条，逐一核同身份的参数、MJB、filter、config、checkpoint、qualification和全部来源hash；完整保留失败，分train/validation与方法汇总。它将对比学生在teacher历史上的模仿误差、teacher在学生历史上的反事实动作差异，以及学生真实动作饱和/场景行为与安全指标。

反事实teacher输出没有在动力学中执行，也不得加入训练或充当因果证明。审查工具编译及CLI导入通过，真实18条审查尚未执行。正确运行入口为：

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=scripts:tools taskset -c 6 /home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python tools/review_v9_paired_scene_closure_20261029.py --root outputs/nonrl_v9_paired_scene_closure_20261029_v3 --output outputs/nonrl_v9_paired_scene_closure_20261029_v3/REVIEW.json
```

解释器实际绝对路径：`/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python`，工作目录`code/mujoco_6d_vmc_benchmark`。18完成后才能执行审查，不能用其六个旧validation身份声称未见泛化。

## 正式六指标仍需完成的证据

| 项目 | 原108 | 当前特化场景资格审计 | 后继要求 |
|---|---|---|---|
| Task | 原office终态放置gate | 原特化任务各自的成功条件 | 明确任务语义并先冻结；不能跨任务混合成功率 |
| Strict | 原冻结Strict | development safety/qualification | 资格合格不冒充原office Strict；最终协议须有完整固定安全判据 |
| 双成功SPT | 首次持续终态成功时刻已有原记录 | 通常只有final success，无首次持续成功遥测 | 不以episode时长、release/retreat事件或final bool代替完成时刻；补齐后再正式跑 |
| 平均峰值力矩 | 有全回合子步 | 有逐关节子步/峰值 | 全回合分母含失败，继续保留 |
| 人舒适度 | 实际人体接触dt | rod/ball扰动代理；corner没有该接触 | 无人体接触为NA；扰动代理单列，不冒称人体测量 |
| 机器合规率 | 独立于Strict | 现有外部穿透、力矩、finite等 | 显式沿用固定违规判据，失败与abort留分母 |

因此18只用于修复前定位，并不是正式主矩阵。最终新场景测试不得复用已选模validation；未记录的完成时间不能从成功标志猜测，不能通过放宽gate修复表面指标。
