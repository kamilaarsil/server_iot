from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Request
from starlette import status
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..database import Sessionlocal
from ..models import OpenWeather

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/openweather",
    tags=["openweather"],
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

class OpenWeatherRequest(BaseModel):
    temperature: float = Field(description="Temperature", ge=-40.0, le=80.0)
    feels_like: float = Field(description="Feels Like", ge=-40.0, le=80.0)
    humidity: float = Field(description="Humidity", ge=0.0, le=100.0)

### Pages ###
@router.get("/", response_class=HTMLResponse)
async def openweather(request: Request):
    return templates.TemplateResponse(request, "openweather.html")

### Endpoints ###
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_openweather(openweather_request: OpenWeatherRequest, db: Session = Depends(get_db)):
    if not openweather_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
    openweather = OpenWeather(**openweather_request.model_dump())
    
    db.add(openweather)
    db.commit()
    return openweather

@router.get("/data_openweather", status_code=status.HTTP_200_OK)
async def read_openweather_data(page: int = 1, db: Session = Depends(get_db)):
    limit = 10
    offset = (page - 1) * limit

    openweather_records = (
        db.query(OpenWeather)
        .order_by(OpenWeather.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total_records = db.query(OpenWeather).count()
    total_pages = (total_records + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "total_records": total_records,
        "data": [
            {
                "id": record.id,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M"),
                "temperature": record.temperature,
                "humidity": record.humidity,
                "feels_like": record.feels_like
            }
            for record in openweather_records
        ],
    }

@router.put("/update/{openweather_id}", status_code=status.HTTP_200_OK)
async def update_openweather(openweather_id: int, openweather_request: OpenWeatherRequest, db: Session = Depends(get_db)):
    try:
        openweather = db.query(OpenWeather).filter(OpenWeather.id == openweather_id).first()
        if not openweather:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OpenWeather not found")
        
        openweather.temperature = openweather_request.temperature
        openweather.feels_like = openweather_request.feels_like
        openweather.humidity = openweather_request.humidity
        db.commit()
        return openweather
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/delete/{openweather_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_openweather(openweather_id: int, db: Session = Depends(get_db)):
    try:
        openweather = db.query(OpenWeather).filter(OpenWeather.id == openweather_id).first()
        if not openweather:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OpenWeather not found")
        
        db.delete(openweather)
        db.commit()
        return {"message": "OpenWeather data deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))