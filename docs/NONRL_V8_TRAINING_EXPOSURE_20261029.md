# v8训练曝光与不等时长场景权重

主矩阵仍未修复，Goal active。本轮检查实际保存的神经训练日程，排除补零计数、
跨身份混合或MLP/RNN曝光不一致；没有重新拟合、选模、物理积分或修改已有源码快照。

## 结果及对后续补采的含义

当前v8本来已经是不等长数据：棍推500帧、球750帧、桌角325帧/回合，actor间隔0.04s。
各场景8train+2validation并不代表各场景等权。

| 场景 | train帧 | validation帧 | 在各自集合中的帧权重 |
|---|---:|---:|---:|
| 棍推 | 4000 | 1000 | 31.7460% |
| 球 | 6000 | 1500 | 47.6190% |
| 桌角 | 2600 | 650 | 20.6349% |

实际训练源码使用逐帧目标；原数据importance为1（已有完整fit审计覆盖数据重建和权重），
验证选择也按拼接后的全部帧计算MSE。ESN的ridge使用全部train帧，神经网络分组重复呈现。
本表不是新权重方案，不改现有选择规则，也不将这种比例直接归因为当前失败。
后续补采后应复算实际帧份额和采样日程；不能仅靠每场景回合数宣称等权，
更不能为改善已看的回归结果悄然修改权重或模型选择。

| seed末位 | 每个神经候选的有效帧呈现 | 补零帧槽 | 终态所在epoch（从0计） |
|---|---:|---:|---:|
| 1 | 11266448 | 4733600 | 894 |
| 2 | 11253848 | 4746200 | 893 |
| 3 | 11262048 | 4738000 | 893 |

同一种子下24个MLP/RNN候选的schedule逐hash一致，三种子共72份全部核对。
各日程32000条update、末offset192，允许终态epoch未遍历完。
有效曝光的三场景份额与上述数据份额接近，精确每episode和scene计数保存在JSON。
补零帧槽只统计真正创建的张量槽；末chunk不足64不会虚增槽数。
这些计数不是不同方法计算量相等、独立梯度重放、收敛或任务成功证明。

## 新独立审计入口

`code/mujoco_6d_vmc_benchmark/tools/audit_special_training_exposure_20261029.py`
接受 `--root <完整训练目录> --output <新JSON>`。逐候选检查metadata及schedule hash，
对三份不同日程检查实际内容：只含train身份、同batch连续chunk、整批结束才换组、
每完整epoch各身份恰一次、逐chunk实际有效帧数与记录一致、末epoch允许有限截断。
再核对各候选报告的总有效曝光及同seed两家12候选日程一致。
它只分析保存的收据，不声称独立观察到每次optimizer实际执行。

变时长70/130帧手算边界（包括末epoch部分遍历）得到328有效帧呈现和60补零槽；
另五类损坏均拒绝：补零冒充样本、未知/验证身份、序列缺口、提前换epoch、重复身份。
检查源码完整保留在CHECK.json；这些是内存测试，不是合成示范训练。
实际72份日程全部通过，没有新发现的训练日程bug。

本机检查服务`sii-v8-training-exposure-20261029.service`自然exit0，800ms/CPU532ms。
实际affinity=[6]、memory.max128MiB、swap.max0；memory.peak达到128MiB、memory.events max709，
oom/oom_kill为0。包含文件缓存计费，不称有内存余量，也不宣称全主机swap为0。

- [实际审计](evidence/NONRL_INTENT_RECOVERY_20261029/V8_TRAINING_EXPOSURE.json)：37409bytes，
  SHA256 `0bd0b9a27ecbbff0fea441db7c9101e6a255a2d662736e6ec448d37318693bdc`。
- [检查及源码](evidence/NONRL_INTENT_RECOVERY_20261029/V8_TRAINING_EXPOSURE_CHECK.json)：3951bytes，
  SHA256 `c1634f4b83d2068656d2d38e0ad0716237e1c9383cb7a1ba92e3628ec89de246`。

工具和两证据共三成员逐字节核验，暂存及最终归档大小/hash一致：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_training_exposure_20261029_v1/SOURCE_AND_EVIDENCE.tar.gz`
10080bytes，SHA256 `e76f37d5212bd522bce1e3712361f3adf9a2851633b37b8e9a5fef5f9a9fae10`。

开工实际fetch/read main82f77f09/baselinef6e8f8c。05:03:45UTC原1172675及1201537仍active，
原矩阵71/108、条件007 MLP3在途。前一轮verified wait，本轮新增曝光审计工具和实际证据；
原108完整审查归档→唯一v6八球→正式三场景资格/覆盖/公平重训/闭环回归仍待。
没有重试可选004审计、启动v6或修改绑定源；当前原12条件仍为已检查回归集。
