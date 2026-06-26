from office.result import ConvertResult


def test_convert_result_fields():
    r = ConvertResult(markdown="x", images=["a.png"], image_count=1, unit_count=3)
    assert r.markdown == "x"
    assert r.images == ["a.png"]
    assert r.image_count == 1
    assert r.unit_count == 3
