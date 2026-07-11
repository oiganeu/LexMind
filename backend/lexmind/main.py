"""FastAPI application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from lexmind.constants import APP_NAME
from lexmind.lifecycle import shutdown, startup
from lexmind.version import get_version


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    startup()
    yield
    shutdown()


app = FastAPI(title=APP_NAME, lifespan=lifespan)


@app.get("/")
def health() -> dict[str, str]:
    return {"name": APP_NAME, "status": "ok", "version": get_version()}
