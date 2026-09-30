from run_contact_sidecar_pairs_20260924 import canonical_contact


def test_only_explicit_sets_are_order_insensitive():
    a=dict(pairs=[['rod','hand'],['guard','link']],robot_geoms=['hand','link'],robot_bodies=['b','a'],
           other_contacts=['y','x'],force=[1.,2.,3.],max_penetration_m=.0002)
    b=dict(a,pairs=a['pairs'][::-1],robot_geoms=a['robot_geoms'][::-1],robot_bodies=['a','b'],other_contacts=['x','y'])
    assert canonical_contact(a)==canonical_contact(b)
    assert canonical_contact(a)!=canonical_contact(dict(b,force=[3.,2.,1.]))
    assert canonical_contact(a)!=canonical_contact(dict(b,max_penetration_m=.00020000000001))
