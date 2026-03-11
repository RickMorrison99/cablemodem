"""Technicolor XB6 (CGM4140COM) driver (scaffold).

This is an initial scaffold copied from the Arris CM3500B driver login flow
as requested. Implement parsing and page selectors specific to the XB6
before marking implementation complete.
"""

import logging
import re

import requests
from bs4 import BeautifulSoup

from .base import ModemDriver

log = logging.getLogger("docsis.driver.technicolor_xb6")


class XB6Driver(ModemDriver):
    """Scaffold driver for Technicolor XB6 (CGM4140COM).

    Authentication and status scraping are currently copied from the
    Arris CM3500B driver. Update endpoint paths and parsing logic to
    match the XB6 web UI.
    """

    def __init__(self, url: str, user: str, password: str):
        # Many modem web UIs expect HTTPS; upgrade silently if needed
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]
            log.info("XB6 driver upgraded URL to %s", url)
        super().__init__(url, user, password)
        self._session = requests.Session()
        # Local testing often uses self-signed certs; disable verification by default
        self._session.verify = False

    def login(self) -> None:
        """Authenticate via form POST (copied from CM3500 pattern).

        Retries once with a fresh connection on ConnectionError.
        """
        for attempt in range(2):
            try:
                r = self._session.post(
                    f"{self._url}/cgi-bin/login_cgi",
                    data={"username": self._user, "password": self._password},
                    timeout=30,
                )
                r.raise_for_status()
                log.info("XB6 auth OK")
                return
            except requests.ConnectionError:
                if attempt == 0:
                    log.warning("XB6 connection lost, retrying with fresh session")
                    self._session.close()
                    self._session = requests.Session()
                    self._session.verify = False
                    continue
                raise RuntimeError("XB6 authentication failed: connection refused after retry")
            except requests.RequestException as e:
                raise RuntimeError(f"XB6 authentication failed: {e}")

    def get_docsis_data(self) -> dict:
        """Placeholder: return empty channel structures until parser is implemented."""
        # TODO: implement HTML scraping and parsing of downstream/upstream tables
        return {"channelDs": {"docsis30": [], "docsis31": []}, "channelUs": {"docsis30": [], "docsis31": []}}

    def get_device_info(self) -> dict:
        """Attempt to scrape a status page for device info; fallback to static values."""
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

            model = info.get("Hardware Model", "CGM4140COM")
            result = {"manufacturer": "Technicolor", "model": model, "sw_version": info.get("Software Version", "")}
            return result
        except Exception:
            return {"manufacturer": "Technicolor", "model": "CGM4140COM", "sw_version": ""}

    def get_connection_info(self) -> dict:
        """Retrieve provisioned speeds or other connection info. Placeholder."""
        # TODO: implement based on XB6 UI (may require different endpoint)
        return {}

    def _fetch_status_page(self) -> BeautifulSoup:
        """Fetch and parse the modem status page (placeholder path).

        Update the endpoint path if XB6 uses a different status page.
        """
        try:
            r = self._session.get(f"{self._url}/cgi-bin/status_cgi", timeout=30)
            r.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"XB6 status page retrieval failed: {e}")
        return BeautifulSoup(r.text, "html.parser")


    # Minimal helpers copied from CM3500 for later use
    @staticmethod
    def _parse_number(value: str) -> float:
        if not value:
            return 0.0
        parts = value.strip().split()
        try:
            return float(parts[0])
        except (ValueError, IndexError):
            return 0.0

    @staticmethod
    def _format_freq(freq_str: str) -> str:
        if not freq_str:
            return ""
        parts = freq_str.strip().split()
        try:
            mhz = float(parts[0])
            return f"{int(mhz)} MHz"
        except (ValueError, IndexError):
            return freq_str
