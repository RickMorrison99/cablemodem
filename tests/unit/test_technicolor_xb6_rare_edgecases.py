import pytest
from pathlib import Path
from bs4 import BeautifulSoup

from app.drivers.technicolor_xb6 import XB6Driver


def _load_fixture(name):
    path = Path(__file__).parent.parent / "fixtures" / name
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def test_empty_table_no_crash(monkeypatch):
    soup = _load_fixture("xb6_empty_table.html")
    monkeypatch.setattr(XB6Driver, "_fetch_status_page", lambda self: soup)
    d = XB6Driver("https://0.0.0.0", "u", "p")
    data = d.get_docsis_data()
    assert isinstance(data.get("channelDs"), dict)
    assert isinstance(data.get("channelUs"), dict)
    assert sum(len(v) for v in data["channelDs"].values()) == 0


def test_nonstandard_labels(monkeypatch):
    soup = _load_fixture("xb6_nonstandard_labels.html")
    monkeypatch.setattr(XB6Driver, "_fetch_status_page", lambda self: soup)
    d = XB6Driver("https://0.0.0.0", "u", "p")
    data = d.get_docsis_data()
    # parser should not crash; may return no channels
    assert isinstance(data, dict)


def test_duplicate_channel_ids(monkeypatch):
    soup = _load_fixture("xb6_duplicate_ids.html")
    monkeypatch.setattr(XB6Driver, "_fetch_status_page", lambda self: soup)
    d = XB6Driver("https://0.0.0.0", "u", "p")
    data = d.get_docsis_data()
    ds = data["channelDs"]
    total = len(ds.get("docsis30", [])) + len(ds.get("docsis31", []))
    assert total == 2
    ids = [c["channelID"] for c in ds.get("docsis30", []) + ds.get("docsis31", [])]
    assert ids[0] == ids[1]


def test_compressed_values_parse(monkeypatch):
    soup = _load_fixture("xb6_compressed_values.html")
    monkeypatch.setattr(XB6Driver, "_fetch_status_page", lambda self: soup)
    d = XB6Driver("https://0.0.0.0", "u", "p")
    data = d.get_docsis_data()
    ds = data["channelDs"]
    all_ch = ds.get("docsis30", []) + ds.get("docsis31", [])
    assert len(all_ch) == 1
    ch = all_ch[0]
    # SNR should parse the first numeric token
    assert ch.get("snr") == pytest.approx(38.4)
