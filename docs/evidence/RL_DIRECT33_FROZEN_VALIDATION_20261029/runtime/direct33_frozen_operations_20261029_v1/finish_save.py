"""Finish the unchanged saved snapshot after creating the absent repository tools directory."""
from pathlib import Path
import json,hashlib,time,ast
D=Path(__file__).parent
source=(D/'save.py').read_text();namespace={'__file__':str(D/'save.py')}
exec(compile(source.split('obs=read(',1)[0],str(D/'save.py'),'exec'),namespace)
R=namespace['R'];B=namespace['B'];TAG=namespace['TAG'];E=R/'docs/evidence'/TAG
assert E.exists() and not (B/'repository'/TAG).exists()
(R/'tools').mkdir(exist_ok=False)
failure=dict(time=time.time(),error='FileNotFoundError: repository tools directory absent at save.py line46',source_sha256=hashlib.sha256((D/'save.py').read_bytes()).hexdigest(),evidence_snapshot_already_copied=True,archive_not_created=True,science_unchanged=True)
(D/'SAVE_INITIAL_FAILURE.json').write_text(json.dumps(failure,indent=2)+'\n')
r=dict(passed=True,time=time.time(),repair='Create repository tools directory; continue packaging from existing immutable snapshot. No training/evaluation restart or snapshot resampling.',original_source_sha256=failure['source_sha256'],new_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(D/'SAVE_RECOVERY_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n')
m=json.loads((E/'MANIFEST.json').read_text())
for p in [Path(__file__),D/'SAVE_INITIAL_FAILURE.json',D/'SAVE_RECOVERY_REVIEW.json']:
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;assert not q.exists();q.write_bytes(data);m['files'].append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(E/'MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
namespace.update(E=E,manifest=m['files'],snap=json.loads((D/'SAVE_SNAPSHOT.json').read_text()),obs=json.loads((D/'OBSERVATION_FINISHED.json').read_text()),rows=[json.loads(l) for l in (D/'GUARD_SAMPLES.jsonl').read_text().splitlines()])
tail=source[source.index("for n in ['evaluate_serl33_frozen_20261029.py','review_serl33_frozen_matrix_20261029.py']:"):]
exec(compile(tail,str(D/'save.py')+'[packaging continuation]','exec'),namespace)
