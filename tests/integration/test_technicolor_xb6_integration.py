import pytest
from pathlib import Path
from bs4 import BeautifulSoup

from app.drivers.technicolor_xb6 import XB6Driver


def test_technicolor_xb6_from_fixture(monkeypatch):
    """Use a recorded network_setup.jst fixture so CI doesn't need the live device."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "xb6_network_setup.html"
    html = fixture_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # Patch the driver to return the fixture HTML instead of performing network I/O
    monkeypatch.setattr(XB6Driver, "_fetch_status_page", lambda self: soup)

    d = XB6Driver("https://10.0.0.1", "admin", "happy123")
    data = d.get_docsis_data()

    assert "channelDs" in data and "channelUs" in data
    ds = data["channelDs"]
    us = data["channelUs"]
    assert isinstance(ds.get("docsis30"), list)
    assert isinstance(ds.get("docsis31"), list)
    assert isinstance(us.get("docsis30"), list)
    assert isinstance(us.get("docsis31"), list)
    # Expect at least one downstream channel from the fixture
    assert len(ds.get("docsis30", [])) + len(ds.get("docsis31", [])) > 0
