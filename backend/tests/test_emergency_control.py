from datetime import datetime, timezone

import pytest

from app.brokers.base import BrokerAuthentication
from app.brokers.idempotency import BrokerIdempotencyStore
from app.execution import ControlledBrokerExecution, ControlledExecutionError, DeterministicExecutionGate, RiskLimits
from app.execution.emergency_control import EmergencyControlError, EmergencyControlState, PostgresEmergencyControlStore


class FakeExecutor:
    def __init__(self, row=None, *, fail_fetch=False, fail_write=False):
        self.row = row
        self.fail_fetch = fail_fetch
        self.fail_write = fail_write
        self.writes = []

    def fetch_one(self, query, params):
        if self.fail_fetch:
            raise ConnectionError("database unavailable")
        return self.row

    def execute_returning(self, query, params):
        if self.fail_write:
            raise ConnectionError("database unavailable")
        self.writes.append(params)
        return {"active": params["active"], "reason": params["reason"], "updated_at": datetime.now(timezone.utc)}


def test_missing_emergency_state_fails_closed():
    with pytest.raises(EmergencyControlError, match="missing or invalid"):
        PostgresEmergencyControlStore(FakeExecutor()).get_state()


def test_database_read_failure_fails_closed():
    with pytest.raises(EmergencyControlError, match="state unavailable"):
        PostgresEmergencyControlStore(FakeExecutor(fail_fetch=True)).get_state()


def test_invalid_emergency_state_fails_closed():
    row = {"active": "unknown", "reason": "x", "updated_at": datetime.now(timezone.utc)}
    with pytest.raises(EmergencyControlError, match="missing or invalid"):
        PostgresEmergencyControlStore(FakeExecutor(row)).get_state()


def test_emergency_state_round_trips():
    timestamp = datetime.now(timezone.utc)
    state = PostgresEmergencyControlStore(
        FakeExecutor({"active": True, "reason": "operator stop", "updated_at": timestamp})
    ).get_state()
    assert state == EmergencyControlState(True, "operator stop", timestamp)


def test_set_active_persists_only_non_empty_reason():
    executor = FakeExecutor()
    state = PostgresEmergencyControlStore(executor).set_active(True, "  operator stop  ")
    assert state.active is True
    assert state.reason == "operator stop"
    assert executor.writes == [{"active": True, "reason": "operator stop"}]
    with pytest.raises(EmergencyControlError, match="reason must be non-empty"):
        PostgresEmergencyControlStore(executor).set_active(True, "   ")


def test_write_failure_fails_closed():
    with pytest.raises(EmergencyControlError, match="could not be persisted"):
        PostgresEmergencyControlStore(FakeExecutor(fail_write=True)).set_active(True, "operator stop")


class FakeBroker:
    async def authenticate(self):
        return BrokerAuthentication(provider="fake", account_id="account-1", authenticated=True)


class MemoryEmergencyStore:
    def __init__(self, active=True):
        self.state = EmergencyControlState(active, "persisted emergency stop" if active else "cleared", datetime.now(timezone.utc))

    def get_state(self):
        return self.state

    def set_active(self, active, reason):
        self.state = EmergencyControlState(active, reason, datetime.now(timezone.utc))
        return self.state


def build_execution(store):
    return ControlledBrokerExecution(
        FakeBroker(),
        DeterministicExecutionGate(RiskLimits()),
        confirmation_phrase="ENABLE LIVE",
        idempotency_store=BrokerIdempotencyStore(),
        emergency_control=store,
    )


@pytest.mark.asyncio
async def test_startup_keeps_kill_switch_active_when_persisted_stop_exists():
    execution = build_execution(MemoryEmergencyStore(active=True))
    await execution.startup()
    assert execution.started
    assert execution.kill_switch_active
    with pytest.raises(ControlledExecutionError, match="durable emergency stop is active"):
        execution.activate("ENABLE LIVE")


@pytest.mark.asyncio
async def test_emergency_stop_reset_requires_explicit_confirmation_and_stays_deactivated():
    store = MemoryEmergencyStore(active=True)
    execution = build_execution(store)
    await execution.startup()
    with pytest.raises(ControlledExecutionError, match="explicit live-execution confirmation required"):
        execution.clear_emergency_stop("WRONG")
    execution.clear_emergency_stop("ENABLE LIVE", "operator reviewed state")
    assert store.state.active is False
    assert execution.kill_switch_active
    assert not execution.active


@pytest.mark.asyncio
async def test_emergency_stop_persistence_failure_keeps_local_stop_active():
    class FailingStore(MemoryEmergencyStore):
        def set_active(self, active, reason):
            raise EmergencyControlError("persistence failed")

    execution = build_execution(FailingStore(active=False))
    with pytest.raises(ControlledExecutionError, match="could not be persisted"):
        execution.trip_kill_switch("operator stop")
    assert execution.kill_switch_active
    assert not execution.active
