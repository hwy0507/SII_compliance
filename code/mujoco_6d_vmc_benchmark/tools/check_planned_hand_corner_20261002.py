"""Meaningful planner/task regressions without stepping a simulator."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from planned_hand_corner_20261002 import astar, PlannedCornerTask, DOWN
from office_task_v4_20260917 import PickPlaceTask


def main():
    start=np.array([0.,0.,0.]); goal=np.array([.1,0.,0.])
    box=('obstacle',np.array([.05,0.,0.]),np.array([.015,.02,.04]))
    half=np.full(3,.005)
    path,expanded=astar(start,goal,[box],half)
    assert expanded>0 and len(path)>2
    assert any(abs(p[1])>.025 or abs(p[2])>.045 for p in path)
    for a,b in zip(path,path[1:]):
        for p in np.linspace(a,b,50):
            assert not np.all(abs(p-box[1])<box[2]+half+.002-1e-8)
    again,_=astar(start,goal,[box],half)
    np.testing.assert_array_equal(path,again)
    try:
        astar(start,box[1],[box],half)
    except ValueError:
        pass
    else:
        raise AssertionError('Planner accepted goal inside an obstacle')
    base=PickPlaceTask(np.array([.54,-.19,.60]),[7,8],[7,8])
    release=np.array([.63,-.31,.64])
    task=PlannedCornerTask(base,{5:[(release,DOWN)]})
    task.index=5;task.rotation=DOWN.copy()
    q=np.zeros(9);dq=np.zeros(9);twist=np.zeros(6);wrench=np.zeros(6)
    # Being stationary outside the specified XY region must never release.
    for _ in range(20):
        assert not task.update(q,dq,release+[.03,0,0],DOWN,twist,wrench)
    assert task.index==5
    # Five 40ms samples at the commanded pose release without any force truth.
    for _ in range(5):
        task.update(q,dq,release,DOWN,twist,wrench)
    assert task.index==6
    base=PickPlaceTask(np.zeros(3),[7,8],[7,8])
    route=[(np.array([x,0.,0.]),DOWN) for x in (0.,.01,.02)]
    task=PlannedCornerTask(base,{4:route});task.index=4;task.cursors[4]=1
    task.goals[4]=route[1][0].copy();task.allow_lateral_rejoin=True
    task.update(q,dq,np.array([.015,.09,0.]),DOWN,twist,wrench)
    assert task.cursors[4]==1, 'Must not jump arbitrarily far from the reference'
    task.update(q,dq,np.array([.015,.03,0.]),DOWN,twist,wrench)
    assert task.cursors[4]==2 and task.index==4, 'A contact detour may cross a waypoint plane without returning inside the obstacle'
    task.cursors[4]=1;task.goals[4]=route[1][0].copy()
    task.update(q,dq,np.array([.15,.03,0.]),DOWN,twist,wrench)
    assert task.cursors[4]==2, 'Forward travel after a detour must not count as lateral deviation'
    task.update(q,dq,np.array([.15,.03,0.]),DOWN,twist,wrench)
    assert task.index==4, 'Crossing the last plane is not arrival at the terminal waypoint'
    print('PASS: obstacle detour, swept edges, deterministic path, blocked goal rejection, no false release, proprioceptive release, bounded lateral rejoin')


if __name__=='__main__':
    main()
