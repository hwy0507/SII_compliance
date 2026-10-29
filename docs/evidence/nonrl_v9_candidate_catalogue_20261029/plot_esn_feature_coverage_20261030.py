"""Plot only hash-bound descriptive development windows; not final test metrics."""
import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
b=Path(__file__).resolve().parent;p=b/'ESN_FEATURE_COVERAGE_V2_20261030.json'
d=json.loads(p.read_text());before=hashlib.sha256(p.read_bytes()).hexdigest()
fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
labels=['Seed01 rank1 (rod fail)','Seed01 rank2 (rod pass; ball fail)','Seed01 rank3 (rod fail)','Seed02 rank1 (rod pass)']
for row,label in zip(d['rows'],labels):
 windows=row['windows'];time=[w['end_index_exclusive']*.04 for w in windows]
 axes[0].plot(time,[w['max_envelope_excess'] for w in windows],marker='.',label=label)
 axes[1].plot(time,[w['max_residual_raw'] for w in windows],marker='.',label=label)
axes[0].set_ylabel('Max feature excess / training range');axes[0].set_yscale('symlog',linthresh=.01)
axes[1].set_ylabel('Max |residual raw readout|');axes[1].set_yscale('symlog',linthresh=.1)
for ax in axes:
 ax.set_xlabel('End of 2 s window (s)');ax.grid(alpha=.25)
axes[0].legend(fontsize=7,loc='upper left')
fig.suptitle('Same rod00: ESN training-envelope departure and readout growth\nSaved histories only; not a causal proof or final unseen-test result',fontsize=11)
for ext in ['png','pdf']:fig.savefig(b/('ESN_FEATURE_COVERAGE_20261030.'+ext),dpi=170)
assert hashlib.sha256(p.read_bytes()).hexdigest()==before
(b/'ESN_FEATURE_PLOT_RECEIPT_20261030.json').write_text(json.dumps(dict(input_sha256=before,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),outputs={ext:hashlib.sha256((b/('ESN_FEATURE_COVERAGE_20261030.'+ext)).read_bytes()).hexdigest() for ext in ['png','pdf']}),indent=2)+'\n')
