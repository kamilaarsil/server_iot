from sqlalchemy.orm import Session
from ..models import DataAnalysis
from datetime import datetime

def update_tset(tset: int, db: Session):
    if not (17 <= tset <= 21):
        raise ValueError("T_set must be between 17 and 21°C.")

    latest = db.query(DataAnalysis).order_by(DataAnalysis.timestamp.desc()).first()
    if not latest:
        raise ValueError("No DataAnalysis row exists to update.")

    latest.ac_temperature = tset
    latest.timestamp = datetime.now()
    db.commit()
    return tset

def get_last_tset(db: Session):
    latest = db.query(DataAnalysis).order_by(DataAnalysis.timestamp.desc()).first()
    return latest.ac_temperature if latest and latest.ac_temperature else 24
