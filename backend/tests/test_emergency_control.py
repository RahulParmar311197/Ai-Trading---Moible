from datetime import datetime, timezone

import pytest

from app.execution.emergency_control import EmergencyControlError, PostgresEmergencyControlStore


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
        return {
            "active": params["active"],
            "reason": params["reason"],
            "updated_at": datetime.now(timezone.utc),
        }


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
    row = {"active": True, "reason": "operator stop", "updated_at": timestamp}
    state = PostgresEmergencyControlStore(FakeExecutor(row)).get_state()
    assert state.active is True
    assert state.reason == "operator stop"
    assert state.updated_at == timestamp


def test_set_active_persists_only_non_empty_reason():
    executor = FakeExecutor()
    store = PostgresEmergencyControlStore(executor)
    state = store.set_active(True, "  operator stop  ")
    assert state.active is True
    assert state.reason == "operator stop"
    assert executor.writes == [{"active": True, "reason": "operator stop"}]
    with pytest.raises(EmergencyControlError, match="reason must be non-empty"):
        store.set_active(True, "   ")


def test_write_failure_fails_closed():
    with pytest.raises(EmergencyControlError, match="could not be persisted"):
        PostgresEmergencyControlStore(FakeExecutor(fail_write=True)).set_active(True, "operator stop")
