"""FastAPI y archivos estáticos para la demo de Última Ventana."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ultima_ventana_ml import PredictionInputError

from .demo_service import DEFAULT_LOCATION, FORECAST_PRESETS, RAIN_TRIGGER_THRESHOLD_MM, analyze_demo
from .model_service import DISCLAIMER, ModelService
from .schemas import DemoAnalysisRequest, DemoAnalysisResponse, FeatureInput, PredictionResponse

STATIC_DIR = Path(__file__).with_name("static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model_service = ModelService.load()
    yield


app = FastAPI(
    title="Última Ventana Demo API",
    version="0.1.0",
    description="Inferencia demostrativa sobre rutas, terreno y pronóstico simulados.",
    lifespan=lifespan,
)


@app.exception_handler(PredictionInputError)
async def prediction_input_error(_: Request, error: PredictionInputError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(error)})


def _model(request: Request) -> ModelService:
    return request.app.state.model_service


@app.get("/api/health")
async def health(request: Request) -> dict[str, object]:
    model = _model(request)
    return {
        "status": "ok",
        "model_loaded": True,
        "model_version": model.metadata["model_version"],
        "feature_schema_version": model.metadata["feature_schema_version"],
    }


@app.get("/api/demo/config")
async def demo_config(request: Request) -> dict[str, object]:
    model = _model(request)
    return {
        "mode": "SYNTHETIC_DEMO",
        "model_version": model.metadata["model_version"],
        "default_location": DEFAULT_LOCATION,
        "rain_trigger_threshold_mm": RAIN_TRIGGER_THRESHOLD_MM,
        "forecast_presets": FORECAST_PRESETS,
        "disclaimer": DISCLAIMER,
    }


@app.post("/api/predict", response_model=PredictionResponse)
async def predict(payload: FeatureInput, request: Request) -> dict[str, object]:
    return _model(request).predict(payload.model_dump())


@app.post("/api/demo/analyze", response_model=DemoAnalysisResponse)
async def analyze(payload: DemoAnalysisRequest, request: Request) -> dict[str, object]:
    return analyze_demo(_model(request), payload)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
