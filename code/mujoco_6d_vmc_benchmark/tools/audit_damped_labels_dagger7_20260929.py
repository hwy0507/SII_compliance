"""Run the independent campaign audit against the DAgger7 result prefix."""
from pathlib import Path

source = Path(__file__).with_name('audit_exposure_dagger5_20260929.py')
program = source.read_text()
program = program.replace('results/dagger5_balanced_*', 'results/damped_labels_dagger7_*')
program = program.replace('Balanced DAgger5 ESN audit', 'Damped-label DAgger7 ESN audit')
exec(compile(program, str(source), 'exec'), {'__name__': '__main__', '__file__': str(source)})
