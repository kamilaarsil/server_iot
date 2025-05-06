from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import EmissionLog
from ..models import DataAnalysis
from ..database import Sessionlocal
from fastapi import Depends

EMISSION_FACTOR = 0.7791  # kg CO2 per kWh

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

def log_emission(db: Session = Depends(get_db)):
    try:
        db = next(get_db())
        latest_data = db.query(DataAnalysis).order_by(DataAnalysis.timestamp.desc()).first()
        energy_latest=latest_data.energy if latest_data else 0
        
        emission = (energy_latest / 1000000) * EMISSION_FACTOR

        entry = EmissionLog(
            timestamp=datetime.now(),
            energy=energy_latest,
            emission=emission
        )

        db.add(entry)
        db.commit()
        return round(emission, 3)
    
    except Exception as e:
        print(f"❌ Failed to store data: {e}")

def latest_emission(db: Session):
    latest = db.query(EmissionLog).order_by(EmissionLog.timestamp.desc()).first()
    return {
        "emission": round(latest.emission, 3) if latest else 0.0,
        "timestamp": latest.timestamp.strftime("%Y-%m-%d %H:%M:%S") if latest else "-"
    }

def total_emission(db: Session):
    today = datetime.now().date()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    total = db.query(EmissionLog).filter(EmissionLog.timestamp.between(start, end)).with_entities(
        func.sum(EmissionLog.emission)).scalar() or 0.0

    return round(total, 3)


