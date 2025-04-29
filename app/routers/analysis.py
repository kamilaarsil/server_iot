import numpy as np
import joblib
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from tensorflow import keras

from ..database import Sessionlocal
from ..models import DataAnalysis

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
model = keras.models.load_model('models/power_prediction_model.h5', compile=False)
scaler_X = joblib.load('models/scaler_X.pkl')
scaler_y = joblib.load('models/scaler_y.pkl')


# Compile the model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.metrics import MeanAbsoluteError

model.compile(optimizer=Adam(),
              loss=MeanSquaredError(),
              metrics=[MeanAbsoluteError()])

def recommend_optimal_T_set(model, scaler_X, scaler_y, real_time_data, current_T_set, current_actual_power):
    comfort_range = range(17, 22)
    candidates = []

    for T_set_candidate in comfort_range:
        if T_set_candidate == current_T_set:
            continue

        features = np.array([
            T_set_candidate,
            real_time_data['H_indoor'],
            real_time_data['T_outdoor'],
            real_time_data['H_outdoor'],
            real_time_data['N']
        ]).reshape(1, -1)

        features_scaled = scaler_X.transform(features)
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
    # Ambil data terbaru
    latest_data = db.query(DataAnalysis).order_by(DataAnalysis.timestamp.desc()).first()

    if not latest_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No data available"
        )

    # Rule-based recommendations
    recommendations = []

    # Rule 1: Matikan AC jika ruangan kosong
    if latest_data.occupant == 0:
        recommendations.append(
            {
                "icon": "🚨",
                "message": "Ruangan kosong - Matikan AC untuk menghemat energi.",
            }
        )

    # Rule 2: Rekomendasikan ventilasi alami jika suhu luar nyaman
    if (latest_data.outdoor_temperature - latest_data.indoor_temperature) > 3:
        recommendations.append(
            {
                "icon": "🌬️",
                "message": f"Naikkan suhu AC untuk menghemat energi. Suhu luar: {latest_data.outdoor_temperature}°C.",
            }
        )

    # Rule 3: Kurangi intensitas lampu jika okupansi rendah
    if latest_data.occupant < 5:
        recommendations.append(
            {
                "icon": "💡",
                "message": "Okupansi rendah - Kurangi intensitas lampu hingga 50%.",
            }
        )

    # Rule 4: Peringatkan jika beban daya tinggi
    if latest_data.power > 2500:
        recommendations.append(
            {
                "icon": "⚠️",
                "message": f"Beban daya tinggi ({latest_data.power}W). Pertimbangkan untuk mematikan perangkat non-esensial.",
            }
        )

    # Rule 5: Peringatkan jika suhu ruangan tidak nyaman
    if latest_data.indoor_temperature < 18 or latest_data.indoor_temperature > 25:
        recommendations.append(
            {
                "icon": "🌡️",
                "message": f"Suhu ruangan tidak nyaman ({latest_data.indoor_temperature}°C).",
            }
        )

    # Rule 6: Peringatkan jika kelembaban ruangan tidak nyaman
    if latest_data.indoor_humidity < 30 or latest_data.indoor_humidity > 60:
        recommendations.append(
            {
                "icon": "💧",
                "message": f"Kelembaban ruangan tidak nyaman ({latest_data.indoor_humidity}%).",
            }
        )

    return {
        "timestamp": latest_data.timestamp.strftime("%Y-%m-%d %H:%M"),
        "recommendations": recommendations,
    }
