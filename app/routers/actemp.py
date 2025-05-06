# routers/tset_router.py

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from ..database import Sessionlocal
from ..service import ac_temp

router = APIRouter(
    prefix="/tset",
    tags=["T_set"],
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/set")
async def set_tset(tset: int = Body(..., embed=True), db: Session = Depends(get_db)):
    try:
        updated = ac_temp.update_tset(tset, db)
        return {"status": "success", "updated_T_set": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get")
async def get_tset(db: Session = Depends(get_db)):
    value = ac_temp.get_last_tset(db)
    return {"T_set": value}
