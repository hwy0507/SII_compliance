from parallel_fair_comparison_20261013 import admission, neural_cap, GIB


def test_reserve_growth_of_active_worker_not_only_rss():
    # 3GiB active cap, only1GiB currently resident: another2GiB may still grow.
    assert not admission(4*GIB, 1.5*GIB, [(3*GIB,GIB)], .75*GIB)
    assert admission(4.25*GIB, 1.5*GIB, [(3*GIB,GIB)], .75*GIB)


def test_unstarted_and_drained_lane_reservations():
    assert not admission(5*GIB, 1.5*GIB, [(3*GIB,0)], .75*GIB)
    assert admission(5*GIB, 1.5*GIB, [], .75*GIB)


def test_three_light_lanes_fit_without_promising_four():
    assert admission(4.5*GIB, 1.5*GIB, [(1.5*GIB,.5*GIB)]*2, .75*GIB)
    assert not admission(4*GIB, 1.5*GIB, [(1.5*GIB,.5*GIB)]*3, .75*GIB)


def test_pilot_margin_and_short_episode_do_not_shrink_cap():
    assert neural_cap(.5*GIB,True)==1.5*GIB
    assert neural_cap(.8*GIB,True)==2*GIB
    assert neural_cap(1.1*GIB,True)==3*GIB
    assert neural_cap(.1*GIB,False)==3*GIB
    assert neural_cap(0,True)==3*GIB
