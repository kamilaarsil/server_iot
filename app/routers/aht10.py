from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from starlette import status
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse

from ..database import Sessionlocal
from ..models import AHT10
from ..service.pmv import calculate_and_log_pmv


templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/aht10",
    tags=["aht10"],
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()
        
class AHT10Request(BaseModel):
    temperature: float = Field(description="Temperature", ge=-40.0, le=200.0)
    humidity: float = Field(description="Humidity", ge=0.0, le=100.0)

### Pages ###
@router.get("/", response_class=HTMLResponse)
async def aht10(request: Request):
    return templates.TemplateResponse(request, "aht10.html")

### Endpoints ###
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_aht10(aht10_request: AHT10Request, db: Session = Depends(get_db)):
    if not aht10_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
    
    aht10 = AHT10(**aht10_request.model_dump())
    db.add(aht10)
    db.commit()

    # Automatically calculate and log PMV
    try:
        pmv_result = calculate_and_log_pmv(db)
    except Exception as e:
        print(f"PMV logging failed: {e}")
        pmv_result = {"error": "PMV calculation failed"}

    return {
        "aht10": {
            "temperature": aht10.temperature,
            "humidity": aht10.humidity
        },
        "pmv_result": pmv_result
    }

@router.get("/data_aht10", status_code=status.HTTP_200_OK)
async def read_aht10_data(page: int = 1, db: Session = Depends(get_db)):
    limit = 10
    offset = (page - 1) * limit

    aht10_records = (
        db.query(AHT10)
        .order_by(AHT10.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total_records = db.query(AHT10).count()
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
            }
            for record in aht10_records
        ],
    }

@router.put("/update/{aht10_id}", status_code=status.HTTP_200_OK)
async def update_aht10(
    aht10_id: int, aht10_request: AHT10Request, db: Session = Depends(get_db)
):
    aht10 = db.query(AHT10).filter(AHT10.id == aht10_id).first()
    if not aht10:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="AHT10 not found"
        )

    aht10.temperature = aht10_request.temperature
    aht10.humidity = aht10_request.humidity
    db.commit()
    return {"message": "AHT10 data updated successfully"}

    
@router.delete("/delete/{aht10_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_aht10(aht10_id: int, db: Session = Depends(get_db)):
    try:
        aht10 = db.query(AHT10).filter(AHT10.id == aht10_id).first()
        if not aht10:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AHT10 not found")
        
        db.delete(aht10)
        db.commit()
        return {"message": "AHT10 data deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))