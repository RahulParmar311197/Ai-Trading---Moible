from decimal import Decimal

from app import main
from app.config import settings


def _configure_execution(monkeypatch, *, sandbox: bool) -> None:
    monkeypatch.setattr(settings, "execution_broker", "upstox")
    monkeypatch.setattr(settings, "execution_sandbox", sandbox)
    monkeypatch.setattr(settings, "execution_confirmation_phrase", "CONFIRM LIVE TRADING")
    monkeypatch.setattr(settings, "trading_session_id", "session-1")
    monkeypatch.setattr(settings, "execution_max_order_notional", Decimal("100000"))
    monkeypatch.setattr(settings, "execution_max_position_quantity", 100)
    monkeypatch.setattr(settings, "execution_max_daily_loss", Decimal("5000"))
    monkeypatch.setattr(settings, "upstox_sandbox_access_token", "sandbox-token")
    monkeypatch.setattr(settings, "upstox_access_token", "live-token")
    monkeypatch.setattr(settings, "execution_allow_live_orders", True)
    monkeypatch.setattr(settings, "execution_allow_sandbox_orders", False)


def test_application_execution_builder_rejects_production_runtime(monkeypatch):
    _configure_execution(monkeypatch, sandbox=False)
    broker_constructed = False

    def fake_broker(*args, **kwargs):
        nonlocal broker_constructed
        broker_constructed = True
        raise AssertionError("production broker must not be constructed")

    monkeypatch.setattr(main, "UpstoxBroker", fake_broker)
    runtime, error = main._build_execution_runtime()

    assert runtime is None
    assert "Production broker execution is not enabled" in error
    assert broker_constructed is False


def test_application_sandbox_builder_forces_live_mutations_off(monkeypatch):
    _configure_execution(monkeypatch, sandbox=True)
    captured = {}

    class BrokerStub:
        def __init__(self, *args, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(main, "UpstoxBroker", BrokerStub)
    monkeypatch.setattr(main, "build_execution_runtime", lambda broker, **kwargs: (broker, kwargs))

    runtime, error = main._build_execution_runtime()

    assert error is None
    assert runtime is not None
    assert captured["sandbox"] is True
    assert captured["allow_live_orders"] is False
    assert captured["allow_sandbox_orders"] is False
