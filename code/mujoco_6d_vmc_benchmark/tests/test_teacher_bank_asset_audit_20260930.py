import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import teacher_bank_asset_audit_20260930 as assets
import teacher_bank_campaign_20260930 as campaign


def robot_assets(tmp_path):
    root=tmp_path/'assets'
    for name in assets.ROBOT_ROOTS:
        folder=root/name/'assets'
        folder.mkdir(parents=True)
        (folder/'mesh.obj').write_text('test asset content')
    for name in assets.ROBOT_MODELS:
        (root/name).write_text('<mujoco><compiler meshdir="assets"/><asset><mesh file="mesh.obj"/></asset></mujoco>')
    return root


def test_complete_manifest_covers_fr3_generation_xml_and_panda_hand(tmp_path):
    root=robot_assets(tmp_path)
    manifest=assets.collect_robot_assets(root)
    assert set(assets.ROBOT_MODELS)<=set(manifest)
    assert {'franka_fr3/assets/mesh.obj','franka_emika_panda/assets/mesh.obj'}<=set(manifest)
    run=tmp_path/'run'
    (run/'source_inputs').mkdir(parents=True)
    (run/'source_inputs/robot_asset_manifest.json').write_text(json.dumps(manifest))
    verified=campaign.verify_assets(run,root)
    assert verified['complete_fr3_and_panda_coverage']


def test_prepare_missing_real_fr3_model_fails_before_creating_campaign(tmp_path,monkeypatch):
    root=robot_assets(tmp_path)
    (root/'franka_fr3/fr3.xml').unlink()
    monkeypatch.setattr(campaign,'ASSETS',root)
    destination=tmp_path/'new_run'
    with pytest.raises(FileNotFoundError,match='required robot model'):
        campaign.prepare(destination)
    assert not destination.exists()


@pytest.mark.parametrize('name',assets.ROBOT_ROOTS)
def test_missing_referenced_mesh_is_rejected(tmp_path,name):
    root=robot_assets(tmp_path)
    (root/name/'assets/mesh.obj').unlink()
    with pytest.raises(FileNotFoundError,match='missing mesh asset'):
        assets.collect_robot_assets(root)


def test_legacy_panda_manifest_is_explicitly_incomplete(tmp_path):
    root=robot_assets(tmp_path)
    complete=assets.collect_robot_assets(root)
    old={k:v for k,v in complete.items() if k.startswith('franka_emika_panda/')}
    run=tmp_path/'run'
    (run/'source_inputs').mkdir(parents=True)
    path=run/'source_inputs/robot_asset_manifest.json'
    path.write_text(json.dumps(old))
    before=path.read_bytes()
    checked=campaign.verify_assets(run,root)
    assert checked['files_verified']==len(old)
    assert not checked['complete_fr3_and_panda_coverage']
    assert checked['covered_robot_roots']==['franka_emika_panda']
    assert path.read_bytes()==before


def test_saved_xml_resolves_fr3_meshdir_and_absolute_panda_mesh(tmp_path):
    root=robot_assets(tmp_path)
    xml=tmp_path/'rollout.xml'
    panda=root/'franka_emika_panda/assets/mesh.obj'
    fr3=root/'franka_fr3/assets'
    xml.write_text(f'<mujoco><compiler meshdir="{fr3}"/><asset>'
                  f'<mesh name="arm" file="mesh.obj"/><mesh name="hand" file="{panda}"/></asset></mujoco>')
    resolved=assets.referenced_files(xml)
    assert [r['resolved'] for r in resolved]==[str(fr3/'mesh.obj'),str(panda)]
    assert all(r['sha256']==assets.sha(r['resolved']) for r in resolved)
