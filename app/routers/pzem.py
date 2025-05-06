from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Request
from starlette import status
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..database import Sessionlocal
from ..models import Pzem
from ..service import pzem_sensor

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/pzem",
    tags=["pzem"],
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

class PzemRequest(BaseModel):
    voltage: float = Field(description="Voltage", ge=0.0)
    current: float = Field(description="Current", ge=0.0)
    power: float = Field(description="Power", ge=0.0)
    energy: float = Field(description="Energy", ge=0.0)
    frequency: float = Field(description="Frequency", ge=0.0)
    power_factor: float = Field(description="Power Factor", ge=0.0)

### Pages ###
@router.get("/", response_class=HTMLResponse)
async def pzem(request: Request):
    return templates.TemplateResponse(request, "pzem.html")

### Endpoints ###
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_pzem(pzem_request: PzemRequest, db: Session = Depends(get_db)):
    if not pzem_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
    pzem = Pzem(**pzem_request.model_dump())
    
    db.add(pzem)
    db.commit()

    return {
        "id": pzem.id,
        "timestamp": pzem.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "voltage": pzem.voltage,
        "current": pzem.current,
        "power": pzem.power,
        "energy": pzem.energy,
        "frequency": pzem.frequency,
        "power_factor": pzem.power_factor
    }


@router.get("/data_pzem", status_code=status.HTTP_200_OK)
async def read_pzem_data(page: int = 1, db: Session = Depends(get_db)):
    limit = 10
    offset = (page - 1) * limit

    pzem_records = (
        db.query(Pzem)
        .order_by(Pzem.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total_records = db.query(Pzem).count()
    total_pages = (total_records + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "total_records": total_records,
        "data": [
            {
                "id": record.id,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M"),
                "voltage": record.voltage,
                "current": record.current,
                "power": record.power,
                "energy": record.energy,
                "power_factor": record.power_factor,
                "frequency": record.frequency
            }
            for record in pzem_records
        ],
    }
    
@router.get("/reset_energy", status_code=status.HTTP_200_OK)
async def reset_pzem_energy():
    try:
        pzem_sensor.reset_energy_counter()
        return {"message": "Energy reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/update/{pzem_id}", status_code=status.HTTP_200_OK)
async def update_pzem(pzem_id: int, pzem_request: PzemRequest, db: Session = Depends(get_db)):
    try:
        pzem = db.query(Pzem).filter(Pzem.id == pzem_id).first()
        if not pzem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pzem not found")
        
        pzem.voltage = pzem_request.voltage
        pzem.current = pzem_request.current
        pzem.power = pzem_request.power
        pzem.energy = pzem_request.energy
        pzem.power_factor = pzem_request.power_factor
        pzem.frequency = pzem_request.frequency
        db.commit()
        return pzem
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.delete("/delete/{pzem_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pzem(pzem_id: int, db: Session = Depends(get_db)):
    try:
        pzem = db.query(Pzem).filter(Pzem.id == pzem_id).first()
        if not pzem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pzem not found")
        
        db.delete(pzem)
        db.commit()
        return {"message": "Pzem data deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))