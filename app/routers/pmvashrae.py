from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from ..database import Sessionlocal
from ..service import pmv
from ..service.pmv import pmv_to_comfort_status
from ..models import PMVLog

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/pmv",
    tags=["pmv"],
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

### 📊 PMV History (Paginated) ###
@router.get("/data_pmv", status_code=status.HTTP_200_OK)
async def read_pmv_data(page: int = 1, db: Session = Depends(get_db)):
    limit = 10
    offset = (page - 1) * limit

    pmv_records = (
        db.query(PMVLog)
        .order_by(PMVLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total_records = db.query(PMVLog).count()
    total_pages = (total_records + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "total_records": total_records,
        "data": [
            {
                "id": record.id,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M"),
                "pmv": record.pmv,
                "ppd": record.ppd,
                "comfort_status": pmv_to_comfort_status(record.pmv)
            }
            for record in pmv_records
        ],
    }


### 📈 Real-time PMV Result from Latest AHT10 ###
@router.get("/status", status_code=status.HTTP_200_OK)
async def get_pmv_status(db: Session = Depends(get_db)):
    try:
        result = pmv.calculate_and_log_pmv(db)
        return result
    except Exception as e:
        return {
            "error": "PMV calculation failed",
            "detail": str(e)
        }
