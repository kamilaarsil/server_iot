import cv2
import threading
import time


class CameraStream:
    """Singleton camera class to optimize CPU usage for low-power devices."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraStream, cls).__new__(cls)
                cls._instance.camera = cv2.VideoCapture(1)
                cls._instance.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Lebih ringan
                cls._instance.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Lebih ringan
                cls._instance.running = True
                cls._instance.frame = None
                cls._instance.fps_limit = 5  # Batasi ke 5 FPS
                cls._instance.thread = threading.Thread(
                    target=cls._instance._update, daemon=True
                )
                cls._instance.thread.start()
        return cls._instance

    def _update(self):
        """Continuously capture frames at a limited frame rate."""
        while self.running:
            start_time = time.time()
            success, frame = self.camera.read()
            if success:
                self.frame = frame
            time.sleep(
                max(0, 1 / self.fps_limit - (time.time() - start_time))
            )  # Batasi FPS

    def get_frame(self):
        """Return the latest frame."""
        return self.frame

    def stop(self):
        """Release the camera."""
        self.running = False
        self.camera.release()


camera_stream = CameraStream()
