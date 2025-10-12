from hhp.packet import build_fragment
def test_fragment_size():
    frag = build_fragment(tag="angelic:weather", payload=b"hello", t_epoch=1, win_ctr=1, fragment_size=1024)
    assert len(frag)==1024
