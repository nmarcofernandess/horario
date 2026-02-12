"""FastAPI app — API REST para EscalaFlow"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.database.setup import init_db

from api.routes import employees, sectors, preferences, scale, shifts, exceptions, demand_profile, config


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    # cleanup if needed


app = FastAPI(
    title="EscalaFlow API",
    description="API REST para gestão de escala de trabalho",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router)
app.include_router(sectors.router)
app.include_router(preferences.router)
app.include_router(scale.router)
app.include_router(shifts.router)
app.include_router(exceptions.router)
app.include_router(demand_profile.router)
app.include_router(config.router)


@app.get("/health")
def health():
    return {"status": "ok"}
