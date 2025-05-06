from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status

from ..database import Sessionlocal
from ..models import PMVLog, EmissionLog, RecommendationLog

router = APIRouter(
    prefix="/insight",
    tags=["insight"]
)

templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

### Page
@router.get("/", response_class=HTMLResponse)
async def insight_page(request: Request):
    return templates.TemplateResponse(request, "insight.html")

