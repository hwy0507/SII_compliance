"""Run the independent campaign audit against the DAgger6 result prefix."""
from pathlib import Path

source = Path(__file__).with_name('audit_exposure_dagger5_20260929.py')
program = source.read_text()
program = program.replace('results/dagger5_balanced_*', 'results/damped_teacher_dagger6_*')
program = program.replace('Balanced DAgger5 ESN audit', 'Damped-teacher DAgger6 ESN audit')
exec(compile(program, str(source), 'exec'), {'__name__': '__main__', '__file__': str(source)})
