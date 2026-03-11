import pytest
from pathlib import Path
from bs4 import BeautifulSoup

from app.drivers.technicolor_xb6 import XB6Driver


def _load_fixture():
    fixture_path = Path(__file__).parent.parent / "fixtures" / "xb6_network_setup.html"
    return BeautifulSoup(fixture_path.read_text(encoding="utf-8"), "html.parser")


def test_docsis_parsing_from_fixture(monkeypatch):
    """Ensure get_docsis_data() parses downstream/upstream tables from fixture."""
    soup = _load_fixture()
    # Patch network fetch to return the fixture DOM
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

    # Spot-check fields on first downstream channel
    first = (ds.get("docsis30") or ds.get("docsis31") or [None])[0]
    assert first is not None
    assert isinstance(first.get("channelID"), int)
    assert isinstance(first.get("frequency"), str)
    assert first.get("frequency").endswith("MHz")


def test_value_parsers():
    # _parse_number should extract numeric portion
    assert XB6Driver._parse_number("38.4 dB") == pytest.approx(38.4)
    # _parse_int should extract integer tokens
    assert XB6Driver._parse_int("5") == 5
    # _format_freq should convert large Hz values to MHz and preserve MHz strings
    assert XB6Driver._format_freq("812000000") == "812 MHz"
    assert XB6Driver._format_freq("465 MHz") == "465 MHz"
