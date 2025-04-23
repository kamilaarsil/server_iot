from imageai.Detection import ObjectDetection
import cv2
import os
from datetime import datetime
import warnings
import httpx
from ..utils.camera_manager import camera_stream

warnings.filterwarnings("ignore", category=UserWarning, module="torchvision.models._utils")

MODEL_PATH = "models/retinanet_resnet50_fpn_coco-eeacb38b.pth"
MIN_PROBABILITY = 15
FASTAPI_URL = "http://localhost:8000/camera/create"  # API Endpoint

execution_path = os.getcwd()

def ensure_directories():
    os.makedirs("images/in", exist_ok=True)
    os.makedirs("images/out", exist_ok=True)

def generate_file_paths():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = f"images/in/input_frame_{timestamp}.png"
    output_path = f"images/out/output_frame_{timestamp}.png"
    return input_path, output_path

def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

async def people_counter():
    ensure_directories()
    clear_directory("images/in")
    clear_directory("images/out")

    frame = camera_stream.get_frame()
    if frame is None:
        print("Failed to capture frame from camera")
        return
    
    detector = ObjectDetection()
    detector.useCPU = True

    if MODEL_PATH == "models/retinanet_resnet50_fpn_coco-eeacb38b.pth":
        detector.setModelTypeAsRetinaNet()
    elif MODEL_PATH == "models/yolov3.pt":
        detector.setModelTypeAsYOLOv3()
    elif MODEL_PATH == "models/yolov3-tiny.pt":
        detector.setModelTypeAsYOLOv3_tiny()

    detector.setModelPath(os.path.join(execution_path, MODEL_PATH))
    detector.loadModel()

    try:
        input_path, output_path = generate_file_paths()
        cv2.imwrite(input_path, frame)

        custom = detector.CustomObjects(person=True)
        detections = detector.detectObjectsFromImage(
            input_image=input_path, 
            output_image_path=output_path, 
            minimum_percentage_probability=MIN_PROBABILITY, 
            custom_objects=custom
        )
        num_people = len(detections)
        print(f"Number of people detected: {num_people}")

        await store_data(num_people)
    
    except Exception as e:
        print(f"Error: {e}")

async def store_data(num_people):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(FASTAPI_URL, json={"occupant": num_people})
            response.raise_for_status()
            print("WebCam data stored successfully")
        except httpx.HTTPStatusError as e:
            print(f"WebCam failed to store data: {e}")