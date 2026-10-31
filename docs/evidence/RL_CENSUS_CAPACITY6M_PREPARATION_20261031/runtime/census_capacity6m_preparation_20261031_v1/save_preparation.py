from pathlib import Path
import ast, hashlib, json, shutil, socket, subprocess, tarfile, time
D=Path(__file__).resolve().parent; B=D.parents[1]
O=B/'runs/census_capacity6m_preparation_20261031_v1'; R=B/'repository/SII_compliance'
TAG='RL_CENSUS_CAPACITY6M_PREPARATION_20261031'; E=R/'docs/evidence'/TAG; A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,d):
    with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
review=read(O/'REVIEW.json');assert review['passed'] and not (O/'FAILURE.json').exists()
proc=read(O/'PROCESS.json')
for p in Path('/proc').glob('[0-9]*/cmdline'):
    try:raw=p.read_bytes()
    except OSError:continue
    assert str(D/'validate_capacity6m.py').encode() not in raw, 'Validator still running'
plan=read(O/'PLAN.json')
for p,h in plan['sources'].items():assert sha(Path(p))==h
for p in D.glob('*.py'):ast.parse(p.read_text())
start=read(O/'LIVE_START.json')
for e in start['identities']:
    s=Path('/proc',str(e['pid']),'stat').read_text().rsplit(')',1)[1].split()
    assert s[0]!='Z' and s[19]==e['start']
progress={m:read(B/'runs/parameter_census_cycle96_20261031_v1'/m/'train/PROGRESS.json') for m in review['methods']}
growth={m:progress[m]['steps']-start['progress'][m]['steps'] for m in progress};assert all(v>0 for v in growth.values())
samples=[json.loads(x) for x in Path('/tmp/sii_gpu_util_guard_20261031_recovery_v1/samples.jsonl').read_text().splitlines()]
samples=[x for x in samples if x['time']>=plan['time']];assert samples and time.time()-samples[-1]['time']<15
gpu=dict(samples=len(samples),minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_guard_included=True)
put(O/'LIVE_END.json',dict(time=time.time(),identities_checked_at_both_endpoints=len(start['identities']),elapsed_since_start=time.time()-start['time'],progress=progress,growth=growth,gpu=gpu,continuous_observation_claim=False))
(O/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples))
E.mkdir();A.mkdir();manifest=[]
for root in (D,O):
    for p in sorted(root.iterdir()):
        if not p.is_file() or p.suffix not in ('.py','.json','.jsonl','.diff'):continue
        rel=p.relative_to(B);target=E/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        assert target.read_bytes()==p.read_bytes()
        manifest.append(dict(relative=str(rel),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
    for p in sorted(E.rglob('*')):
        if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
    for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
    members=len(t.getmembers())
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=members,all_members_verified=True,backup_scope='Shared SSD small evidence; large checkpoints remain SSD; HDD pointer only, not full backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/f'{TAG}_SAVE.json',receipt)
arithmetic=read(O/'CAPACITY_ARITHMETIC.json')
entry=f'''## 2026-10-31 — 600万回放容量准备通过；原第96轮继续

- [交接](docs/{TAG}.md)。现4m不能容纳完整97，独立6m候选仅准备；真实完整95三路全部回放/历史双容量及架构标记/RNG精确、CPU census终端与1/32/256/65536采样一致，完整learner digest和原checkpoint hash保持。
- 合成3,999,998→4,000,002保留全部旧行/缓存/终端新增4、恢复采样及RNG精确；最后6m槽位写入通过，满容量写入拒绝且完整状态不变；{len(review['negative_guards'])}损坏状态拒绝。无physics/optimizer更新，非GPU/full96接入验证，无97派发。原wrapper默认4m须显式传6m。
- 原101身份在两端检查一致，steps增长{growth}（非连续观察）；GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，guard继续。原96三训练/修正版archive/两个消费者继续；完整96、94–96统计及收敛待，A原19.7689%必要条件失败保持，Direct原结论与指定ESN缺失保持，Goal active。
- SSD小证据{members}成员/SHA{receipt['sha256'][:8]}，HDD仅指针；main e1f84ca1/baseline f6e8f8c2已query/fetch/read。部署需完整96审查、精确全state/GPU预检及独立有限97登记。

'''
body=f'''# 600万回放容量准备（2026-10-31，尚未部署）

Goal active。前一轮属于verified wait：实际检查原训练/等待器/guard仍活跃；本轮完成新的容量候选及真实回放兼容性验证。原第96轮继续，未重启或覆盖其运行时。

主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮沿用sii-research-sync；开工真实查询并fetch/read main `e1f84ca15d10e3d28b4acadf61b335976a18d631` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无子agent。

## 容量与实现

完整96预计I/A/V为3976512/3980000/3981000条，现4m仅余23488/20000/19000，完整97最多新增41250时超限。候选6m保持append-only、拒绝覆盖，保留历史2m/4m容量标记，另加replay_capacity_third。只能从digest绑定的完整4m回放迁入，之后恢复要求三个标记一致。扩容超过4m后与覆盖式ring不同，不声称算法等价或性能提升；每个后续科学阶段仍需有限登记。

原52维violation_replay_class默认capacity4m，因此必须显式传capacity6000000；本次真实三路验证采用此路径。当前正式driver96与协议仍保持4m，候选源码 `{D}/parameter_replay_capacity6m.py` 未接入正式训练。

按实际5/7/7动作维数，三路CPU回放加设备镜像预计增加{arithmetic['extra_three_methods_cpu_and_device_bytes']}字节（约5.24GiB）。准备前容器可用{plan['free_container_bytes']/1024**3:.2f}GiB，swap{plan['swap_bytes']}字节。这里只是存储估算，正式接入还需GPU运行检查。

## 实际验证

`{O}/REVIEW.json`：三份真实完整95 checkpoint逐hash加载；全部保留行、RNG、原历史容量与52维架构标记精确。CPU CensusCache重建终端2845/2844/2844及全部32 mask分层计数准确，采样1/32/256/65536与原生回放的值和采样RNG一致，load后cache重建也通过。完整learner digest和checkpoint文件hash前后不变。没有创建或更新learner；未声称已完成6m learner/GPU原生更新检查。

独立合成3,999,998→4,000,002检验全部旧prefix保留、边界两步与原4m写入相同、全部cache字段一致、新增4个终端、恢复后65536样本及RNG一致。填充全部6m存储后写入最后有效槽位，额外add被拒且全部数据/size/cursor/RNG digest不变。{len(review['negative_guards'])}个缺失/错误标记、回卷、容量、size、schema、RNG、dtype、NaN、mask/done与shape异常在修改状态前被拒。

验证CPU54/nice15/900秒上限，实际原生进程已结束；零physics、零optimizer更新、未保存辅助权重。原实现依赖及新源码hash锁在PLAN.json，原active96锁定文件复核无变化。容量算术与未来接入要求另见CAPACITY_ARITHMETIC.json、DEPLOYMENT_REQUIREMENTS.json。

## 原任务与下一步

原101身份在准备中的起止两端仍为同一PID/start，steps增长{growth}，并非全程逐样本身份观察。末进度{ {m:v['steps'] for m,v in progress.items()} }。原3learner、90sampler、修正版archive、固定8533终端与全90比较消费者继续。GPU保存窗口{gpu['samples']}样本最低{gpu['minimum']}%、低于50次数{gpu['below50']}；独立guard仍继续，含synthetic占用，不等于科学吞吐或每瞬时保证。

先验收完整96的回放/真实终端增长/原loss及图、全90与固定终端比较，再完成原94–96九组绑定和统计；A94→95的19.7689%必要条件失败及全部历史退化保持。然后依据完整96结果登记是否继续有限97：绑定真实96全部learner/Adam/RNG/replay与digest、CPU/GPU cache及原生65536重复更新恢复，接通三容量标记的checkpoint/startup/archive/fullreview，之后才允许部署。真实跨4m保留及新reward/action/history/bit检查仍待；本次95准备不是完整96接入证明。无自动97/98或Direct34。

Direct33原数值验收及冻结全30 Task/Strict0/0保持，旧28 memory-invariance缺口及恢复2已证保持；指定ESN仍缺，最终独立对比/联合收敛未完成。中断保全最新96 partial，不回退95；MuJoCo物理state未保存。

## 保存

小证据包 `{archive}`，{members}成员，SHA256 `{receipt['sha256']}`，逐成员字节核验通过。Git小证据 `docs/evidence/{TAG}`。大checkpoint/replay/journals仅共享SSD；HDD配额满只原地更新254字节LATEST，不是HDD/arm1完整备份。实际发布核验收据将在 `{A}/PUBLICATION.json`。
'''
(R/'docs'/f'{TAG}.md').write_text(body)
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
    p=R/name;old=p.read_text();add=entry.replace('docs/'+TAG,TAG) if name.startswith('docs/') else entry
    if name=='AGENTS.md':
        first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
    else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
data=(str(R/'docs'/f'{TAG}.md')+'\nGoal active; SSD assets.\n').encode();size=pointer.stat().st_size;assert len(data)<=size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data)
print(json.dumps(dict(passed=True,members=members,growth=growth,gpu=gpu,archive_sha256=receipt['sha256'])))
