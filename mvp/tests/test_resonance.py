from hhp.resonance import tag_vec, cosine
def test_cosine_self():
    v = tag_vec("angelic:weather")
    assert 0.99 <= cosine(v,v) <= 1.01
