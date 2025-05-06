from ..models import Pzem, AHT10, Camera, OpenWeather, DataAnalysis
from ..database import Sessionlocal
from fastapi import Depends
from sqlalchemy.orm import Session
from .ac_temp import get_last_tset  # ✅ Import from your T_set service

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

def get_interest_data(db: Session = Depends(get_db)):
    try:
        db = next(get_db())

        latest_data = {
            "pzem": db.query(Pzem).order_by(Pzem.timestamp.desc()).first(),
            "aht": db.query(AHT10).order_by(AHT10.timestamp.desc()).first(),
            "camera": db.query(Camera).order_by(Camera.timestamp.desc()).first(),
            "openweather": db.query(OpenWeather).order_by(OpenWeather.timestamp.desc()).first()
        }

        # ✅ Get the most recent T_set value from the DB
        last_tset = get_last_tset(db)

        interest_data = DataAnalysis(
            power=latest_data["pzem"].power if latest_data["pzem"] else 0,
            energy=latest_data["pzem"].energy if latest_data["pzem"] else 0,
            indoor_temperature=latest_data["aht"].temperature if latest_data["aht"] else 0,
            indoor_humidity=latest_data["aht"].humidity if latest_data["aht"] else 0,
            outdoor_temperature=latest_data["openweather"].temperature if latest_data["openweather"] else 0,
            outdoor_humidity=latest_data["openweather"].humidity if latest_data["openweather"] else 0,
            occupant=latest_data["camera"].occupant if latest_data["camera"] else 0,
            ac_temperature=last_tset  # ✅ Ensure T_set is saved for retraining
        )

        db.add(interest_data)
        db.commit()

        print("✅ Interest data stored successfully")

    except Exception as e:
        print(f"❌ Failed to store data: {e}")
