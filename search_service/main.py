"""
Workisto search service — a small, async FastAPI app that owns the read-heavy
provider-search hot path.

It is a SEPARATE service (its own container / uvicorn process), not a Django app:
it talks to the same Postgres over asyncpg for higher throughput per instance,
and trusts requests via a short-lived JWT that Django signs (ADR 0001). The
write side (bookings, payments, the transactional flows) stays in Django.
"""

from contextlib import asynccontextmanager

import asyncpg
from fastapi import Depends, FastAPI, Query

from . import config
from .auth import verify_token
from .queries import search_providers


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(
        dsn=config.database_url(), min_size=1, max_size=5,
    )
    try:
        yield
    finally:
        await app.state.pool.close()


app = FastAPI(title="Workisto Search Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/search/providers")
async def search(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    category: str | None = Query(None),
    mode: str | None = Query(None),
    radius_km: float = Query(10.0, gt=0, le=50),
    _claims: dict = Depends(verify_token),
):
    results = await search_providers(
        app.state.pool, lat=lat, lng=lng, category=category,
        mode=mode, radius_km=radius_km,
    )
    return {"count": len(results), "results": results}
