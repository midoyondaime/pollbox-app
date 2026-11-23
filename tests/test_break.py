# deliberately failing test: proves that a red test blocks the image build
def test_gate_blocks_release():   # a test that always fails
    assert 1 == 2                 # false on purpose
