"""Review finite early replay receipts against an existing completed control."""
from pathlib import Path
import argparse
import hashlib
import json
import math


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main(args):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=args.run;reg=json.loads((out/'REGISTRATION.json').read_text());report=json.loads((out/'REVIEW.json').read_text())
    for key in ['checkpoint','completed_control','control_review','completed_control_report']:
        assert sha(reg[key]['path'])==reg[key]['sha256']
    control=json.loads(Path(reg['completed_control']['path']).read_text());candidate=report['candidate']
    assert report['passed'] and report['formal_state_unchanged'] and report['control_rerun'] is False
    assert report['weights_saved'] is False and report['new_physics']==0
    assert report['total_critic_updates']==16000 and report['total_actor_updates']==2000
    assert candidate==json.loads((out/'horizon32_RESULT.json').read_text())
    assert report['control_final']==control['points'][-1]
    assert candidate['outer_updates']==2000 and candidate['critic_updates']==16000 and candidate['actor_updates']==2000
    assert candidate['sampled_rows']==control['sampled_rows']==65536*2000
    assert candidate['uniform_draws_sha256']==control['sampled_rows_sha256']
    assert candidate['final_sample_rng_digest']==control['final_sample_rng_digest']
    assert candidate['sampled_rows_sha256']!=control['sampled_rows_sha256']
    for key in ['initial_learner_digest','initial_replay_digest']:assert candidate[key]==control[key]
    assert all(candidate['initial'][k]==v for k,v in control['initial'].items())
    assert [p['outer_updates'] for p in candidate['points']]==list(range(100,2001,100))
    for p in [candidate['initial']]+candidate['points']:
        for k,v in p.items():assert all(math.isfinite(x) for x in (v if isinstance(v,list) else [v])),k
    assert not list(out.rglob('*.pt'))
    fig,axes=plt.subplots(2,3,figsize=(15,8))
    for ax,key in zip(axes.flat,['terminal_mae','td1_mae','td32_mae','q_mean','last100_critic_loss','mode_public0_mean']):
        for label,a in [('Completed uniform control',control),('Half early replay candidate',candidate)]:
            ax.plot([p['outer_updates'] for p in a['points']],[p[key] for p in a['points']],label=label)
        ax.set_title(key);ax.set_xlabel('Auxiliary outer updates');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Formal13 initial state; reused control; no physical improvement or weight promotion')
    fig.tight_layout();fig.savefig(out/'comparison.png',dpi=150);plt.close(fig)
    result=dict(passed=True,report_sha256=sha(out/'REVIEW.json'),checkpoint=reg['checkpoint'],control=reg['completed_control'],source_sha256=sha(__file__),identical_initial_state_and_underlying_uniform_draws=True,control_rerun=False,final_control=control['points'][-1],initial_candidate=candidate['initial'],final_candidate=candidate['points'][-1],early_rows=candidate['early_rows'],new_physics=0,optimizer_updates=0,plot_sha256=sha(out/'comparison.png'),limitation='Receipt consistency review, not an independent numerical training rerun or physical task test. Candidate early diagnostics have no recorded final-control counterpart. Visual inspection separate.')
    (out/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);main(p.parse_args())
