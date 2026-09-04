from __future__ import annotations

from .controlled import ControlledBrokerExecution, ControlledExecutionError
from .emergency_control import EmergencyControlError


class FailClosedControlledBrokerExecution(ControlledBrokerExecution):
    """Controlled execution wrapper that makes persisted emergency-stop state authoritative at startup."""

    async def startup(self):
        # Establish the safety invariant before contacting the broker: an active
        # persisted emergency stop must make startup unavailable, not merely
        # leave a locally armed kill switch while reporting readiness.
        if self._emergency_control is not None:
            try:
                emergency_state = self._emergency_control.get_state()
            except EmergencyControlError as exc:
                self._audit("STARTUP_REJECTED", "", "durable emergency control state unavailable")
                self._started = False
                self._activated = False
                self._kill_switch = True
                raise ControlledExecutionError("durable emergency control state unavailable") from exc
            if emergency_state.active:
                self._audit("STARTUP_REJECTED", "", "durable emergency stop is active")
                self._started = False
                self._activated = False
                self._kill_switch = True
                raise ControlledExecutionError("durable emergency stop is active")
        return await super().startup()

    def clear_emergency_stop(self, confirmation: str, reason: str = "manual reset") -> None:
        # Clearing a persisted emergency stop must remain possible after a
        # fail-closed startup rejection. Clearing never authenticates, starts,
        # or activates execution; startup + explicit activation are still
        # required before any order can be submitted.
        if confirmation != self._confirmation_phrase:
            self._audit("EMERGENCY_RESET_REJECTED", "", "explicit confirmation did not match")
            raise ControlledExecutionError("explicit live-execution confirmation required")
        if not reason.strip():
            raise ValueError("emergency reset reason must be non-empty")
        if self._emergency_control is None:
            raise ControlledExecutionError("durable emergency control is not configured")
        try:
            self._emergency_control.set_active(False, reason)
        except EmergencyControlError as exc:
            self._audit("EMERGENCY_RESET_FAILED", "", "durable emergency stop could not be cleared")
            raise ControlledExecutionError("durable emergency stop could not be cleared") from exc
        self._started = False
        self._activated = False
        self._kill_switch = True
        self._audit("EMERGENCY_STOP_CLEARED", "", reason)
        self._audit("EXECUTION_DEACTIVATED", "", "emergency stop cleared; explicit startup and activation remain required")
