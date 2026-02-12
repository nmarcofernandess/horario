"""FastAPI app — API REST para EscalaFlow"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.backend.src.infrastructure.database.setup import init_db

from apps.backend.routes import employees, sectors, preferences, scale, shifts, exceptions, demand_profile, config, weekday_template, sunday_rotation


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
app.include_router(weekday_template.router)
app.include_router(sunday_rotation.router)


@app.get("/health")
def health():
    return {"status": "ok"}
