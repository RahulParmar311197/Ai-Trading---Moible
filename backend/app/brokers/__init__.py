"""Provider-neutral broker contracts and explicitly gated adapters."""

from .auth import BrokerAuthError, BrokerToken, DhanOAuth, UpstoxOAuth
from .base import Account, Broker, BrokerOrder, BrokerOrderStatus, BrokerPosition
from .catalogue import InstrumentCatalogueError, dhan_catalogue, resolver_from_catalogue, upstox_catalogue
from .dhan import DhanBroker
from .http import BrokerHTTPError, LiveBrokerDisabled
from .idempotency import BrokerIdempotencyStore, IdempotencyConflict, IdempotentBroker
from .order_config import BrokerInstrument, ExchangeSegment, InstrumentResolver, OrderValidity, ProductType
from .session import BrokerSession, BrokerSessionState, StaticTokenBrokerSession
from .upstox import UpstoxBroker

__all__ = [
    "Account",
    "Broker",
    "BrokerOrder",
    "BrokerOrderStatus",
    "BrokerPosition",
    "BrokerIdempotencyStore",
    "IdempotencyConflict",
    "IdempotentBroker",
    "BrokerHTTPError",
    "LiveBrokerDisabled",
    "BrokerAuthError",
    "BrokerToken",
    "UpstoxOAuth",
    "DhanOAuth",
    "DhanBroker",
    "UpstoxBroker",
    "BrokerInstrument",
    "ExchangeSegment",
    "InstrumentResolver",
    "OrderValidity",
    "ProductType",
    "InstrumentCatalogueError",
    "upstox_catalogue",
    "dhan_catalogue",
    "resolver_from_catalogue",
    "BrokerSession",
    "BrokerSessionState",
    "StaticTokenBrokerSession",
]
