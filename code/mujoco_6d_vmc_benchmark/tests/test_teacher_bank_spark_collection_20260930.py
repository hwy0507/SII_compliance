"""Supplemental driver rejects premature launch and miscounted paired data."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import teacher_bank_spark_collection_20260930 as driver


def test_three_disjoint_worker_shards_preserve_all_three_categories():
    fixtures=[dict(id=f'{category}_train_{i:04d}',category=category,split='train')
              for category in driver.CATEGORIES for i in range(1000)]
    shards=[{f['id'] for f in driver.shard_fixtures(fixtures,w)} for w in range(3)]
    assert len(set.union(*shards))==300
    assert not any(shards[i]&shards[j] for i in range(3) for j in range(i+1,3))
    assert all(int(identity.rsplit('_',1)[1])>=900 for shard in shards for identity in shard)


def test_unlocked_review_and_implicit_dynamic_launch_are_rejected(tmp_path):
    path=tmp_path/'review.json'
    driver.write(path,dict(snapshot_consistency=dict(stable=True),closeout=dict(bank_certified_locked=False)))
    with pytest.raises(RuntimeError,match='Uncertified search'):
        driver.verify_locked_review(path,driver.sha(path),tmp_path)
    with pytest.raises(RuntimeError,match='explicit --start'):
        driver.run_worker(tmp_path,0)


def test_locked_review_pins_exact_selected_bank_bytes(tmp_path):
    bank={};groups={}
    for category in driver.CATEGORIES:
        for method in driver.METHODS:
            key=f'{category}/{method}'
            chosen=dict(index=0,x=[.5]*5,anchor_feasible=False)
            bank[key]=[chosen]
            groups[key]=dict(all_budget_candidates_verified=True,
                recorded_selection_matches_independent_rank=True,candidates=[{} for _ in range(6)],
                recorded_selection=chosen,best_complete_candidate=dict(index=0,x=chosen['x']),
                selected_controller_config={'stiffness':300.})
    driver.write(tmp_path/'teacher_bank.json',bank)
    driver.write(tmp_path/'plan.json',dict(search_candidates_per_category=6))
    driver.write(tmp_path/'fixtures.json',[])
    review=dict(snapshot_consistency=dict(stable=True),closeout=dict(bank_certified_locked=True,
        all_candidate_summaries_and_rank_verified=True,source_manifest_verified=True,reconstructed_groups=groups),
        metadata_sha256={name:driver.sha(tmp_path/name) for name in ('teacher_bank.json','plan.json','fixtures.json')})
    path=tmp_path/'review.json';driver.write(path,review)
    driver.verify_locked_review(path,driver.sha(path),tmp_path)
    bank['passive_corner/vmc'][0]['x'][0]=.9
    driver.write(tmp_path/'teacher_bank.json',bank)
    with pytest.raises(RuntimeError,match='Pinned evidence changed'):
        driver.verify_locked_review(path,driver.sha(path),tmp_path)


def test_panda_only_manifest_is_not_enough_for_actual_fr3_robot(tmp_path):
    manifest=tmp_path/'manifest.json'
    driver.write(manifest,{'franka_emika_panda/panda.xml':'abc'})
    with pytest.raises(RuntimeError,match='FR3 plus Panda'):
        driver.verify_assets(tmp_path,manifest)


def test_cross_architecture_mjb_byte_difference_blocks_preparation(tmp_path,monkeypatch):
    monkeypatch.setattr(driver.platform,'machine',lambda:'aarch64')
    path=tmp_path/'static.json'
    checks=[dict(fixture_id=f'{category}_train_{index:04d}',reference_mjb_sha256='same',target_mjb_sha256='same')
            for category in driver.CATEGORIES for index in (0,337,671)]
    value=dict(compatible_for_collection=True,no_dynamic_steps=True,target_architecture='aarch64',
               parent_plan_sha256='plan',asset_manifest_sha256='assets',model_checks=checks)
    driver.write(path,value)
    driver.verify_static_review(path,driver.sha(path),'plan','assets')
    checks[0]['target_mjb_sha256']='different'
    driver.write(path,value)
    with pytest.raises(RuntimeError,match='compiled model differs'):
        driver.verify_static_review(path,driver.sha(path),'plan','assets')


def test_duplicate_fixture_method_is_counted_once_without_cherry_picking(tmp_path):
    root,parent=tmp_path/'supplemental',tmp_path/'parent'
    def add(folder,method,eligible):
        driver.write(folder/'execution.json',dict(status='completed',returncode=0))
        driver.write(folder/'audit.json',dict(fixture_id='f1',method=method,eligible=eligible,
            model_sha256='model',rmse_m=.02,peak_torque_nm=30.,peak_speed_mps=.1))
    add(parent/'collection/f1/vmc','vmc',False)
    add(root/'workers/0/f1/vmc','vmc',True)
    add(root/'workers/0/f1/admittance','admittance',True)
    add(root/'workers/0/f1/impedance','impedance',True)
    result=driver.reconcile(root,parent)
    assert result['unique_fixture_method_count']==3
    assert result['unique_fixture_count']==result['complete_paired_fixture_count']==1
    assert len(result['cross_host_duplicates'])==1
    assert result['cross_host_duplicates'][0]['first']['eligible'] is False


def test_mixed_host_partial_runs_do_not_become_a_complete_paired_fixture(tmp_path):
    root,parent=tmp_path/'supplemental',tmp_path/'parent'
    for host,methods in ((parent/'collection/f1',('vmc',)),(root/'workers/0/f1',('admittance','impedance'))):
        for method in methods:
            driver.write(host/method/'execution.json',dict(status='completed',returncode=0))
            driver.write(host/method/'audit.json',dict(fixture_id='f1',method=method,eligible=True,
                model_sha256='same',rmse_m=.02,peak_torque_nm=30.,peak_speed_mps=.1))
    result=driver.reconcile(root,parent)
    assert result['unique_fixture_method_count']==3
    assert result['complete_paired_fixture_count']==0
    assert result['incomplete_same_host_pairing']==['f1']


def test_dynamic_worker_requires_real_cgroup_memory_and_cpu_bounds(tmp_path):
    proc=tmp_path/'self_cgroup';proc.write_text('0::/worker\n')
    cgroup=tmp_path/'cgroup/worker';cgroup.mkdir(parents=True)
    (cgroup/'memory.max').write_text(str(3*1024**3))
    (cgroup/'cpu.max').write_text('100000 100000')
    assert driver.worker_resource_limits(proc,tmp_path/'cgroup')['memory_max_bytes']==3*1024**3
    (cgroup/'memory.max').write_text('max')
    with pytest.raises(RuntimeError,match='MemoryMax'):
        driver.worker_resource_limits(proc,tmp_path/'cgroup')
