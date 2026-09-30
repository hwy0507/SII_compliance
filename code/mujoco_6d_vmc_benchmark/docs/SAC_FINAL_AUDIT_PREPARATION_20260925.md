# SAC最终独立审计：工具已就绪，真实运行结果待验

`tools/audit_canonical48_sac_final_20260925.py`是新增离线工具，不属于已冻结的SAC训练source依赖。它只接受固定最终8192在线步、seed20260923、8092次SAC更新及四项最终评估的完整run；拒绝FAILED、缺seed、错预算、错产物hash或任何不一致，不套用PPO的384更新或`ppo_final.zip`命名。当前没有用此工具宣称任何尚未完成的SAC真实run通过。

核验包含原冻结transition auditor覆盖的全部8192 Gym/reward和float32转换、实际post-add每个replay槽与原journal/示范绑定、原buffer_actions到环境实际action的float32 unscale链、全部sample索引的可用前缀与demo计数、只由在线reset/step重算的逐步obs_rms、每个actual optimizer posthook事件的顺序，以及final ZIP内每个Adam state.step。初始模型与normalizer也按manifest hash核验，初始RMS必须为未拟合状态。

示范分支必须传原r2目录，接受固定manifest SHA `9f9092c03abcbf80cbf3e036552fbd9d6a214cdd21af8dded5eed1c402eb0a56`及其NPZ原字节；它有600条额外训练数据，总可用8792条。online-only只能有8192条，不能误传示范。两者都用标准均匀replay，不称RLPD。

所有非terminal next与原Gym float32精确核对；terminal next按当时RMS的normalize/unnormalize实际舍入链复算，但只能作为done=1、timeout=0的无效占位。若预算恰在terminal结束，DummyVecEnv仍会auto-reset，后面可有0transition空episode。工具用hash绑定的最终normalizer文件中真实`old_obs`重算这次reset的RMS，并单独标记该来源；它没有下一条action journal的独立见证。不会把末terminal占位冒充reset obs，不强制SAC恰为13×600+392。

实际sample返回张量在训练时由冻结代码逐值断言核验，但未另存张量字节。本工具独立检查归档replay槽、索引和当时online统计，并重构采样契约；不声称已独立重放未存的实际sample张量、TD target、loss或梯度数值。四项评估保留所有失败和安全早停，以实有步数/时长和末min(10,n)帧取当前阶段endpoint，不跨阶段平均，也不混入50µs子步主表。

待真实run归档checksum完成后，从项目工作目录运行：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-rl/bin/python \
  SII_compliance/code/mujoco_6d_vmc_benchmark/tools/audit_canonical48_sac_final_20260925.py \
  --run /absolute/path/to/completed/run \
  --snapshot /absolute/path/to/frozen/source \
  --output /absolute/path/to/fresh/report.json
```

demo-prefill额外传`--demo /absolute/path/to/train_only_action7_demo_20260924_r2`。工具生成同名JSON和MD，必须使用新输出路径；不启动MuJoCo、训练、物理评估或重新选择checkpoint。

验证：`tests/test_sac_final_audit_20260925.py`共14个测试通过（1.27s，0物理步）。使用真实SB3的合成105步/5更新产物核对全RMS、slots、sample统计和保存Adam步数；另实际执行合成104步/4更新，在最后terminal处结束，验证auto-reset空journal和保存/重载normalizer的末raw reset值。负例覆盖sample未来索引、demo污染统计、动作错位、假partial next、terminal错误bootstrap、optimizer错序、缺seed/错final更新。原冻结auditor接受合法空reset episode也有独立测试。

最终预算恰在terminal结束时，生成MD也明确标记末reset输入仅来自绑定normalizer.old_obs、没有后继Gym journal独立见证，与JSON字段一致。该追加仅改变报告文字，未更改审计数值逻辑或冻结训练源。

本工具SHA256：`aa20ec926a07ae73f598076a5f336f61fd98647b829e80becc46bc6cd4c09fcb`。测试文件SHA256：`84a55d9165b5e6b5259bead7d74121bd5d059d0057f7bdeeaa875d15cf3ea09a`。
