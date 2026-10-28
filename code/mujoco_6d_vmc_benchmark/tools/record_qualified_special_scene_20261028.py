"""Copy immutable small evidence and snapshot collection progress for handoff."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):
            h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    out=p.parse_args().output.resolve();out.mkdir(parents=True,exist_ok=False)
    runs=[f'special_scene_rod_dev{i}_20261028' for i in (17,18,19,20)]
    runs+=['special_scene_ball_dev01_20261028','special_scene_shared_dev04_20261028']
    runs += [f'special_scene_corner_dev{i:02d}_20261028' for i in (1,2,3,5)]
    files={};rows=[]
    def copy(path):
        relative=path.relative_to(ROOT/'outputs')
        target=out/'receipts'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
        files[str(relative)]=dict(bytes=target.stat().st_size,sha256=sha(target))
    names={'execution.json','legacy.json','teacher.json','recipe.json','SOURCE_HASHES.json',
           'INDEPENDENT_AUDIT.json','ROD_YIELD_REJOIN_AUDIT_V3.json',
           'DEMONSTRATION_QUALIFICATION.json','manifest.json'}
    for name in runs:
        folder=ROOT/'outputs'/name
        for path in folder.rglob('*.json'):
            if path.name in names:
                copy(path)
        for path in folder.glob('*/execution.json'):
            e=json.loads(path.read_text());q=path.parent/'DEMONSTRATION_QUALIFICATION.json'
            rows.append(dict(run=name,scene=e['scene'],status=e['status'],
                             qualification=json.loads(q.read_text())['status'] if q.exists() else 'not_qualified',
                             error=e.get('error'),teacher_config_sha256=e['teacher_config_sha256']))
    collection=ROOT/'outputs/special_scene_vmc_collection_20261028_v3'
    copy(collection/'COLLECTION_PLAN.json')
    progress=json.loads((collection/'COLLECTION_PROGRESS.json').read_text())
    for entry in progress['episodes']:
        for path in (collection/entry['id']/entry['scene']).glob('*.json'):
            if path.name in names:
                copy(path)
    archive=ROOT/'outputs/special_scene_teacher_qualified_20261028_v1.tar.gz'
    result=dict(schema='sii-three-special-scenes-qualified-development-handoff-v1',
                created_utc=datetime.now(timezone.utc).isoformat(),development=rows,
                collection_progress_snapshot=progress,
                archive=dict(filename=archive.name,bytes=archive.stat().st_size,sha256=sha(archive),
                             content='All ten listed completed development roots, including failures/raw/MJB/source/media, plus prospective plan. Live collection raw excluded.'),
                files=files,limitations='Three development demonstrations qualified with same teacher; not a qualified complete dataset, not trained students, not final108. Raw substep arithmetic is not independent integration replay.')
    (out/'INDEX.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(output=str(out),files=len(files),archive=result['archive'],collection=progress)))


if __name__=='__main__':main()
