# 三真实场景采集继续与冻结108入口准备

**最新：v5已于09:15:30 UTC完整30/30合格，原交接已启动公平拟合。** 下面“18/30、24/30、没有学生”是此前快照；正式九模型选择与108测试仍未完成。

本轮继续原Goal，前轮是实质进展，本轮原采集已验证live且推进；不重启原服务。
开工实际查询/fetch/read main `a13a92f6f71006bb51b4d33a00b6cf683c6a48c4` 与
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，两分支无新增本任务约束。
[前轮完整交接](NONRL_SPECIAL_BALL_STABILITY_20261028.md)。

## 原采集与训练状态

09:09 UTC附近读取原v5：18/30完整且合格，棍10/10、球前8条通过，ball_08在途。
上一轮失败的ball_01在本轮原条件下已完整通过。全部棍推真实手接触、越过、持续回位
及撤回时刻已逐条读取原V3行为审计：回位7.88–9.44秒，撤回12.80–13.00秒。
这些是采集资格，不是尚未训练学生的测试Task/Strict。

`sii-special-collection-v5-20261028.service` 原725751、
`sii-special-learning-handoff-v2-20261028.service` 原725995仍active；后者等待全30，
没有提前构建正式训练数据、没有新学生模型/正式108结果。全部交接登记源码hash不变。
所有模型仍按同一24train/6val、三seed、每家每seed12候选、神经每候选32000更新，
以同一验证requested-action MSE选择；有限预算不声称训练收敛。旧结果和失败全部保留。

## 冻结测试准备，尚未派发

新增 `tools/prepare_special_frozen_test_20261028.py`：在拟合完成前固定原12条件、
父协议、593个冻结物理Python来源、归档几何/参考/运行协议、测试协调器及拟合审计源码。
目标固定九个新模型×12条件=108；不读取测试成绩来选模型、不拆分局部参考时间。

准备目录 `code/mujoco_6d_vmc_benchmark/outputs/special_scene_frozen108_preparation_20261028_v1`，
登记SHA256 `51fdc49b05b202acdd3fdd919d316b8c1082f191303722cc9a856b15e51caebe`。
未来目标 `outputs/special_scene_frozen108_readout05_20261028_v1`，当前不存在。
此工具**没有后台自动等待器**；后续需在原拟合服务完整退出后，真实3GiB/swap0/单线程
服务中执行准备目录下的 `tools/prepare_special_frozen_test_20261028.py --root <准备目录绝对路径> --run`。
先确认没有已存在execution或测试目录；禁止重复派发。

执行入口只有在原交接状态为`fitting_complete_pending_test_review`、服务inactive/success、
九模型完整且所有固定输入不变时才运行全拟合审计；审计通过后才调用已保存的测试协调器，
由原全局计算锁保持单仿真。结束后只标记`evaluation_complete_pending_independent_audit`，
不能据此宣布Goal完成。异常保留原收据，不自动重启/覆盖。

首次预检把归档几何的原dt=1e-4字节hash直接与正式dt=5e-5模型hash比较，错误拒绝
`Frozen MJB drift`，发生在创建准备目录之前，零模拟步。查原冻结loader确认其规范流程为
加载原MJB，在内存设定已冻结5e-5，再序列化核验；新预检已按原流程修正，未修改归档模型。
实际MuJoCo3.11：归档SHA `173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11`，
正式SHA `d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`，与旧冻结协议一致。
这不是发现/修复了物理环境漂移，也不是重编译模型。

真实提前调用`--run`退出1并拒绝`Original fitting handoff incomplete`；没有生成execution、
FIT_AUDIT或测试目录。准备成功不等于九模型审计或新108测试成功。

## 完整矩阵保存证据审计准备

新增 `tools/audit_special_frozen108_20261028.py` 要求全部108与九模型完整：
逐条检查源、MJB、config、checkpoint、轨迹与子步hash，原actor/filter审计值，
固定条件与运行版本；重算子步RMSE/速度/峰矩/穿透、真实人体接触dt分母和机器合规。
独立重算Task/Strict全分母，SPT仅双成功且有完成时间的回合，完整108统一最短T_ref。
双成功缺时间直接拒绝；无双成功/无人接触为NA，不用0掩盖。给出每seed六指标及三seed
均值/样本标准差，任一种子缺值仍NA；不把少数成功上的条件效率等同整体任务能力。

实际验证使用**旧**new30首个ESN回合：1100000保存子步的RMSE28.395402609mm、
峰速0.375389187m/s、峰矩51.491859436Nm复算一致。故意将内存中的报告峰矩加1后拒绝；
合成Task-only成功更快的例子未影响双成功T_ref，缺失双成功时间被拒绝。
这是审计工具接口/算术预检，不是新模型结果；没有新增物理仿真。
两入口编译通过。最终新108全审计、正式图表、归档仍未完成。

审计范围是保存子步算术和证据链，不冒称独立动力学重新积分。当前12条件已被研究者查看，
只能称冻结当前测试组重评，不能称全新未见确认。舒适阈值仍是工程代理而非人体标定。

## 共享归档与后续状态

本轮小证据/准确提交前来源包已逐大小及SHA核验，无覆盖发布到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_special_frozen108_prep_20261028_v1/special_scene_frozen108_preparation_20261028_v1.tar.gz`。
62255字节，SHA256 `9ed9f05676b1ed84a562484a3ba4a18040113568f0c5e47d2c6a7a5ad491aeb2`，
[收据](evidence/NONRL_SPECIAL_FROZEN108_PREP_20261028/ARCHIVE_RECEIPT.json)注明范围。
不含live v5 raw、新学生或新测试，未使用服务器计算。

09:13:25 UTC原服务仍active，24/30已完成，棍10/10、球10/10均合格，corner_04在途。
采集MemoryCurrent1119170560、MemoryMax3221225472、swap上限0；交接等待完整30。
这是进度快照，后续须读取真实状态；尚无新模型排名。

## 全30完成与真实新学生训练启动

v5自然完成，棍10/10、球10/10、角10/10；原交接实际执行全30审查和builder成功。
数据15750帧：棍每条500、球750、角325；每场景8train/2val，合计12600训练帧、3150验证帧。
同一教师，未混入旧综合场景。数据SHA256 `8824c24df3991b0783c9954b8e6b0e81a9db1c8c4cf4333dd7d39040c94e3d86`。
`outputs/special_scene_retrain_readout05_20261028_v1` 已真实建立；190个fitting_source文件逐hash核验，
基准commit `e22724d455a44a17e74c334574b5a43bdf0b4204`，实际字节由快照清单确定。
原交接725995派生训练协调器746822，3GiB/swap0，OOM/OOM-kill均0；未重复启动新服务。

三ESN作业已各完成全部12候选。独立复核36个checkpoint hash与验证最小值，
三个所选模型各在完整15750观测上用旧冻结测试actor重放，全部逐数组相等、误差0。
三seed验证action MSE分别4.806492199e-6、4.002228821e-6、3.626354846e-6。
见[真实新ESN重放](evidence/NONRL_SPECIAL_FROZEN108_PREP_20261028/NEW_ESN_REPLAY.json)。
这只是示范模仿误差，不等于闭环Task/Strict成功，也不提前证明ESN优于未完成的MLP/RNN。

首个RNN候选seed2026102801/candidate00已实际完成32000更新，验证MSE6.195590951e-6，
NumPy/Torch导出差3.88578e-16。其余候选按原75作业计划继续；不据首个候选选择赢家，
不把有限预算说成收敛。当前六指标测试仍未启动，全部拟合完成后的全九模型审计仍待。

完整30 raw/全资格审查/新数据与拟合源码本地包
`outputs/special_scene_v5_complete_and_dataset_20261028_v1.tar.gz`，1670057992字节，
SHA256 `e6c2becee95f5eba53a3de1d6717a44dccdbf31eed41ca38fecdf0ea5281498c`；
正在上传独立incoming，不含运行中拟合和尚未开始的测试；归档最终状态后续按真实核验追加。

上述全量数据包及69314字节训练启动小证据包已传输完成，逐大小/SHA核验，无覆盖发布到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_special_v5_dataset_20261028_v1/`。
小包SHA `62a6349e6e53683f9e322f61d261a6bee1c221693a3544c47348b2200ec1a3f3`，
[完整范围收据](evidence/NONRL_SPECIAL_FROZEN108_PREP_20261028/DATASET_ARCHIVE_RECEIPT.json)。
本地完整包gzip测试通过。运行中学生checkpoint/history不在此包，后续独立归档；旧v4失败包仍保留。

发布前原训练已完成8/75作业，当前`mlp_scratch_s2026102803_candidate00`，实测3836更新。
原725995/746822身份保持；实际内存1360064512字节、上限3221225472、swap上限0、OOM/OOM-kill均0，
全部190拟合源hash未变。完整九模型锁/全拟合审计/108闭环和最终图表仍未完成，Goal active。
测试准备科学提交048b9027、整合远端RL进度e22724d4已push；非快进拒绝后正常合并，无force。
