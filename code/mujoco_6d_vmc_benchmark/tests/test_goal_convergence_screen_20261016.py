from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
import shutil

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from screen_goal_rl_convergence_20261016 import collect,read_bound,screen
from rl_goal_stage_20261016 import write

CRITERIA=dict(minimum_completed_episodes=96,window_episodes=32,
    adjacent_window_relative_mean_change_max=.05,last_window_return_cv_max=.25,
    required_task_and_strict_rate_each_last_window=.9)
CONDITIONS=[f'train_{i}' for i in range(32)]


def rows(count=96):
    return [dict(episode=i,condition_id=CONDITIONS[i%32],step_before=i*1375,
        step_after=(i+1)*1375,steps=1375,ended_utc='closed',return_value=10.,
        result=dict(task_success=True,strict_success=True,physical_valid=True,
                    full_task_horizon_completed=True)) for i in range(count)]


class ConvergenceScreenTests(unittest.TestCase):
    def test_valid_candidate_still_not_goal_or_acceptance(self):
        result=screen(rows(),CONDITIONS,CRITERIA)
        self.assertTrue(result['training_candidate'])
        self.assertFalse(result['acceptance'])
        self.assertFalse(result['goal_complete'])
        self.assertEqual(result['latest_window']['joint'],32)

    def test_failed_plateau_and_separate_success_flags_do_not_pass(self):
        data=rows()
        for row in data:
            row['return_value']=-20.
            row['result'].update(task_success=False,strict_success=False)
        result=screen(data,CONDITIONS,CRITERIA)
        self.assertEqual(result['relative_mean_drift'],0)
        self.assertFalse(result['training_candidate'])
        for row in data:
            row['result'].update(task_success=row['episode']%2==0,strict_success=row['episode']%2==1)
        self.assertEqual(screen(data,CONDITIONS,CRITERIA)['latest_window']['joint'],0)

    def test_coverage_sample_count_and_reward_stability(self):
        self.assertIn('insufficient_completed_episodes',screen(rows(95),CONDITIONS,CRITERIA)['reasons'])
        missing=rows()
        for row in missing:
            row['condition_id']=CONDITIONS[0]
        self.assertIn('latest_condition_coverage_incomplete',screen(missing,CONDITIONS,CRITERIA)['reasons'])
        drift=rows()
        for row in drift[-32:]:
            row['return_value']=12.
        self.assertIn('return_mean_not_stable',screen(drift,CONDITIONS,CRITERIA)['reasons'])
        variance=rows()
        for row in variance[-32:]:
            row['return_value']=0. if row['episode']%2 else 20.
        self.assertIn('return_variation_too_large',screen(variance,CONDITIONS,CRITERIA)['reasons'])

    def test_early_failures_remain_in_denominator_and_pending_is_explicit(self):
        data=rows()
        for row in data[-4:]:
            row['result'].update(task_success=False,strict_success=False,full_task_horizon_completed=False)
        pending=dict(episode=96,condition_id=CONDITIONS[0],step_before=96*1375)
        result=screen(data+[pending],CONDITIONS,CRITERIA)
        self.assertFalse(result['training_candidate'])
        self.assertEqual(result['latest_window']['count'],32)
        self.assertEqual(result['latest_window']['joint'],28)
        self.assertEqual(result['incomplete_episodes'],[96])

    def test_rejects_duplicates_skips_nonfinite_and_missing_gate(self):
        for change in ('duplicate','gap','nan','missing_gate'):
            data=rows()
            if change=='duplicate':data[-1]=deepcopy(data[-2])
            if change=='gap':data.pop(10)
            if change=='nan':data[-1]['return_value']=float('nan')
            if change=='missing_gate':data[-1]['result'].pop('strict_success')
            with self.assertRaises((AssertionError,KeyError)):
                screen(data,CONDITIONS,CRITERIA)

    def make_lineage(self,base):
        previous=None
        hashes={}
        for index in range(2):
            root=base/f'stage{index}'
            root.mkdir()
            jobs=[dict(name=name,controller=controller,seed=1,output=str(root/name),
                inherited_steps=index*48*1375) for name,controller in (
                    ('direct',None),('impedance','impedance'),('admittance','admittance'),('vmc','vmc'))]
            reg=dict(schema='sii-rl-persistent-goal-stage-v1',run_root=str(root),jobs=jobs,
                training_convergence=CRITERIA)
            if previous:
                reg['previous_stage']=dict(root=str(previous),
                    registration_sha256=read_bound(previous/'REGISTRATION.json')[1],
                    execution_sha256=read_bound(previous/'execution.json')[1])
            write(root/'REGISTRATION.json',reg)
            for job in jobs:
                output=Path(job['output'])
                output.mkdir()
                spec=dict(protocol_sha256='physics',seed=1,controller=job['controller'],agent_config={'n_step':25},
                    reward={'version':'fixed'},reward_variant='fixed',utd=1,prior_file_sha256='prior',
                    training_conditions=CONDITIONS,goal_registration_sha256=read_bound(root/'REGISTRATION.json')[1])
                write(output/'PROTOCOL.json',spec)
                execution=dict(status='complete',steps=(index+1)*48*1375,episodes=(index+1)*48,
                    rows=rows()[index*48:(index+1)*48])
                if previous:
                    execution['resumed_from']=dict(inherited_steps=index*48*1375,
                        parent_execution_sha256=hashes[job['name']])
                write(output/'execution.json',execution)
                hashes[job['name']]=read_bound(output/'execution.json')[1]
            write(root/'execution.json',{'status':'finite_stage_complete'})
            previous=root
        return previous

    def test_lineage_uses_own_rows_not_cumulative_episode_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_lineage(Path(tmp))
            report=collect(root)
            self.assertTrue(report['all_training_candidates'])
            self.assertFalse(report['goal_complete'])
            for method in report['methods'].values():
                self.assertEqual(method['screen']['closed']['count'],96)

    def test_lineage_rejects_treatment_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_lineage(Path(tmp))
            path=root/'direct/PROTOCOL.json'
            spec,_=read_bound(path)
            spec['reward']={'version':'changed'}
            write(path,spec)
            with self.assertRaisesRegex(AssertionError,'different training treatments'):
                collect(root)

    def test_missing_parent_method_cannot_drop_failed_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_lineage(Path(tmp))
            (root.parent/'stage0/direct/execution.json').rename(root.parent/'stage0/direct/preserved.json')
            with self.assertRaisesRegex(AssertionError,'parent method evidence is missing'):
                collect(root)

    def test_lineage_rejects_optional_tracking_objective_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_lineage(Path(tmp))
            path=root/'direct/PROTOCOL.json'
            spec,_=read_bound(path)
            from goal_tracking_reward_20261016 import CONFIG
            spec['tracking_guidance']=CONFIG
            write(path,spec)
            with self.assertRaisesRegex(AssertionError,'different training treatments'):
                collect(root)

    def selected_fixture(self, base):
        root=self.make_lineage(base)
        previous=base/'stage0'
        reg,_=read_bound(root/'REGISTRATION.json')
        pilot=base/'pilot';pilot.mkdir()
        prototype=deepcopy(reg['jobs'][0])
        pilot_jobs=[]
        for name in ('control','tracking'):
            output=pilot/name
            shutil.copytree(previous/'direct',output)
            pilot_jobs.append(dict(prototype,name=name,output=str(output),inherited_steps=0))
        pilot_reg=dict(schema=reg['schema'],run_root=str(pilot),jobs=pilot_jobs,
            experiment_kind='fresh_direct_tracking_pilot',training_convergence=CRITERIA)
        write(pilot/'REGISTRATION.json',pilot_reg)
        write(pilot/'execution.json',{'status':'finite_stage_complete'})
        for job in pilot_jobs:
            path=Path(job['output'])/'PROTOCOL.json'
            spec,_=read_bound(path)
            spec['goal_registration_sha256']=read_bound(pilot/'REGISTRATION.json')[1]
            if job['name']=='control':spec['reward']={'different':'not selected'}
            write(path,spec)
        # A selected historical failure must still count; the unselected arm's
        # differing objective and duplicate episode IDs must never be pooled.
        path=pilot/'tracking/execution.json'
        history,_=read_bound(path)
        history['rows'][0]['result'].update(task_success=False,strict_success=False)
        write(path,history)
        reg.pop('previous_stage')
        reg['selected_lineages']={}
        for job in reg['jobs']:
            parent=pilot if job['controller'] is None else previous
            parent_name='tracking' if job['controller'] is None else job['name']
            reg['selected_lineages'][job['name']]=dict(root=str(parent),job=parent_name,
                registration_sha256=read_bound(parent/'REGISTRATION.json')[1],
                execution_sha256=read_bound(parent/'execution.json')[1],
                protocol_sha256=read_bound(parent/parent_name/'PROTOCOL.json')[1])
        write(root/'REGISTRATION.json',reg)
        for job in reg['jobs']:
            path=Path(job['output'])/'PROTOCOL.json'
            spec,_=read_bound(path);spec['goal_registration_sha256']=read_bound(root/'REGISTRATION.json')[1]
            write(path,spec)
            path=Path(job['output'])/'execution.json'
            state,_=read_bound(path)
            parent=reg['selected_lineages'][job['name']]
            state['resumed_from']['parent_execution_sha256']=read_bound(
                Path(parent['root'])/parent['job']/'execution.json')[1]
            write(path,state)
        return root,pilot

    def test_selected_lineage_counts_failures_without_pooling_other_arm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,pilot=self.selected_fixture(Path(tmp))
            result=collect(root)
            direct=result['methods']['direct']
            self.assertEqual(direct['screen']['closed']['count'],96)
            self.assertEqual(direct['screen']['closed']['joint'],95)
            self.assertEqual(direct['evidence'][0]['source_job'],'tracking')
            self.assertEqual(len(direct['evidence']),2)
            self.assertFalse(result['goal_complete'])
            self.assertFalse(result['acceptance_performed'])

    def test_selected_history_cannot_disappear_or_change_objective(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,pilot=self.selected_fixture(Path(tmp))
            path=pilot/'tracking/execution.json';path.rename(path.with_name('preserved.json'))
            with self.assertRaisesRegex(AssertionError,'parent method evidence is missing'):
                collect(root)
        with tempfile.TemporaryDirectory() as tmp:
            root,pilot=self.selected_fixture(Path(tmp))
            path=root/'direct/PROTOCOL.json';spec,_=read_bound(path)
            spec['tracking_guidance']={'changed':True};write(path,spec)
            with self.assertRaisesRegex(AssertionError,'different training treatments'):
                collect(root)

    def test_normal_stage_after_selection_follows_each_ancestry(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root,pilot=self.selected_fixture(base)
            child=base/'later';child.mkdir()
            reg,_=read_bound(root/'REGISTRATION.json')
            reg.pop('selected_lineages')
            reg['run_root']=str(child)
            reg['previous_stage']=dict(root=str(root),registration_sha256=read_bound(root/'REGISTRATION.json')[1],
                                      execution_sha256=read_bound(root/'execution.json')[1])
            for job in reg['jobs']:
                job.update(output=str(child/job['name']),inherited_steps=96*1375)
            write(child/'REGISTRATION.json',reg)
            for job in reg['jobs']:
                output=Path(job['output']);output.mkdir()
                spec,_=read_bound(root/job['name']/'PROTOCOL.json')
                spec['goal_registration_sha256']=read_bound(child/'REGISTRATION.json')[1]
                write(output/'PROTOCOL.json',spec)
                state=dict(status='complete',steps=144*1375,rows=rows(144)[96:],
                    resumed_from=dict(inherited_steps=96*1375,
                        parent_execution_sha256=read_bound(root/job['name']/'execution.json')[1]))
                write(output/'execution.json',state)
            result=collect(child)
            self.assertEqual(result['methods']['direct']['screen']['closed']['count'],144)
            self.assertEqual(result['methods']['direct']['screen']['closed']['joint'],143)
            self.assertEqual(len(result['methods']['direct']['evidence']),3)


if __name__=='__main__':
    unittest.main()
