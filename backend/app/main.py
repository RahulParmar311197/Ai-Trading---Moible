from fastapi import FastAPI

from app.api.markets import router as markets_router

app = FastAPI(title="AI Trading Platform API", version="0.1.0")
app.include_router(markets_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
