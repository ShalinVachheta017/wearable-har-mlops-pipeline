"""
FastAPI Inference API for HAR Model
====================================

This API provides RESTful endpoints for activity recognition inference.

Endpoints:
    GET  /health          - Health check
    GET  /api/health      - Health check (alias)
    GET  /model/info      - Model information
    POST /predict         - Single window prediction
    POST /predict/batch   - Batch prediction

Usage:
    

Author: MLOps Pipeline
Date: December 11, 2025
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    "models/pretrained/fine_tuned_model_1dcnnbilstm.keras",
    "D:\study apply\ML Ops\MasterArbeit_MLops\models\pretrained\fine_tuned_model_1dcnnbilstm.keras"
)
CONFIG_PATH = os.environ.get(
    "CONFIG_PATH",
    "config/pipeline_config.yaml",
)

# Activity class mapping
ACTIVITY_CLASSES: Dict[int, str] = {
    0: "ear_rubbing",
    1: "forehead_rubbing",
    2: "hair_pulling",
    3: "hand_scratching",
    4: "hand_tapping",
    5: "knuckles_cracking",
    6: "nail_biting",
    7: "nape_rubbing",
    8: "sitting",
    9: "smoking",
    10: "standing",
}

# Global model reference
_model = None
_model_info = None

# ============================================================================
# Pydantic Models
# ============================================================================

class SensorReading(BaseModel):
    Ax: float = Field(..., description="Accelerometer X (m/s²)")
    Ay: float = Field(..., description="Accelerometer Y (m/s²)")
    Az: float = Field(..., description="Accelerometer Z (m/s²)")
    Gx: float = Field(..., description="Gyroscope X (deg/s)")
    Gy: float = Field(..., description="Gyroscope Y (deg/s)")
    Gz: float = Field(..., description="Gyroscope Z (deg/s)")


class PredictionRequest(BaseModel):
    window: List[List[float]] = Field(
        ...,
        description="200x6 window of sensor data [[Ax,Ay,Az,Gx,Gy,Gz], ...]",
    )
    return_probabilities: bool = Field(
        default=False,
        description="Whether to return probability distribution",
    )

    @field_validator("window")
    @classmethod
    def validate_window(cls, v):
        if len(v) != 200:
            raise ValueError(f"Window must have 200 timesteps, got {len(v)}")
        if any(len(row) != 6 for row in v):
            raise ValueError("Each timestep must have 6 sensor values")
        return v


class BatchPredictionRequest(BaseModel):
    windows: List[List[List[float]]] = Field(
        ...,
        description="List of 200x6 windows",
    )
    return_probabilities: bool = Field(
        default=False,
        description="Whether to return probability distributions",
    )


class PredictionResponse(BaseModel):
    activity: str
    activity_id: int
    confidence: float
    probabilities: Optional[Dict[str, float]] = None
    timestamp: str
    model_version: str


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    total_windows: int
    processing_time_ms: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    timestamp: str
    uptime_seconds: float


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    input_shape: List[int]
    output_classes: int
    activity_classes: Dict[int, str]
    loaded_at: str

# ============================================================================
# Model Loading
# ============================================================================

def load_model():
    global _model, _model_info

    try:
        import tensorflow as tf
        tf.get_logger().setLevel("ERROR")

        model_path = Path(MODEL_PATH)
        if not model_path.exists():
            logger.error(f"Model not found: {model_path}")
            raise FileNotFoundError(f"Model not found: {model_path}")

        logger.info(f"Loading model from: {model_path}")
        _model = tf.keras.models.load_model(model_path)

        _model_info = {
            "model_name": "1D-CNN-BiLSTM HAR",
            "model_version": "1.0.0",
            "input_shape": list(_model.input_shape[1:]),  # (200, 6)
            "output_classes": _model.output_shape[-1],    # 11
            "loaded_at": datetime.now().isoformat(),
        }

        logger.info(f"Model loaded successfully: {_model_info}")
        return True

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False

# ============================================================================
# Startup/Shutdown
# ============================================================================

_start_time = datetime.now()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting HAR Inference API...")
    load_model()
    yield
    logger.info("👋 Shutting down HAR Inference API...")

# ============================================================================
# App
# ============================================================================

app = FastAPI(
    title="HAR Inference API",
    description="REST API for Human Activity Recognition using 1D-CNN-BiLSTM",
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

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "HAR Inference API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "health_alias": "/api/health",  # ADDED (clarity)
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy" if _model is not None else "unhealthy",
        model_loaded=_model is not None,
        timestamp=datetime.now().isoformat(),
        uptime_seconds=(datetime.now() - _start_time).total_seconds(),
    )

# ADDED: alias endpoint so CD/others can also call /api/health safely
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check_alias():
    return await health_check()

@app.get("/model/info", response_model=ModelInfoResponse, tags=["Model"])
async def model_info():
    if _model is None or _model_info is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return ModelInfoResponse(
        model_name=_model_info["model_name"],
        model_version=_model_info["model_version"],
        input_shape=_model_info["input_shape"],
        output_classes=_model_info["output_classes"],
        activity_classes=ACTIVITY_CLASSES,
        loaded_at=_model_info["loaded_at"],
    )

@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest):
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        window = np.array(request.window).reshape(1, 200, 6)
        probabilities = _model.predict(window, verbose=0)[0]
        predicted_class = int(np.argmax(probabilities))
        confidence = float(probabilities[predicted_class])

        response = PredictionResponse(
            activity=ACTIVITY_CLASSES[predicted_class],
            activity_id=predicted_class,
            confidence=confidence,
            probabilities=None,
            timestamp=datetime.now().isoformat(),
            model_version=_model_info["model_version"],
        )

        if request.return_probabilities:
            response.probabilities = {
                ACTIVITY_CLASSES[i]: float(p)
                for i, p in enumerate(probabilities)
            }

        return response

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
async def predict_batch(request: BatchPredictionRequest):
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        import time
        start_time = time.time()

        windows = np.array(request.windows)
        if len(windows.shape) != 3 or windows.shape[1:] != (200, 6):
            raise ValueError(f"Invalid shape: {windows.shape}, expected (N, 200, 6)")

        all_probabilities = _model.predict(windows, verbose=0)

        predictions = []
        for probs in all_probabilities:
            predicted_class = int(np.argmax(probs))
            confidence = float(probs[predicted_class])

            pred = PredictionResponse(
                activity=ACTIVITY_CLASSES[predicted_class],
                activity_id=predicted_class,
                confidence=confidence,
                probabilities=None,
                timestamp=datetime.now().isoformat(),
                model_version=_model_info["model_version"],
            )

            if request.return_probabilities:
                pred.probabilities = {
                    ACTIVITY_CLASSES[j]: float(p)
                    for j, p in enumerate(probs)
                }

            predictions.append(pred)

        processing_time = (time.time() - start_time) * 1000

        return BatchPredictionResponse(
            predictions=predictions,
            total_windows=len(windows),
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)