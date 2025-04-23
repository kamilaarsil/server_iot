from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

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
