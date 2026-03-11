import pytest
from bs4 import BeautifulSoup

from app.drivers.technicolor_xb6 import XB6Driver


def test_parse_bonded_table_missing_cells():
    html = """
    <table>
      <thead><tr><td>Downstream</td></tr></thead>
      <tbody>
        <tr><th>Channel ID</th><td>1</td><td>2</td><td>3</td></tr>
        <tr><th>Frequency</th><td>100 MHz</td><td>200 MHz</td></tr>
        <tr><th>Modulation</th><td>256 QAM</td><td>256 QAM</td><td>256 QAM</td></tr>
      </tbody>
    </table>
    """

    driver = XB6Driver("https://0.0.0.0", "u", "p")
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    parsed = driver._parse_bonded_table(table, downstream=True)

    assert len(parsed) == 3
    # missing third frequency cell should default to empty string
    assert parsed[2]["frequency"] == ""


def test_parse_bonded_table_ofdm_classification():
    html = """
    <table>
      <thead><tr><td>Downstream</td></tr></thead>
      <tbody>
        <tr><th>Channel ID</th><td>1</td><td>2</td></tr>
        <tr><th>Frequency</th><td>100 MHz</td><td>200 MHz</td></tr>
        <tr><th>Modulation</th><td>256 QAM</td><td>OFDM</td></tr>
      </tbody>
    </table>
    """

    soup = BeautifulSoup(html, "html.parser")
    driver = XB6Driver("https://0.0.0.0", "u", "p")
    # patch fetch to return our fixture DOM
    driver._fetch_status_page = lambda: soup
    data = driver.get_docsis_data()

    # ensure OFDM channel is classified into docsis31
    assert len(data["channelDs"]["docsis31"]) == 1
    ofdm_ch = data["channelDs"]["docsis31"][0]
    assert ofdm_ch["modulation"].upper().find("OFDM") != -1


def test_parse_bonded_table_unusual_freq_format():
    html = """
    <table>
      <thead><tr><td>Downstream</td></tr></thead>
      <tbody>
        <tr><th>Channel ID</th><td>5</td></tr>
        <tr><th>Frequency</th><td>812000000</td></tr>
        <tr><th>Modulation</th><td>256 QAM</td></tr>
      </tbody>
    </table>
    """

    driver = XB6Driver("https://0.0.0.0", "u", "p")
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    parsed = driver._parse_bonded_table(table, downstream=True)

    assert parsed[0]["frequency"] == "812 MHz"
