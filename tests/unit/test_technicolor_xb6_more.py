import pytest
from pathlib import Path
from bs4 import BeautifulSoup

from app.drivers.technicolor_xb6 import XB6Driver


def test_ofdm_fixture_counts(monkeypatch):
    fixture = Path(__file__).parent.parent / "fixtures" / "xb6_ofdm_multi.html"
    soup = BeautifulSoup(fixture.read_text(encoding="utf-8"), "html.parser")

    monkeypatch.setattr(XB6Driver, "_fetch_status_page", lambda self: soup)
    d = XB6Driver("https://0.0.0.0", "u", "p")
    data = d.get_docsis_data()

    # two downstream OFDM channels expected from fixture
    total_ds = len(data["channelDs"]["docsis30"]) + len(data["channelDs"]["docsis31"])
    assert total_ds == 2
    assert len(data["channelDs"]["docsis31"]) == 2


def test_complex_channels_parsing(monkeypatch):
    fixture = Path(__file__).parent.parent / "fixtures" / "xb6_channels_complex.html"
    soup = BeautifulSoup(fixture.read_text(encoding="utf-8"), "html.parser")

    monkeypatch.setattr(XB6Driver, "_fetch_status_page", lambda self: soup)
    d = XB6Driver("https://0.0.0.0", "u", "p")
    data = d.get_docsis_data()

    # downstream: two QAM (docsis30) and one OFDM (docsis31)
    assert len(data["channelDs"]["docsis30"]) == 2
    assert len(data["channelDs"]["docsis31"]) == 1

    # upstream: one QAM and one OFDMA
    assert len(data["channelUs"]["docsis30"]) == 1
    assert len(data["channelUs"]["docsis31"]) == 1

    # spot check converted MHz from Hz
    ofdm = data["channelDs"]["docsis31"][0]
    assert ofdm["frequency"].endswith("MHz")
