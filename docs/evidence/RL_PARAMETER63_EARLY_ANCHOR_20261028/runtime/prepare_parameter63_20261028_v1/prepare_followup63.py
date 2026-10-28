"""Prepare read-only63 audits and check-only64; never dispatch training."""
from pathlib import Path
import ast,difflib,hashlib,json,re,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def adapt(src,dest,names,mapping,hashmap=None):
    dest.mkdir(exist_ok=True);assert not (dest/'PLAN.json').exists();report={}
    for oldname,newname in names.items():
        s=(src/oldname).read_text();hashes={}
        def protect(m):
            key='OPAQUEHASH'+chr(65+len(hashes))+'TOKEN';hashes[key]=m.group(0);return key
        raw=re.sub(r'[0-9a-f]{64}|2026\d{4}',protect,s)
        pattern=re.compile(r'(?<!\d)(?:'+'|'.join(re.escape(x) for x in sorted(mapping,key=len,reverse=True))+r')(?!\d)') if mapping else None
        v=pattern.sub(lambda m:mapping[m.group(0)],raw) if pattern else raw
        invmap={v:k for k,v in mapping.items()};assert len(invmap)==len(mapping)
        inverse=re.compile(r'(?<!\d)(?:'+'|'.join(re.escape(x) for x in sorted(invmap,key=len,reverse=True))+r')(?!\d)').sub(lambda m:invmap[m.group(0)],v) if invmap else v
        assert inverse==raw,(oldname,'inverse')
        for k,h in hashes.items():v=v.replace(k,(hashmap or {}).get(h,h))
        ast.parse(v);p=dest/newname;p.write_text(v)
        (dest/(newname+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(src/oldname),tofile=str(p))))
        report[newname]=dict(parent=ref(src/oldname),current=ref(p),inverse_exact_excluding_explicit_hash_update=True)
    write(dest/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),mapping=mapping,explicit_hashmap=hashmap or {},files=report,ast_passed=True))
run=B/'runs/parameter_capacity_pool30_cycle63_20261026_v1';jobs=read(run/'LAUNCH.json')['jobs'];monitor=read(run/'MONITOR_LAUNCH.json')
for j in jobs+[monitor]:
    f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
assert not (run/'ARCHIVE_REVIEW_FINISHED.json').exists()
old=B/'runs/vmc62_terminal_anchor_followup_20261028_v1';out=B/'runs/vmc63_terminal_anchor_followup_20261028_v1'
mapping={'00061':'00062','00062':'00063','61':'62','62':'63','1854':'1884','1884':'1914'}
# Only these source files contain cycle/count literals; opaque checkpoint hashes are protected.
adapt(old,out,{x:x for x in ['capture_anchor.py','review_anchor.py','track.py','review_values.py','wait.py']},mapping,{'7a155281f6a99818b3b900c9f03117a98b804b680019709319e200acdcefbc59':'067cb41496065e47d4f4105575c4c45286640fac449ea9718cc9709f820fd0e2'})
assert (old/'wait.py').read_bytes()==(out/'wait.py').read_bytes()
# Exact dates and fixed focus indices must remain unchanged.
for name in ['capture_anchor.py','review_anchor.py','track.py','review_values.py']:
    assert set(re.findall(r'2026\d{4}',(old/name).read_text()))==set(re.findall(r'2026\d{4}',(out/name).read_text()))
    assert set(re.findall(r'ky\d+',(old/name).read_text()))==set(re.findall(r'ky\d+',(out/name).read_text()))
write(out/'PREPARATION_CONTEXT.json',dict(time=time.time(),registered_during63=True,parent_run=str(run),jobs=jobs,monitor=monitor,anchor_from_complete62=True,automatic_training=False))
print('Terminal63 sources prepared',out)
