from .database import Base
from sqlalchemy import Column, Integer, Float, DateTime, String
import datetime

class Pzem(Base):
    __tablename__ = "pzem"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, default=datetime.datetime.now)
    voltage = Column(Float)
    current = Column(Float)
    power = Column(Float)
    energy = Column(Float) #Wh
    frequency = Column(Float)
    power_factor = Column(Float)
    
class AHT10(Base):
    __tablename__ = "aht10"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, default=datetime.datetime.now)
    temperature = Column(Float)
    humidity = Column(Float)

class Camera(Base):
    __tablename__ = "camera"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, default=datetime.datetime.now)
    occupant = Column(Integer)
    
class OpenWeather(Base):
    __tablename__ = "open_weather"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, default=datetime.datetime.now)
    temperature = Column(Float)
    feels_like = Column(Float)
    humidity = Column(Float)

class DataAnalysis(Base):
    __tablename__ = "data_analysis"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, default=datetime.datetime.now)
    indoor_temperature = Column(Float, default=0)
    indoor_humidity = Column(Float, default=0)
    outdoor_temperature = Column(Float, default=0)
    outdoor_humidity = Column(Float, default=0)
    power = Column(Float, default=0)
    energy = Column(Float, default=0)
    occupant = Column(Integer, default=0)
    ac_temperature = Column(Integer, default=0)
    ac_fan = Column(Integer, default=0)

class RecommendationLog(Base):
    __tablename__ = "recommendation_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)

    current_t_set = Column(Integer)
    current_power = Column(Float)
    optimal_t_set = Column(Integer)
    predicted_power = Column(Float)
    estimated_saving = Column(Float)
    recommendation_text = Column(String)

class EmissionLog(Base):
    __tablename__ = "emission_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    energy = Column(Float)  # Wh
    emission = Column(Float)  # metric tons of CO2 equivalent

class PMVLog(Base):
    __tablename__ = "pmv_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    t_indoor = Column(Float)
    h_indoor = Column(Float)
    pmv = Column(Float)
    ppd = Column(Float)
    
