from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from ..database import Sessionlocal
from ..service import emission
from ..models import EmissionLog

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/emission",
    tags=["emission"],
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

### 🖥 Page Route for Dashboard ###
@router.get("/", response_class=HTMLResponse)
async def emission_page(request: Request):
    return templates.TemplateResponse(request, "emission.html")

### 📊 Emission History Data (Paginated) ###
@router.get("/data_emission", status_code=status.HTTP_200_OK)
async def read_emission_data(page: int = 1, db: Session = Depends(get_db)):
    limit = 10
    offset = (page - 1) * limit

    emission_records = (
        db.query(EmissionLog)
        .order_by(EmissionLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total_records = db.query(EmissionLog).count()
    total_pages = (total_records + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "total_records": total_records,
        "data": [
            {
                "id": record.id,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M"),
                "energy": record.energy,
                "emission": record.emission,
            }
            for record in emission_records
        ],
    }

### 📈 Real-time + Daily Emission Summary ###
@router.get("/status", status_code=status.HTTP_200_OK)
async def get_emission_status(db: Session = Depends(get_db)):
    latest = emission.latest_emission(db)
    total_today = emission.total_emission(db)

    return {
        "real_time_emission": latest["emission"],
        "latest_timestamp": latest["timestamp"],
        "total_emission": total_today
    }
