from datetime import datetime, time
from decimal import Decimal
from pydantic import BaseModel
from app.market.models import Candle

class SessionWindow(BaseModel):
    name: str
    start: time
    end: time

class SessionLevels(BaseModel):
    name: str
    high: Decimal
    low: Decimal
    start: datetime
    end: datetime

def in_window(ts: datetime, window: SessionWindow) -> bool:
    local = ts.timetz().replace(tzinfo=None)
    if window.start <= window.end:
        return window.start <= local <= window.end
    return local >= window.start or local <= window.end

def session_levels(candles: list[Candle], window: SessionWindow) -> SessionLevels | None:
    selected = [c for c in candles if in_window(c.timestamp, window)]
    if not selected:
        return None
    return SessionLevels(name=window.name, high=max(c.high for c in selected), low=min(c.low for c in selected), start=selected[0].timestamp, end=selected[-1].timestamp)

# UTC windows are intentionally explicit; callers can define exchange-local windows.
ICT_LONDON = SessionWindow(name="LONDON", start=time(7, 0), end=time(10, 0))
ICT_NEW_YORK = SessionWindow(name="NEW_YORK", start=time(12, 0), end=time(15, 0))
