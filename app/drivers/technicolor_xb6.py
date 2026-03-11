"""Technicolor XB6 (CGM4140COM) driver.

Implements HTTP web UI scraping of the network_setup.jst page to extract
DOCSIS downstream/upstream channel tables. Authentication uses the
/check.jst endpoint which sets a DUKSID session cookie.

This driver intentionally mirrors the data structures used by the
Arris CM3500 driver so the analyzer/collector can consume the results.
"""

import logging
import re
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

from .base import ModemDriver

log = logging.getLogger("docsis.driver.technicolor_xb6")


class XB6Driver(ModemDriver):
    """Driver for Technicolor XB6 (CGM4140COM).

    - login() posts to /check.jst and preserves cookies set by the UI
    - _fetch_status_page() retrieves /network_setup.jst
    - get_docsis_data() parses the downstream/upstream tables into the
      same shaped structure returned by other drivers.
    """

    def __init__(self, url: str, user: str, password: str):
        if url.startswith("http://"):
            url = "https://" + url[len("http://") :]
            log.info("XB6 driver upgraded URL to %s", url)
        super().__init__(url, user, password)
        self._session = requests.Session()
        # Local test devices commonly use self-signed certs
        self._session.verify = False

    def login(self) -> None:
        """Authenticate using /check.jst (preferred) with a fallback.

        Retries once on ConnectionError with a fresh session.
        """
        payload = {"username": self._user, "password": self._password, "locale": "false"}
        endpoints = ["/check.jst", "/cgi-bin/login_cgi"]

        for attempt in range(2):
            for ep in endpoints:
                try:
                    r = self._session.post(f"{self._url}{ep}", data=payload, timeout=30)
                    r.raise_for_status()
                    log.info("XB6 auth OK via %s", ep)
                    return
                except requests.ConnectionError:
                    log.warning("XB6 connection lost when hitting %s", ep)
                    if attempt == 0:
                        self._session.close()
                        self._session = requests.Session()
                        self._session.verify = False
                        continue
                    raise RuntimeError("XB6 authentication failed: connection refused after retry")
                except requests.RequestException as e:
                    log.debug("Auth endpoint %s failed: %s", ep, e)
                    # try next endpoint
                    continue
        raise RuntimeError("XB6 authentication failed: no auth endpoint succeeded")

    def get_docsis_data(self) -> dict:
        """Scrape the network_setup.jst page and return parsed channel lists.

        Returns:
        {
          "channelDs": {"docsis30": [...], "docsis31": [...]},
          "channelUs": {"docsis30": [...], "docsis31": [...]}
        }
        """
        soup = self._fetch_status_page()

        ds_tables = []
        us_tables = []
        # find tables whose heading contains Downstream/Upstream
        for table in soup.find_all("table"):
            # search nearby header text (previous siblings) for "Downstream"/"Upstream"
            header = None
            # try thead > tr > td
            thead = table.find("thead")
            if thead:
                td = thead.find("td")
                if td:
                    header = td.get_text(strip=True).lower()
            # fallback: inspect preceding text nodes
            if not header:
                prev = table.find_previous(string=True)
                if prev:
                    header = str(prev).strip().lower()
            if not header:
                continue
            if "downstream" in header:
                ds_tables.append(table)
            elif "upstream" in header:
                us_tables.append(table)

        ds30 = []
        ds31 = []
        for t in ds_tables:
            parsed = self._parse_bonded_table(t, downstream=True)
            for ch in parsed:
                if ch.get("modulation", "").upper().find("OFDM") != -1:
                    ds31.append(ch)
                else:
                    ds30.append(ch)

        us30 = []
        us31 = []
        for t in us_tables:
            parsed = self._parse_bonded_table(t, downstream=False)
            for ch in parsed:
                if ch.get("modulation", "").upper().find("OFDMA") != -1:
                    us31.append(ch)
                else:
                    us30.append(ch)

        return {
            "channelDs": {"docsis30": ds30, "docsis31": ds31},
            "channelUs": {"docsis30": us30, "docsis31": us31},
        }

    def get_device_info(self) -> dict:
        try:
            soup = self._fetch_status_page()
            info = {}
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = row.find_all("td")
                    if len(cells) == 2:
                        key = cells[0].get_text(strip=True)
                        val = cells[1].get_text(strip=True)
                        if key:
                            info[key] = val

            model = info.get("Model", info.get("Hardware Model", "CGM4140COM"))
            return {"manufacturer": "Technicolor", "model": model, "sw_version": info.get("Download Version", "")}
        except Exception:
            return {"manufacturer": "Technicolor", "model": "CGM4140COM", "sw_version": ""}

    def get_connection_info(self) -> dict:
        return {}

    def _fetch_status_page(self) -> BeautifulSoup:
        try:
            r = self._session.get(f"{self._url}/network_setup.jst", timeout=30)
            r.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"XB6 status page retrieval failed: {e}")
        return BeautifulSoup(r.text, "html.parser")

    def _parse_bonded_table(self, table, downstream: bool = True) -> List[Dict]:
        """Parse a bonded (transposed) table where columns represent channels.

        The table layout used by XB6 presents Channel ID as the first row
        and subsequent rows contain metric values for each channel.
        """
        tbody = table.find("tbody") or table
        rows = tbody.find_all("tr")
        if not rows:
            return []

        # find 'Channel ID' row index
        header_idx = None
        for i, row in enumerate(rows):
            th = row.find("th")
            if th and "channel id" in th.get_text(strip=True).lower():
                header_idx = i
                break
        if header_idx is None:
            return []

        channel_id_cells = rows[header_idx].find_all("td")
        channel_ids = [self._parse_int(td.get_text(strip=True)) for td in channel_id_cells]
        channels = [{"channelID": cid} for cid in channel_ids]

        # process subsequent rows
        for row in rows[header_idx + 1 :]:
            th = row.find("th")
            if not th:
                continue
            label = th.get_text(strip=True).lower()
            values = [td.get_text(strip=True) for td in row.find_all("td")]
            for idx, val in enumerate(values):
                if idx >= len(channels):
                    continue
                ch = channels[idx]
                if "lock status" in label:
                    ch["locked"] = val.lower().startswith("lock") or "locked" in val.lower()
                elif "frequency" in label:
                    ch["frequency"] = self._format_freq(val)
                elif label.startswith("snr") or "snr" in label:
                    ch["snr"] = self._parse_number(val)
                elif "power level" in label or "power" == label:
                    ch["powerLevel"] = self._parse_number(val)
                elif "modulation" in label:
                    ch["modulation"] = val
                elif "symbol rate" in label:
                    ch["symbol_rate"] = self._parse_number(val)
                elif "channel type" in label:
                    ch["channel_type"] = val
                # other metrics (errors, counts) are left as-is; add as needed

        # Post-process: ensure numeric channelIDs and sensible defaults
        for ch in channels:
            if "frequency" not in ch:
                ch["frequency"] = ""
            if "powerLevel" not in ch:
                ch["powerLevel"] = None
            if "snr" not in ch:
                ch["snr"] = None
            if "modulation" not in ch:
                ch["modulation"] = ""

        return channels

    # -- Value parsers --
    @staticmethod
    def _parse_number(value: str) -> float:
        if not value:
            return 0.0
        m = re.search(r"(-?\d+(?:\.\d+)?)", value.replace(',', ''))
        if not m:
            return 0.0
        try:
            return float(m.group(1))
        except Exception:
            return 0.0

    @staticmethod
    def _parse_int(value: str) -> int:
        if not value:
            return 0
        m = re.search(r"(\d+)", value)
        if not m:
            return 0
        try:
            return int(m.group(1))
        except Exception:
            return 0

    @staticmethod
    def _format_freq(freq_str: str) -> str:
        if not freq_str:
            return ""
        s = freq_str.strip()
        # attempt to extract the first numeric token
        m = re.search(r"(-?\d+(?:\.\d+)?)", s.replace(',', ''))
        if not m:
            return s
        num = float(m.group(1))
        # if the number looks like Hz (very large), convert to MHz
        if abs(num) > 1e6:
            mhz = num / 1e6
        else:
            mhz = num
        try:
            return f"{int(mhz)} MHz"
        except Exception:
            return s
