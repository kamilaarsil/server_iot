import subprocess
import uvicorn
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from fastapi_tailwind import tailwind
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.models import Base
from app.database import engine
from app.routers import pzem, aht10, camera, openweather, analysis, carbonemission, actemp, pmvashrae, insight
from app.service import open_weather, pzem_sensor, web_cam, interest, emission, pmv


LOCATION = "Depok,ID"
LAT = "-6.400"
LON = "106.819"
API_KEY = "115653f609fb6a5afdc0a0b447870c1b"

# Run Alembic migrations before starting the server
def run_migrations():
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("✅ Alembic migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Alembic migration failed: {e}")
        exit(1)  # Stop execution if migration fails

run_migrations()  # Ensure DB is up to date

Base.metadata.create_all(bind=engine)

static_files = StaticFiles(directory="app/static")

async def run_service():
    try:
        await open_weather.get_weather(API_KEY, LAT, LON)
    except Exception as e:
        print(f"Failed to run Open Weather service: {e}")

    try:
        await pzem_sensor.read_pzem_data()
    except Exception as e:
        print(f"Failed to run PZEM service: {e}")

    try:
        await web_cam.people_counter()
    except Exception as e:
        print(f"Failed to run WebCam service: {e}")

    try:
        interest.get_interest_data()
    except Exception as e:
        print(f"Failed to run Interest service: {e}")

    try:
        emission.log_emission()
    except Exception as e:
        print(f"Failed to run Emission service: {e}")

    try:
        pmv.calculate_and_log_pmv()
    except Exception as e:
        print(f"Failed to run PMV service: {e}")
        
def run_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_service, 'interval', minutes=1)
    scheduler.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Proses startup
    print("Starting up...")
    process = tailwind.compile(static_files.directory + "/css/output.css", watch=True)
    run_scheduler()  # Menjalankan scheduler saat startup

    yield  # Aplikasi berjalan di sini

    # Proses shutdown
    print("Shutting down...")
    process.terminate()  # Menghentikan proses Tailwind CSS

app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", static_files, name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(request, "home.html")

app.include_router(pzem.router)
app.include_router(aht10.router)
app.include_router(camera.router)
app.include_router(openweather.router)
app.include_router(analysis.router)
app.include_router(carbonemission.router)
app.include_router(actemp.router)
app.include_router(pmvashrae.router)
app.include_router(insight.router)

def main():

    print("[DEBUG] IP_SERVER =", os.environ.get("IP_SERVER"))
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
