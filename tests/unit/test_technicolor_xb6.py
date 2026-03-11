import types

from app.drivers.technicolor_xb6 import XB6Driver


class DummyResponse:
    def raise_for_status(self):
        return None


def test_login_success(monkeypatch):
    d = XB6Driver("https://10.0.0.1", "admin", "happy123")

    # Replace session.post with a dummy callable that returns a DummyResponse
    d._session.post = lambda *args, **kwargs: DummyResponse()
    d._session.verify = False

    # Should not raise
    d.login()


def test_get_device_info_returns_defaults(monkeypatch):
    d = XB6Driver("https://10.0.0.1", "admin", "happy123")
    # Simulate status page fetch failing
    d._session.get = lambda *args, **kwargs: (_ for _ in ()).throw(Exception("network"))
    info = d.get_device_info()
    assert info.get("manufacturer") == "Technicolor"
    assert info.get("model") == "CGM4140COM"
