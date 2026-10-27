from pathlib import Path
import json,time,os
root=Path(__file__).parent
os.sched_setaffinity(0,{54})
plan=json.loads((root/'REGISTRATION.json').read_text());rows=plan['processes'];deadline=time.monotonic()+1200
while any('first_missing' not in row for row in rows):
 assert time.monotonic()<deadline,'Finite exit observation expired'
 for row in rows:
  if 'first_missing' in row:continue
  p=Path(f"/proc/{row['pid']}/stat")
  try:
   stat=p.read_text().split();assert stat[21]==row['start_ticks'],'PID reused during exit observation'
   if stat[2]=='Z':row['first_missing']=time.time();row['terminal_state']='zombie'
   else:row['last_alive']=time.time()
  except FileNotFoundError:row['first_missing']=time.time();row['terminal_state']='absent'
 tmp=root/'OBSERVATION.tmp';tmp.write_text(json.dumps(dict(time=time.time(),processes=rows),indent=2)+'\n');tmp.replace(root/'OBSERVATION.json')
 time.sleep(1)
(root/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=time.time(),scope='Process exit brackets only, not proof of GPU idleness or scientific completion'))+'\n')
