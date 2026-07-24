"""Webcam proctoring helper built on OpenCV.

Opens the local machine's webcam (device index 0), runs Haar-cascade face
detection on each frame in a background thread, and exposes:
  - an MJPEG frame generator for a live <img> preview in the browser
  - a lightweight JSON-able status (face_detected / no_face_streak)
  - start/stop lifecycle helpers so the camera is released when an exam ends

IMPORTANT ARCHITECTURE NOTE
----------------------------
cv2.VideoCapture(0) opens the camera attached to the machine running this
Flask *server process* - not the camera on the student's own laptop/phone.
That's fine for local development or a single proctoring workstation, but it
will NOT work as "each student's own webcam" if you deploy this to a normal
multi-user website, because every visitor's browser would be viewing the
server's camera, not their own. For real multi-student remote proctoring you
would instead capture frames in the browser (JavaScript getUserMedia) and
POST them to the server for OpenCV analysis. This module is intentionally
the simpler "server webcam" version since that's what was requested.
"""
import threading
import time

import cv2

_FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


class FaceMonitor:
    """Owns one cv2.VideoCapture device and continuously scans it for faces."""

    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self._cap = None
        self._face_cascade = cv2.CascadeClassifier(_FACE_CASCADE_PATH)
        self._lock = threading.Lock()
        self._latest_jpeg = None
        self._face_detected = False
        self._no_face_streak = 0
        self._running = False
        self._thread = None
        self._error = None

    def start(self):
        """Open the camera and start the background capture/detection loop."""
        with self._lock:
            if self._running:
                return self._error is None
            self._error = None
            self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW) if _is_windows() else cv2.VideoCapture(self.camera_index)
            if not self._cap or not self._cap.isOpened():
                self._error = "Could not access a webcam on this machine."
                self._cap = None
                return False
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            return True

    def stop(self):
        """Stop the loop and release the camera device."""
        with self._lock:
            self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        if self._cap:
            self._cap.release()
            self._cap = None
        self._latest_jpeg = None

    def _loop(self):
        while True:
            with self._lock:
                if not self._running or not self._cap:
                    break
                cap = self._cap
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60))

            face_found = len(faces) > 0
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 0), 2)

            if not face_found:
                cv2.putText(frame, "No face detected", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif len(faces) > 1:
                cv2.putText(frame, "Multiple faces detected", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 140, 255), 2)

            ok_encode, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            with self._lock:
                if ok_encode:
                    self._latest_jpeg = buffer.tobytes()
                self._face_detected = face_found and len(faces) == 1
                self._no_face_streak = 0 if self._face_detected else self._no_face_streak + 1
            time.sleep(0.05)

    def get_status(self):
        with self._lock:
            return {
                "active": self._running,
                "error": self._error,
                "face_detected": self._face_detected,
                "no_face_streak": self._no_face_streak,
            }

    def frame_generator(self):
        """Yield an MJPEG multipart stream for use as a Flask Response."""
        boundary = b"--frame"
        while True:
            with self._lock:
                if not self._running:
                    break
                jpeg = self._latest_jpeg
            if jpeg is None:
                time.sleep(0.05)
                continue
            yield boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            time.sleep(0.05)


def _is_windows():
    import platform
    return platform.system().lower() == "windows"


# One shared monitor per exam attempt, keyed by (user_id, exam_id), so a
# student can only have one active camera session at a time and it is
# always cleanly released when the exam is submitted or abandoned.
_monitors = {}
_monitors_lock = threading.Lock()


def get_monitor(user_id, exam_id):
    key = (user_id, exam_id)
    with _monitors_lock:
        monitor = _monitors.get(key)
        if monitor is None:
            monitor = FaceMonitor()
            _monitors[key] = monitor
        return monitor


def release_monitor(user_id, exam_id):
    key = (user_id, exam_id)
    with _monitors_lock:
        monitor = _monitors.pop(key, None)
    if monitor:
        monitor.stop()
