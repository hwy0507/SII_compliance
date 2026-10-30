"""Keep the existing worker while routing the wide model contract explicitly."""
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
import current_student_policy_20260921 as legacy_policy
from current_student_policy_mlp384_20261031 import load_current

legacy_policy.load_current = load_current
worker = ROOT/'tools/run_video_reference_coverage_20261029.py'
sys.argv[0] = str(worker)
runpy.run_path(str(worker), run_name='__main__')
