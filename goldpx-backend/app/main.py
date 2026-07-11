import time
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.api import api_router

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger("goldpx")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production backend for GOLD Px \u2014 Wedding Lighting, Event Decoration, "
                 "Pixel LED Installations, Stage & Architectural Lighting, Smart RGB Systems.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---- Middleware ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start)
    return response


# ---- Static files (local upload backend) ----
upload_dir = Path(settings.LOCAL_UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(upload_dir)), name="static")

# ---- Routers ----
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/", tags=["Health"])
def root():
    return {"message": "GOLD Px API is running", "docs": "/docs"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
