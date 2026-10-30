from pathlib import Path
import re,ast,difflib,hashlib,json,time
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;O=B/'runtime/recovery85_full_review_20261030_v1';refs=[]
for before,after in [('summarize.py','summarize.py'),('new_terminal_cases.py','new_terminal_cases.py'),('availability85.py','availability86.py')]:
 old=(O/before).read_text()
 if before=='summarize.py':
  new=re.sub(r'(recovery|cycle)(85|86)',lambda m:m[1]+{'85':'86','86':'87'}[m[2]],old).replace('COMPLETE84_85','COMPLETE85_86')
 else:new=re.sub('2514|2544|85',lambda m:{'2514':'2544','2544':'2574','85':'86'}[m[0]],old)
 ast.parse(new);(D/after).write_text(new);(D/(after+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(O/before),tofile=str(D/after))))
 refs.append(dict(parent=str(O/before),parent_sha256=hashlib.sha256(old.encode()).hexdigest(),path=str(D/after),sha256=hashlib.sha256(new.encode()).hexdigest()))
with (D/'SOURCE_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),sources=refs,automatic_training=False),f,indent=2);f.write('\n')
print('Full86 result/terminal/opportunity summaries prepared')
