# SimbaV2 修复截止交付（2026-10-01）

结论：尚未达到可靠论文 baseline 的稳定抓取要求。奖励尺度修复改善了同20k对照的数值指标与物理有效性，但12条有界策略轨迹的物块最大抬升和水平位移均为0，未夹起或搬运。不能以审计通过、阶段或低RMSE冒充任务成功。

熵诊断实际安全停止于约48.5–50k，共同40k；有界奖励两seed在13:12UTC安全停止，评测共同20k，不称完成目标30k。训练实际末checkpoint步数以runner_state为准，progress文件可能停在上个100步刷新。两者都是看过主结果后的开发诊断，不覆盖100k历史，不是独立确认，也未证明充分训练或算法本质强弱。

6.4秒dt5e-5 hooks物理不变性通过，全部状态差为0；旧四路训练保持暂停，旧heartbeat未恢复。所有源/原始轨迹/模型/媒体留Spark。

# 独立熵目标诊断（主结果之后的探索）

状态：complete；共同step：{'step': 40000}；已完成48/48条。

standard=-0.5、low_entropy=-2.0；其他训练配置相同；两奖励各2个配对seed。测试条件已经见过，不是独立确认。

| Reward | Entropy setting | n | 55s | physical | placement | RMSE cm | peak Nm | peak m/s |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| office_task | standard | 12 | 10 | 8 | 0 | 12.7311 ± 14.12 | 46.6373 ± 5.086 | 0.179571 ± 0.08339 |
| office_task | low_entropy | 12 | 12 | 10 | 0 | 47.9052 ± 24.35 | 58.7118 ± 2.595 | 0.306387 ± 0.1538 |
| metric | standard | 12 | 12 | 11 | 0 | 32.081 ± 5.786 | 40.3601 ± 5.356 | 0.167908 ± 0.06494 |
| metric | low_entropy | 12 | 12 | 12 | 0 | 20.0171 ± 2.844 | 47.9303 ± 14.11 | 0.14282 ± 0.05473 |

全部失败保留。若存在提前终止，指标均值仅描述实际记录，不作完整55秒统一排名。

## 阶段及逐类局部响应

- office_task/standard: stage={'approach': 12}; events={'ball': {'unknown': 11, 'failed': 1}, 'person_hand': {'failed': 5, 'unknown': 1, 'not_exposed': 6}, 'rod': {'not_exposed': 9, 'failed': 3}, 'office_v5_pillar': {'not_exposed': 12}}
- office_task/low_entropy: stage={'approach': 12}; events={'ball': {'not_exposed': 6, 'unknown': 6}, 'person_hand': {'not_exposed': 8, 'unknown': 3, 'failed': 1}, 'rod': {'not_exposed': 12}, 'office_v5_pillar': {'not_exposed': 12}}
- metric/standard: stage={'approach': 12}; events={'ball': {'failed': 6, 'not_exposed': 6}, 'person_hand': {'not_exposed': 10, 'failed': 2}, 'rod': {'not_exposed': 12}, 'office_v5_pillar': {'not_exposed': 12}}
- metric/low_entropy: stage={'approach': 12}; events={'ball': {'unknown': 12}, 'person_hand': {'not_exposed': 3, 'passed': 2, 'failed': 7}, 'rod': {'not_exposed': 10, 'unknown': 1, 'failed': 1}, 'office_v5_pillar': {'not_exposed': 12}}

## 审计

错误：[]；待完成：[]。
raw子步复算、原始时长、同条件MJB、checkpoint路径/seed/hash/共同step、manifest及记录的normalizer诊断核对；不以阶段或未曝光替代成功。


# 有界指标奖励修复：独立开发对照

共同step=20000；完成36/36；状态complete。

两训练seed，均使用entropy=-2；原任务/原指标控制复用低熵实验同step。不是主100k结果或独立确认。
新跟踪训练成本e²/(.12²+e²)，保留原始RMSE/峰矩/峰速。阶段不是抓持成功证据。

| 版本 | reward | n | 55s | physical | task | placement | RMSE cm | Nm | m/s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bounded | metric | 12 | 12 | 12 | 0 | 0 | 18.298423419850195 ± 0.1772165985241654 | 49.359032122244315 ± 2.7910982449587194 | 0.1523188218488972 ± 0.016610802651318087 |
| original | metric | 12 | 12 | 8 | 0 | 0 | 57.193280082089714 ± 22.879499593316925 | 54.98925292070581 ± 7.05033891526532 | 0.19286871310520454 ± 0.0761196999684506 |
| original | office_task | 12 | 12 | 12 | 0 | 0 | 60.8548826643581 ± 3.404045904729536 | 48.78601397230486 ± 3.618348882916127 | 0.2357403888915905 ± 0.04733685984419514 |

任何提前结束均保留，混合时长均值仅描述，不做55s统一排名。

审计错误=[]；pending=[]。

- bounded/metric阶段诊断：{'approach': 12}
- original/metric阶段诊断：{'approach': 12}
- original/office_task阶段诊断：{'approach': 12}


## 有界修复逐类接触证据

```json
{
  "bounded/metric": {
    "ball": {
      "unknown": 5,
      "failed": 1,
      "not_exposed": 6
    },
    "person_hand": {
      "not_exposed": 12
    },
    "rod": {
      "not_exposed": 8,
      "failed": 3,
      "unknown": 1
    },
    "office_v5_pillar": {
      "not_exposed": 12
    }
  },
  "original/metric": {
    "ball": {
      "failed": 11,
      "unknown": 1
    },
    "person_hand": {
      "not_exposed": 12
    },
    "rod": {
      "failed": 2,
      "passed": 7,
      "not_exposed": 3
    },
    "office_v5_pillar": {
      "not_exposed": 12
    }
  },
  "original/office_task": {
    "ball": {
      "unknown": 8,
      "not_exposed": 4
    },
    "person_hand": {
      "not_exposed": 5,
      "unknown": 4,
      "failed": 3
    },
    "rod": {
      "not_exposed": 10,
      "failed": 2
    },
    "office_v5_pillar": {
      "not_exposed": 12
    }
  }
}
```

接触unknown/未曝光保留，不推断整体柔顺能力。原始物块轨迹审计见 OBJECT_MOTION_AUDIT.json；不能将主任务未完成概括为每个局部响应均失败。

预算限制：仅2个训练seed，SD是六条件均值之间的样本SD；20k/40k不与主100k混为公平排名。未完成项：稳定抓取、搬运、放置，以及抓持后的接触恢复/推进验证。
