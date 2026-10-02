"""Original VMC and upstream non-RL anchors for a single native runtime."""
import argparse,json
from pathlib import Path
from optimize_tool_contact_20261002 import sha,write,now

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--protocol',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if a.output.exists():raise FileExistsError(a.output)
cases=json.loads(a.protocol.read_text())['cases']
rows=[dict(name='original_vmc_native',category='runtime_parity',config={})]
for c in cases:
    if c['method']=='zero_bridge':
        row=dict(name=c['id'],category='upstream_anchor',config=dict(channel_gain=[0]*7))
    elif c['method']=='parameter_fixed':
        row=dict(name=c['id'],category='upstream_anchor',controller=c['controller'])
    elif c['method']=='esn':
        assert len(c['checkpoint_hashes'])==1
        row=dict(name=c['id'],category='upstream_anchor',checkpoint=c['checkpoint'],checkpoint_sha256=next(iter(c['checkpoint_hashes'].values())))
    else:continue
    rows.append(row)
assert len(rows)==8, [(c['id'],c['method']) for c in cases]
write(a.output,dict(created_utc=now(),source_sha256=sha(Path(__file__)),upstream_protocol_sha256=sha(a.protocol),candidates=rows,
    purpose='Native runtime parity and upstream anchors; original VMC added as stronger model-based baseline. No heldout evaluation or teacher training.'))
