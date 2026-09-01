from fastapi import FastAPI

from app.api.market_data import router as market_data_router
from app.api.market_stream import router as market_stream_router
from app.api.markets import router as markets_router

app = FastAPI(title="AI Trading Platform API", version="0.1.0")
app.include_router(markets_router)
app.include_router(market_data_router)
app.include_router(market_stream_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
