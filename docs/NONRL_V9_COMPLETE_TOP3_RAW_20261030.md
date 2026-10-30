# 原top3共同资格筛选的完整72回合归档

原top3筛选已经终态，独立FINAL_REVIEW核72完整case，其中10失败、10祖先复用，选中六组。新包实际纳入全部72条对应的raw，而不只保存指向旧run的路径；包含原18祖先的实际复用raw、完整物理子步/状态/动作/filter、MJB、执行与配置、每回合源码tar、全部失败资格和审计收据，以及候选训练metadata。

只读工具`tools/archive_v9_eligibility_prefix_20261030.py`从原终态execution单次字节快照取清单。1640 payload加execution/registration/manifest三成员，逐成员解包大小/SHA、源前后hash、checkpoint/qualification输入均已核验。包大小4249904348字节，SHA256 `664252fbe018b9ba7d75dffb85cf855e9edb5010d1b63648e1b9f478e6211f80`。

snapshot execution SHA `2dfc2ae9a6557a09cd55c15ca7b56a6080e0d54b0a5bd5f6c8a3250fbf5e5423`；registration SHA `bc2994e299dec10fba75a50c53f3bf4e5064a4c5d253fb91472b6b3ba1add933`；MANIFEST SHA `e0032062481bf5473d1a5f1fea2b2de97e208d4a82abaa61736124d15f5ffba4`。恢复映射见`docs/evidence/nonrl_v9_candidate_catalogue_20261029/TOP3_RAW_CASE_INDEX_20261030.json`。保留source_folder作为真实本机执行来源，不改写成服务器计算。

本机归档`sii-v9-top3-raw-archive-20261030.service` CPU6/Nice19/idle I/O/512MiB/swap0，2026-10-30本地01:23:55–01:27:49，自然exit0/CPU112.934秒。不启动第二模拟器，不删原始数据。

这是**原top3阶段完整72回合raw**，不包含后来full12新增回合、全部训练拟合产物或最终未见108。后两类不能借本包声称已备份/评测。最终九组选模与108仍待，Goal active。

已共享并核验：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v9_complete_top3_raw_20261030_v1/COMPLETED_PREFIX.tar.gz`。远端暂存与最终目录大小/hash一致；服务器仅存储/hash。对应本地输入与恢复映射收据已入Git。

另独立读取全部72条原始子步/状态时钟，72/72达到20/30/13s预期horizon，400000/600000/260000子步/5e-5均核验；这不消除10条原科学失败。rod20s额外核显式registration参数；ball30/corner13为和冻结最终执行器一致的独立审查时长，对应原recipe默认/源常量，不声称旧registration有不存在的显式duration字段。首次三次只读审查因旧schema字段差异拒绝、零物理/零输出，失败说明保留，修正入口后完整审查通过。

最新完整12独立prefix核78完整case、69祖先复用、7失败，确认七组已选：三个ESN、三个RNN、MLP seed01。ESN01 rank4九条全通过，当前MLP seed02继续；prefix不等于完整选择或最终测试。原top3失败10与此prefix失败7分母/包含候选范围不同，不混为失败消失。完整12首合格停止会复用已选组九条、不重放其未选候选，原top3所有失败仍由完整raw包保留。
