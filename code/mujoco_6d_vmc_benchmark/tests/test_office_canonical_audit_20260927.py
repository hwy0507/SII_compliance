from types import SimpleNamespace
import numpy as np
from validate_office_apparatus_v5_20260917 import canonical_observation, is_external_contact


def test_payload_body_exclusion_does_not_depend_on_drive_target():
    model=SimpleNamespace(geom_bodyid=np.array([0,1,2,2,3]))
    # Two payload geoms on one body; neither is an external safety contact.
    for g1,g2 in ((1,2),(3,1)):
        assert not is_external_contact(model,{1},2,g1,g2)
    for g1,g2 in ((1,0),(0,1),(1,4),(4,1)):
        assert is_external_contact(model,{1},2,g1,g2)
    assert not is_external_contact(model,{1},2,2,4)


def test_observation_keeps_all_six_wrench_channels_and_no_task_truth():
    obs=canonical_observation(np.arange(9),np.arange(9)+10,np.arange(6)+20,
        np.arange(6)+30,np.arange(6)+40,np.arange(7)+50,np.arange(6)+60,np.arange(3)+70)
    assert obs.shape==(48,)
    np.testing.assert_array_equal(obs[26:32],np.full(6,-20))
    np.testing.assert_array_equal(obs[32:39],np.arange(7)+50)
    np.testing.assert_array_equal(obs[39:45],np.arange(6)+60)
    np.testing.assert_array_equal(obs[45:48],np.arange(3)+70)
