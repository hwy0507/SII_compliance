from pathlib import Path
import re,ast,json,hashlib,difflib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=B/'runtime/parameter74_followups_preparation_20261029_v1';D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
mapping={'00071':'00072','00072':'00073','00073':'00074','2154':'2184','2184':'2214','2214':'2244','71':'72','72':'73','73':'74'}
records=[]
for n in ['sii_prepare73_followups_20261028.py','sii_deploy73_labels_20261028.py','sii_deploy73_terminal_waiters_20261028.py','sii_audit73_prefix_20261028.py']:
 src=Path('/tmp')/n;dst=Path('/tmp')/n.replace('73','74');a=src.read_text();s=a
 protected={}
 for literal in ['68_70','68-70','71_73','71-73']:
  token='__HIST_'+chr(65+len(protected))+'__';protected[token]=literal;s=s.replace(literal,token)
 masked=s;s=re.sub(r'(?<!\d)('+'|'.join(mapping)+r')(?!\d)',lambda m:mapping[m.group()],s)
 inv={v:k for k,v in mapping.items()};assert re.sub(r'(?<!\d)('+'|'.join(inv)+r')(?!\d)',lambda m:inv[m.group()],s)==masked
 for k,v in protected.items():s=s.replace(k,v)
 ast.parse(s);assert not dst.exists();dst.write_text(s);(D/dst.name).write_text(s);(D/(dst.name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(src),tofile=str(dst))))
 records.append(dict(parent=str(src),parent_sha256=sha(src),path=str(dst),sha256=sha(dst),inverse_mapping_exact=True,protected_history=list(protected.values())))
(D/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=records,mapping=mapping,ast_passed=True,automatic_training=False),indent=2)+'\n');print('Prepared four drivers')
