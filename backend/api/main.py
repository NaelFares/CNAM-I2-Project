"""FastAPI entrypoint for the standalone HTTP backend."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import config

from backend.api.routes.auth import router as auth_router
from backend.api.routes.dashboard import router as dashboard_router
from backend.api.routes.geocode import router as geocode_router
from backend.api.routes.matches import router as matches_router
from backend.api.routes.profile import router as profile_router
from backend.api.routes.rides import router as rides_router
from backend.api.routes.schedule import router as schedule_router

app = FastAPI(title=f"{config.APP_NAME} API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "HTTP_ERROR", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": "INTERNAL_ERROR", "message": str(exc)},
    )


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(geocode_router)
app.include_router(schedule_router)
app.include_router(rides_router)
app.include_router(matches_router)
app.include_router(dashboard_router)
