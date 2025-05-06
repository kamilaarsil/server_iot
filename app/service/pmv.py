from sqlalchemy.orm import Session
from datetime import datetime
from pythermalcomfort.models import pmv_ppd_ashrae
from fastapi import Depends
from ..models import AHT10, PMVLog
from ..database import Sessionlocal

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

def calculate_and_log_pmv(db: Session = Depends(get_db)):
    try:
        db = next(get_db())
        latest = db.query(AHT10).order_by(AHT10.timestamp.desc()).first()

        met = 1.0
        clo = 0.61
        air_speed = 0.1
        tr = latest.temperature

        result = pmv_ppd_ashrae(
            tdb=latest.temperature,
            tr=tr,
            rh=latest.humidity,
            vr=air_speed,
            met=met,
            clo=clo,
        )

        pmv_value = round(result["pmv"], 3)
        ppd_value = round(result["ppd"], 1)

        if -0.5 <= pmv_value <= 0.5:
            comfort_status = "✅ Comfortable"
            note = "PMV is within the recommended comfort range."
        else:
            comfort_status = "❌ Uncomfortable"
            note = "PMV is outside the recommended comfort range (-0.5 to +0.5)."

        log = PMVLog(
            timestamp=datetime.now(),
            t_indoor=latest.temperature,
            h_indoor=latest.humidity,
            pmv=pmv_value,
            ppd=ppd_value
        )

        db.add(log)
        db.commit()

        return {
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "T_indoor": log.t_indoor,
            "H_indoor": log.h_indoor,
            "pmv": pmv_value,
            "ppd": ppd_value,
            "comfort_status": comfort_status,
            "note": note
        }

    except Exception as e:
        print(f"❌ Failed to store data: {e}")
    
def get_recent_pmv_logs(db: Session, limit: int = 50):
    records = db.query(PMVLog).order_by(PMVLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M"),
            "T_indoor": r.t_indoor,
            "H_indoor": r.h_indoor,
            "pmv": r.pmv,
            "ppd": r.ppd
        }
        for r in reversed(records)  # reverse for chronological order
    ]

def pmv_to_comfort_status(pmv: float) -> str:
    return "✅ Comfortable" if -0.5 <= pmv <= 0.5 else "❌ Uncomfortable"
