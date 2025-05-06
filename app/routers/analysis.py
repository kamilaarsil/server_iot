import numpy as np
import pandas as pd
import joblib
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from tensorflow import keras
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.metrics import MeanAbsoluteError
from datetime import datetime

from ..database import Sessionlocal
from ..models import DataAnalysis, RecommendationLog

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

# Load once at module level
model = keras.models.load_model('models/prediction_model.h5', compile=False)
scaler_X = joblib.load('models/scaler_X.pkl')
scaler_y = joblib.load('models/scaler_y.pkl')

# Compile the model
model.compile(optimizer=Adam(),
              loss=MeanSquaredError(),
              metrics=[MeanAbsoluteError()])

def recommend_optimal_T_set(model, scaler_X, scaler_y, real_time_data, current_T_set, current_actual_power):
    comfort_range = range(17, 21)
    feature_order = scaler_X.feature_names_in_ if hasattr(scaler_X, 'feature_names_in_') else ['T_set', 'H_indoor', 'T_outdoor', 'H_outdoor', 'N']
    candidates = []

    for T_set_candidate in comfort_range:
        if T_set_candidate == current_T_set:
            continue

        # Build feature vector with correct order
        feature_values = [
            T_set_candidate if name == 'T_set' else real_time_data.get(name, 0)
            for name in feature_order
        ]
        features_df = pd.DataFrame([feature_values], columns=feature_order)

        features_scaled = scaler_X.transform(features_df)
        pred_power_scaled = model.predict(features_scaled, verbose=0)
        pred_power = scaler_y.inverse_transform(pred_power_scaled)[0][0]

        if pred_power < current_actual_power:
            candidates.append((T_set_candidate, pred_power))

    if candidates:
        optimal_T_set, optimal_power = min(candidates, key=lambda x: x[1])
        saving = current_actual_power - optimal_power
        recommendation = f"Set AC temperature to {optimal_T_set}°C to save approximately {saving:.2f} Watts."
    else:
        optimal_T_set = current_T_set
        optimal_power = current_actual_power
        saving = 0
        recommendation = "Current setting is already optimal."

    return {
        'optimal_T_set': int(optimal_T_set),
        'predicted_optimal_power': round(float(optimal_power), 2),
        'power_saving': round(float(saving), 2),
        'recommendation': recommendation
    }

@router.get("/recommendation-model", status_code=status.HTTP_200_OK)
async def get_model_recommendation(db: Session = Depends(get_db)):
    latest_data = db.query(DataAnalysis).order_by(DataAnalysis.timestamp.desc()).first()

    if not latest_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No data available"
        )

    # Prepare real-time input from database
    real_time_data = {
        'H_indoor': latest_data.indoor_humidity,
        'T_outdoor': latest_data.outdoor_temperature,
        'H_outdoor': latest_data.outdoor_humidity,
        'N': latest_data.occupant,
    }

    # Extract current T_set and power (past measurement)
    current_T_set = latest_data.ac_temperature
    current_actual_power = latest_data.power

    result = recommend_optimal_T_set(
        model, scaler_X, scaler_y,
        real_time_data, current_T_set, current_actual_power
    )

    # ✅ Only log if the T_set has changed
    last_log = (
        db.query(RecommendationLog)
        .order_by(RecommendationLog.timestamp.desc())
        .first()
    )

    if not last_log or last_log.current_t_set != current_T_set:
        log = RecommendationLog(
            timestamp=datetime.now(),
            current_t_set=current_T_set,
            current_power=current_actual_power,
            optimal_t_set=result["optimal_T_set"],
            predicted_power=result["predicted_optimal_power"],
            estimated_saving=result["power_saving"],
            recommendation_text=result["recommendation"]
        )
        db.add(log)
        db.commit()

    return {
        "timestamp": latest_data.timestamp.strftime("%Y-%m-%d %H:%M"),
        "current_T_set": current_T_set,
        "current_power": current_actual_power,
        "optimal_T_set": result["optimal_T_set"],
        "predicted_power": result["predicted_optimal_power"],
        "estimated_saving": result["power_saving"],
        "recommendation": result["recommendation"]
    }

@router.get("/recommendations", status_code=status.HTTP_200_OK)
async def get_recommendations(db: Session = Depends(get_db)):
    latest_data = db.query(DataAnalysis).order_by(DataAnalysis.timestamp.desc()).first()

    if not latest_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No data available"
        )

    recommendations = []

    if latest_data.occupant == 0:
        recommendations.append({"icon": "🚨", "message": "The room is empty - Turn off lights and AC to save energy."})

    if latest_data.occupant < 5:
        recommendations.append({"icon": "💡", "message": "Low occupancy detected - Consider dimming the lights."})

    if latest_data.power > 2500:
        recommendations.append({"icon": "⚠️", "message": f"High power consumption detected ({latest_data.power} Watts)."})

    if latest_data.indoor_temperature < 18 or latest_data.indoor_temperature > 28:
        recommendations.append({"icon": "🌡️", "message": f"Room temperature is uncomfortable: {latest_data.indoor_temperature}°C."})

    if latest_data.indoor_humidity < 30 or latest_data.indoor_humidity > 60:
        recommendations.append({"icon": "💧", "message": f"Room humidity is out of comfort range: {latest_data.indoor_humidity}%."})

    return {
        "timestamp": latest_data.timestamp.strftime("%Y-%m-%d %H:%M"),
        "recommendations": recommendations,
    }

@router.get("/recommendation-log", status_code=status.HTTP_200_OK)
async def get_recommendation_logs(page: int = 1, db: Session = Depends(get_db)):
    limit = 10
    offset = (page - 1) * limit

    logs = (
        db.query(RecommendationLog)
        .order_by(RecommendationLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total_records = db.query(RecommendationLog).count()
    total_pages = (total_records + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "data": [
            {
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M"),
                "current_tset": log.current_t_set,
                "optimal_tset": log.optimal_t_set,
                "predicted_power": log.predicted_power,
                "estimated_saving": log.estimated_saving,
                "recommendation": log.recommendation_text
            }
            for log in logs
        ]
    }
