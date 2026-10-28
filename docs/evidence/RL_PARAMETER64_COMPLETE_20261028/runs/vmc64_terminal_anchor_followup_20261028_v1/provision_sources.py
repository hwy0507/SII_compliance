from pathlib import Path
import re,ast,json,hashlib,difflib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
old=B/'runs/vmc63_terminal_anchor_followup_20261028_v1';out=B/'runs/vmc64_terminal_anchor_followup_20261028_v1';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def transform(s,mapping):
 parts=re.split(r'([a-f0-9]{64})',s)
 rx=re.compile(r'(?<!\d)('+ '|'.join(mapping)+r')(?!\d)')
 return ''.join(x if re.fullmatch(r'[a-f0-9]{64}',x) else rx.sub(lambda m:mapping[m[0]],x) for x in parts)
mp={'00062':'00063','00063':'00064','62':'63','63':'64','1884':'1914','1914':'1944'}
entries=[]
for name in ['capture_anchor.py','review_anchor.py','track.py','review_values.py','wait.py']:
 src=(old/name).read_text();s=transform(src,mp)
 assert transform(s,{v:k for k,v in mp.items()})==src
 if name=='capture_anchor.py':
  expected='067cb41496065e47d4f4105575c4c45286640fac449ea9718cc9709f820fd0e2'
  assert s.count(expected)==1;s=s.replace(expected,'46c3f151864b9e028e747ab5e7a9c84b695ae493f16674eb394e499d5b2b22a6')
 assert ('ky26288' in src)==('ky26288' in s)
 ast.parse(s);(out/name).write_text(s);(out/(name+'.diff')).write_text(''.join(difflib.unified_diff(src.splitlines(True),s.splitlines(True),fromfile=str(old/name),tofile=str(out/name))))
 entries.append(dict(name=name,old_sha256=sha(old/name),new_sha256=sha(out/name),inverse_cycle_mapping_exact=True))
write(out/'SOURCE_REVIEW.json',dict(time=time.time(),passed=True,files=entries,mapping=mp,opaque_hashes_protected=True,expected_parent_checkpoint_sha256='46c3f151864b9e028e747ab5e7a9c84b695ae493f16674eb394e499d5b2b22a6',physics_changes=False))
print(out)
