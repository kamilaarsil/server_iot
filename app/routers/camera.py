from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Request
from starlette import status
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import os
import cv2

from ..database import Sessionlocal
from ..models import Camera
from ..utils.camera_manager import camera_stream
import time

templates = Jinja2Templates(directory="app/templates")
execution_path = os.getcwd()

router = APIRouter(
    prefix="/camera",
    tags=["camera"],
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

class CameraRequest(BaseModel):
    occupant: int = Field(description="Occupant(s)", ge=0)

### Pages ###
@router.get("/", response_class=HTMLResponse)
async def camera(request: Request):
    return templates.TemplateResponse(request, "camera.html")

### Endpoints ###
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_camera(camera_request: CameraRequest, db: Session = Depends(get_db)):
    if not camera_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
    camera = Camera(**camera_request.model_dump())
    
    db.add(camera)
    db.commit()
    return camera

@router.get("/data_occupancy", status_code=status.HTTP_200_OK)
async def read_camera_data(page: int = 1, db: Session = Depends(get_db)):
    limit = 10
    offset = (page - 1) * limit

    camera_records = (
        db.query(Camera)
        .order_by(Camera.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total_records = db.query(Camera).count()
    total_pages = (total_records + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "total_records": total_records,
        "data": [
            {
                "id": record.id,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M"),
                "occupant": record.occupant,
            }
            for record in camera_records
        ],
    }
    
@router.put("/update/{camera_id}", status_code=status.HTTP_200_OK)
async def update_camera(camera_id: int, camera_request: CameraRequest, db: Session = Depends(get_db)):
    try:
        camera = db.query(Camera).filter(Camera.id == camera_id).first()
        if not camera:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
        
        camera.occupant = camera_request.occupant
        db.commit()
        return camera
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.delete("/delete/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    try:
        camera = db.query(Camera).filter(Camera.id == camera_id).first()
        if not camera:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
        
        db.delete(camera)
        db.commit()
        return {"message": "Camera data deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/stream")
async def video_stream():
    return StreamingResponse(
        generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )

def generate_frames():
    while True:
        frame = camera_stream.get_frame()
        if frame is None:
            continue

        # Kompres gambar dengan kualitas rendah agar lebih ringan
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        time.sleep(0.2)  # Batasi FPS ke 5 FPS


@router.get("/latest_images")
async def get_latest_images(db: Session = Depends(get_db)):
    input_dir = os.path.join(execution_path, "images/in")
    output_dir = os.path.join(execution_path, "images/out")

    try:
        # Get full paths for input files
        input_files = [
            os.path.join(input_dir, f)
            for f in os.listdir(input_dir)
            if f.endswith(".png")
        ]
        # Sort by creation time (newest first)
        input_files.sort(key=os.path.getctime, reverse=True)

        # Get full paths for output files
        output_files = [
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.endswith(".png")
        ]
        # Sort by creation time (newest first)
        output_files.sort(key=os.path.getctime, reverse=True)

        # Return the latest files (if any)
        return {
            "input": f"/images/in/{os.path.basename(input_files[0])}"
            if input_files
            else None,
            "output": f"/images/out/{os.path.basename(output_files[0])}"
            if output_files
            else None,
        }
    except Exception as e:
        return {"error": str(e)}