from pathlib import Path
import json,datetime,os
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY86_COMPLETE87_RUNNING_20261030';read=lambda p:json.loads(p.read_text())
s=read(D/'SAVE_SNAPSHOT.json');a=read(R/'docs'/(TAG+'_SAVE.json'));g=s['guard'];steps={m:r['steps'] for m,r in s['cycle87'].items()};obs=read(D/'OBSERVATION87_FINISHED.json');watch=read(D/'WATCH_FINISHED.json');full=read(B/'runs/parameter_partial75_recovery_cycle86_review_20261029_v1/REVIEW.json');loss=read(B/'runs/parameter_recovery86_loss_20261029_v1/REVIEW.json');fixed=read(B/'runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1/REVIEW.json');cohort=read(D/'PRIOR85_COHORT86_REVIEW.json');startup=read(B/'runs/parameter_partial75_recovery_cycle87_20261029_v1/startup/REVIEW.json');launch=read(B/'runs/parameter_partial75_recovery_cycle87_20261029_v1/LAUNCH.json');fp={m:(v['completed_conditions'],v['condition'],v['actions']) for m,v in s['frozen82'].items() if m not in s['frozen82_finished']};stamp=datetime.datetime.fromtimestamp(s['time'],datetime.timezone.utc).isoformat();reason=(B/'runtime/recovery87_completion_preparation_20261030_v1/CONTINUATION_REASON.txt').read_text()
rows=[]
for m,x in full['methods'].items():
 q=loss['methods'][m]['loss']['agent_train/q_loss'];act=loss['methods'][m]['loss']['agent_train/actor_loss'];rows.append(f"|{m}|{x['steps']}|{x['reward_mean']:.9f}|{x['task']}/{x['strict']}|{q['first1000']:.6f}→{q['last1000']:.6f}|{q['maximum']:.6f}|{act['first1000']:.6f}→{act['last1000']:.6f}|")
table='\n'.join(rows);critics='\n'.join(f"|{m}|{v['critic']}|{v['sse84']:.6f}|{v['sse85']:.6f}|{v['sse86']:.6f}|" for m,x in fixed['methods'].items() for v in x['critics']);cps='\n'.join(f"- {m}: `{v['checkpoint_sha256']}`。" for m,v in full['methods'].items())
text=f'''# 完整第86轮已审；有限第87轮实际续训

{stamp}，Goal active。完整86三路全replay/reward/health/loss/186保存标签/两终端/固定2514三checkpoint和5张实际图审查通过；reward稳定与loss健康尚未共同成立。明确登记一个有限87周期已实际运行，PID `{ {j['controller']:j['pid'] for j in launch['jobs']} }`，start573936642；保存steps `{steps}`。冻结82及原85—87统计继续，不自动88，无Direct34。

主机 `{s['host']}`，解释器 `{B}/env/bin/python`；大checkpoint/replay/raw/runtime在共享SSD `{B}`。实际ls-remote、fetch/read main `f3a48112e015997eb486d9f0c9ae2026d0219ad0` 和baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，保留其他主机非RL成果，无子agent。按仓库sii-research-sync工作，发布以SSD本包PUBLICATION.json的成功push与之后实际远端核验为准。

|第86轮方法|steps|reward均值|Task/Strict，各30|critic首→末1000|critic最大|actor首→末1000|
|---|---:|---:|---|---|---:|---|
{table}

全部各30个完整55秒回合、41250新增、无abort，旧replay所有字段精确保持、新reward重建误差0，network/optimizer有限。loss独立保存算术和完整health均通过，5张实际图已查看。A/V完整后段尖峰减少且均值下降，I仍多次有限尖峰；actor I先轻微上拱再下降、A小幅波动、V下降后趋平。entropy接近原I−5/A,V−7，alpha有限正值，nextQ尺度未崩溃。单轮改善不是健康稳定证明，不追加事后尖峰阈值。

完整85→86条件变化：阻抗short0600 Task保持真、Strict真→假，外穿透0.185890→0.221793mm。导纳short0600 Strict恢复0.211649→0.188750mm；long0200 Task恢复，short0900 Task退化，总Task仍15。VMC short0000 Strict恢复0.219979→0.179105mm。186保存rollout独立标签审计通过，条件交换和失败均保留。原0.2mm门不改。

Q超过当前固定alpha全局上界采样比例I0/A0.000390625/V0.001074219，仅诊断；终端mask内MAE分别0.347034/0.214563/0.172202，mask外3.433353/2.377991/1.910886，mask外不参与对应critic拟合。所有诊断checkpoint哈希与完整86绑定，网络/RNG保持。

固定同一2514输入/actions/rewards/masks与全部5critic的原前瞻84/85/86审查按PLAN SHA `2f7c719eb64c36ce20b8135ca5d18748c0683bb4bf45d6e44a2f953ce44e5041` 完成，全部5028保存行/三checkpoint的独立标量复核通过，六栏新图实际查看。VMC总SSE9046.060766→3556.824879→1158.553497；导纳1283.626104→3932.822648→2110.926268。

|方法|critic|84 SSE|85 SSE|86 SSE|
|---|---:|---:|---:|---:|
{critics}

VMC从85到86全部5critic改善，但c2仍高于84；导纳c0—3改善，c4由68.649647恶化至697.599873，总误差仍高于84。VMC旧84short0600 index3478427 SSE2624.382648→328.452727→64.701597；相邻正reward long0400 index3478443 765.100376→733.931484→0.860001，critic1从−3.207513改为23.042877；旧short0100 0.804835→122.004646→4.669285。全部30新增84 cohort均保留。当前原输入可以继续改善这些样本，不能由84局部负梯度余弦断言必然无法拟合，也不据此重建历史Adam因果。

完整2544旧终端群体V SSE9991.012435→1172.629322、A8131.029796→2606.867028；旧focus仍有恶化：V index2423133 5.912702→56.484323、2423122 7.332240→21.173519；A index2752093 41.328919→56.984262。两终端保存值逐标量复核、原观测/actions/rewards/masks和网络/RNG不变证明通过。

新增 `PRIOR85_COHORT86_REVIEW.json` 将全部30新增85终端按原episode global index匹配到同一2544群体：V总6434.187555→14.075826，A4198.207147→495.940761；另独立与full2544减fixed2514总量一致。V上轮short0000失败行6149.693743→4.540179，A short0600失败行3688.808975→8.350587。所有60行和改善/退化保留，不只选择失败例，没有新forward或physics。

本轮新30终端贡献V0.001348028，最大long0500占29.3085%；A0.015094606，short0900任务失败占59.0944%，long0500占22.0499%。全部90终端更新机会已按真实append→steps++→update和连续41250日志核对，实际minibatch包含次数未知，不能把机会数当采样次数或充分拟合证明。上一交接10,577,448旧replay历史重建继续有效，只是数据可行性证据，没有历史特征模型修订。

本次有限87科学决定原文：

{reason}

87科学trainer同86，五metadata扩展可逆，19协议+8边界负例与实际缺前置拒绝保持。全learner/optimizer/replay/RNG/next65536准确恢复通过；实际startup检查新增步数 `{ {m:v['added_steps'] for m,v in startup['methods'].items()} }`，30sampler、MJB、旧replay/历史markers、新动作/clock/reward0误差通过。87每方法最多41250新transition、30条件×最多55s，4m append-only/23与47markers/terminal128/batch65536/UTD1/LR/reward/masks/physics/filter/gates不变。

87 archive2291682/start573936642、loss2291685/start573936646，startup及全部labels/两终端后续已部署。原完整86 anchor2574→预期87共2604，锚点保存复核通过。具体新等待PID/start读各LAUNCH.json，避免猜测或重复派发。原86完成观察{watch['samples']}样本/{watch['elapsed_s']:.3f}秒，29身份核验；新87观察{obs['samples']}样本/{obs['elapsed_s']:.3f}秒、{obs['identities']}身份保持live或原成功结束、steps单调且保存逐行回读。观察完成不重启科学。

原85—87 PLAN SHA `6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e`、seed2026102858、5000bootstrap、nearzero1、5%、anchor55、原4小时deadline保持。现完整85/86、87运行。A/V的85→86相邻变化已超过5%，后续87不能使该窗口全部相邻检查通过；完整窗口与bootstrap尚在等待，不能用部分数据冒充最终统计。原76—78/79—81/82—84、partial75/原74—76不可判和79安全中止全部保留。

冻结82的阻抗已完成30条件/41250动作/3300万子步，Task18/Strict17；FINISHED证明full learner与full replay保持不变，initial/final learner digest均19c27c3792cd06067f042fd455d92306b82634f42c2fd6c6f8255a8c8ffffd1d，0optimizer updates，原evaluator正常退出，不重启。该方法PROGRESS仍停29条件是旧进度快照，最终状态以FINISHED为准。剩余方法进度(已完成条件,在途条件,动作) `{fp}`；rootreview/55→82比较/全保存raw审计继续，完整90及其余方法最终全state证明/实际图/完整比较仍未齐。单动作seed2026102638和开发训练条件，不证明泛化或指定ESN最终排名。Direct33数值阶段接受但冻结30 Task/Strict0/0，无Direct34；中断28缺最终内存不变证明仍披露，指定ESN仍缺且不替换其他主机模型。

完整86checkpoint位于 `runs/parameter_partial75_recovery_cycle86_archive_20261029_v1/<method>/cycle_00086.pt`：

{cps}

GPU原v7 supervisor和四worker继续；{g['samples']}保存样本最低{g['minimum']}%、低于50次数{g['below50']}，末值{g['last']}%。科学任务结束仍合成保载，合成占用不算科学吞吐；历史v7预热0和v6低谷保留，采样间瞬时不能保证，非重启自启服务。

共享SSD小证据 `{a['archive']}`，{a['members']}成员/{a['bytes']}字节，SHA256 `{a['sha256']}`。逐tar成员原字节/AST核验，Git index/commit blob另核。大checkpoint/replay/raw/history sidecar仍原共享SSD，非HDD/arm1全备份，HDD LATEST原位保持254字节。归档中的运行日志为快照。

后续先核原87/冻结82/85—87/labels与终端/guard身份及FAILURE/FINISHED。完整87后审原完整窗口与bootstrap、全部loss/health/标签/旧新样本，判断是否需要独立登记训练修订，不自动88；不能只因87结束、部分loss下降或GPU有占用标记Goal完成。
'''
p=R/'docs'/(TAG+'.md');assert not p.exists();p.write_text(text)
entry=f'''## 2026-10-30 — 完整86与固定2514已审；有限87实际续训

- [交接](docs/{TAG}.md)。86各30×55/41250/noabort，旧replay/reward0误差/full loss/health/186标签/两终端/5实际图通过；reward−2.408941/−6.690040/−2.831542、Task/Strict18/17、15/15、17/17。A/V loss下降与旧失败拟合改善，I新Strict失败，未收敛。
- 固定2514 V3556.825→1158.553全5改善，A3932.823→2110.926但c4退化；新85群体V6434.188→14.076/A4198.207→495.941。明确有限87决定/全state准确恢复/actual startup/{obs['elapsed_s']:.1f}秒29身份观察通过，steps{steps}，全后续部署，无自动88。原85—87 A/V相邻已超5%，不靠87追认通过；Goal active。
- GPU{g['samples']}样本min{g['minimum']}%、低于50{g['below50']}，科学完成仍保载；SSD{a['members']}成员/SHA{a['sha256'][:8]}核验，非HDD/arm1全备份。mainf3a48112/baselinef6e8f8c实际fetch/read，发布见收据，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';line,rest=p.read_text().split('\n',1);p.write_text(line+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254
if len(data)<254:data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254;print('Docs and254byte pointer saved')
