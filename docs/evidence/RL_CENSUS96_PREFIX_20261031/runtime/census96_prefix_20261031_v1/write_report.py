from pathlib import Path
import json
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/census96_fixed95_terminal_20261031_v1';read=lambda p:json.loads(p.read_text())
p=read(D/'prefix5000/REVIEW.json');reference=read(T/'reference95/REVIEW.json');ob=read(D/'ONLINE_OBSERVATION_REVIEW.json');w=read(T/'LAUNCH.json');assert reference['passed'] and ob['passed'];growth={m:ob['last_steps'][m]-ob['first_steps'][m] for m in ob['first_steps']}
table='|方法|原loss首1000|原loss末1000|原loss最大|条件估计最大|actor首→末1000|\n|---|---:|---:|---:|---:|---:|\n'
for m,e in p['methods'].items():
 s=e['stats'];a=s['agent_train/original_sampled_q_loss'];c=s['agent_train/conditional_terminal_q_loss'];ac=s['agent_train/actor_loss'];table+=f"|{m}|{a['first1000']:.9f}|{a['last1000']:.9f}|{a['maximum']:.9f}|{c['maximum']:.9f}|{ac['first1000']:.6f}→{ac['last1000']:.6f}|\n"
entry=f'''## 2026-10-31 — 第96轮固定前5000已审；全8533完整95终端参考与比较等待

- [交接](docs/RL_CENSUS96_PREFIX_20261031.md)。固定first5000原始字节/全部metrics/保存算术及实际九栏图通过；原loss最大I1.655/A1.464/V1.301，波动和actor漂移保留，无完整96或收敛结论。前缀terminal_population2845/2844/2844无新增。
- 全8533终端完整95 CPU参考通过，旧8443预测按原≤93/新94块精确复现，新90条95终端原transition/episode绑定；全learner/Adam/replay/RNG与checkpoint不变、独立保存算术通过。保留全部五critic/原mask、79/90/92中止及93失败，不是96改善或独立泛化。
- 实际三partial96拒绝完整检查；唯一等待器{w['pid']}沿修正版archive原截止等待完整96，未增训练。原99身份{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}。原gamma审查失败及修复记录保留；原94–96窗口/A19.7689%必要条件失败、4m不足完整97、Direct原结论和指定ESN缺失保持，Goal active。
'''
(D/'ENTRY.md').write_text(entry)
body=f'''# 第96轮前缀审查与完整95全部终端参考

第96轮原三路训练、90sampler和修正版archive继续；本轮零新增科学训练派发，所有诊断零physics/optimizer更新。Goal active，reward平稳和原loss健康的联合收敛验收未完成。

## 固定first5000原始loss

在读取本轮loss数值前锁定每方法前5000次更新，原JSONL前缀逐字保存并再次回读相等，step连续/update_index0，全部metrics有限。保存NPZ逐字段精确，math.fsum独立首末1000/均值/极值与NumPy结果核验通过。原抽样、条件估计、actor九栏图已实际查看，收据 `{D}/PLOT_INSPECTION.json`。

{table}

原loss均值I.951134/A1.024960/V.739975。I仍有重复尖峰、均值接近水平，actor逐渐上移；A/V原loss首末均值略升，actor也略向上变化。此前缀未见非有限值或接近0的loss坍塌，不代表完整96健康或收敛。原sampled_q_loss与conditional_terminal_q_loss分别保留，不能用后者替代健康口径；health4096 TD仍是未投影固定min-pair诊断，与正式投影/I-min/A-V-mean目标不同。

first5000 terminal_population恒为2845/2844/2844，没有新增终端；这不是终端cache实际增长证明。完整95原loss尖峰、A long0900 Task/Strict失去、部分critic/样本退化和全部历史失败保留。

## 全部8533终端参考与精确恢复

`{T}/REFERENCE_PLAN.json` 在CPU推理前登记完整95所有done行：I2845/A2844/V2844，共8533，1200秒有限预算、CPU11、全5critic/原mask。完整95checkpoint、协议、全部来源与runtime哈希绑定，严格恢复完整learner/Adam/replay/RNG，推理前后digest和checkpoint hash不变、无梯度。

完整95参考的masked SSE总量I591.506459/A155.162374/V89.453603；其中新增95终端分别32.124715/23.291275/1.965561，旧≤94部分仍精确对应559.381744/131.871098/87.488042。全部保存数组另用独立标量分组复算通过（REFERENCE_GROUP_REVIEW），不是96改善结果。

旧8443条输入、动作、reward、masks与上次固定94数据逐元素相同，full95预测与保存complete95精确相等；新95的90条终端从剩余全部done索引提取，与原transition step/condition/reward和完整30episode标签/1375步/55s/无abort逐项绑定。保存indices/obs52/actions/rewards/masks/cycles/conditions/initial_prediction，回读逐值及独立标量masked和all-row SSE核验通过，不筛选低误差样本。

CPU forward保留原≤93块和新增94块的形状，再加入新增95第三块；96比较也使用相同三块，避免把批形状数值差异当成权重变化。历史79/90/92中止和93放置失败3851694原索引/标签保持。这里只构建完整95参考，没有训练或推广辅助权重，不是96预测结果或独立泛化证明。

## 完整96比较与拒绝保护

`{T}/PLAN.json` 绑定全部参考hash、真实96协议、完整95审查、30份96原锁定源码；消费者 `{D}/terminal96.py` 与 `wait_terminal96.py`。全baseline保存算术预检通过，缺完整96拒绝；三份真实startup_repaired96快照通过架构校验但complete=True均被拒绝，未把partial当完成。

后续须等待完整96的review/health/loss/FINISHED，严格加载全state，核验所有保留95终端索引/字段，输出all5 masked及all-row SSE、≤94旧组/新95组、所有逐行预测、已知失败与退化计数及最大20行，保存后再独立复算。最终图仍须实际查看。**完整96固定终端比较尚未运行。**

唯一等待器PID{w['pid']}/start{w['start']}；绑定修正版archive PID33045/start197863944，实际身份以PLAN原件为准，截止继续使用原96 archive启动+14400秒，完成后分析预算1200秒，无自动97/Direct34。原startup/review中gamma误写.9996的失败仍在，实际训练保持.9995；修复仅更换只读消费者，原训练/采样/guard未重启。本轮适配额外核对全部浮点常量不变、历史93索引、真实文件名和checkpoint轮次。

## 持续训练与尚未完成

99身份（原3learner、90sampler、5guard及此前已替换archive）连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}。完整96、真实新终端增长、全loss/图与全90条件比较及原94–96九组输入绑定/统计仍待。

原窗口94–96、5%/nearzero1/5000bootstrap/seed2026102861保持，原意向在94启动后首完整回合前登记。A94→95相对reward变化19.7689%已经违反原5%必要条件，不能移动窗口或抹去失败。4m回放足够完整96，96后I/A/V余量23488/20000/19000，完整97无法容纳，须另作容量决定，不覆盖旧回放。

原physics/MJB/Task/Strict/canonical48/filter/执行器限制/dt5e−5、actor49/critic52/clock/history/rawbit、原LR/reward/masks/terminal128/batch65536/UTD1及census/容量23和47标记不变。中断保全最新96 partial权重/Adam/RNG/replay/journals，另登记恢复，不回退95或重跑整轮96；MuJoCo物理state未保存。

Direct33原数值验收保持但冻结全30 Task/Strict0/0；旧28缺完整memory-invariance证明、恢复2已证，指定ESN仍缺，最终独立对比未完成。原90–92和之后全部失败均保留。
'''
# Use the recorded archive identity, not a guessed start tick.
plan=read(T/'PLAN.json');monitor=plan['original_monitor'];body=body.replace('PID33045/start197863944',f"PID{monitor['pid']}/start{monitor['proc_start_ticks']}")
(D/'REPORT_BODY.md').write_text(body)
print('Report generated from actual prefix/reference/observation/registration evidence')
