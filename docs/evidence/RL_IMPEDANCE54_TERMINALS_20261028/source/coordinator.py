from pathlib import Path
import subprocess,json,time,sys
root=Path(sys.argv[1]);runtime=Path(__file__).parent
try:
 for name in ['audit.py','review.py']:subprocess.run([sys.executable,str(runtime/name),'--root',str(root)],check=True)
 (root/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=time.time(),optimizer_updates=0,new_physics=0))+'\n')
except BaseException as e:
 (root/'COORDINATOR_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
