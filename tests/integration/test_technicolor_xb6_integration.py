import pytest

from app.drivers.technicolor_xb6 import XB6Driver


def test_technicolor_xb6_live():
    """Integration test that exercises the live device. Skips if device not reachable."""
    d = XB6Driver("https://10.0.0.1", "admin", "happy123")
    try:
        d.login()
        data = d.get_docsis_data()
    except Exception as e:
        pytest.skip(f"Live device unreachable or auth failed: {e}")

    assert "channelDs" in data and "channelUs" in data
    ds = data["channelDs"]
    us = data["channelUs"]
    assert isinstance(ds.get("docsis30"), list)
    assert isinstance(ds.get("docsis31"), list)
    assert isinstance(us.get("docsis30"), list)
    assert isinstance(us.get("docsis31"), list)
    assert len(ds.get("docsis30", [])) + len(ds.get("docsis31", [])) > 0
