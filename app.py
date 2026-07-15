import cv2
import math
import numpy as np
import av
import urllib.request
from pathlib import Path
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    HandLandmarksConnections,
    RunningMode,
)
from mediapipe.tasks.python.vision.drawing_utils import draw_landmarks

st.set_page_config(page_title="Project-C", layout="wide")
st.title("Project-C")
st.write("Nyalakan kamera, angkat kedua tanganmu, dan lakukan gerakan 'Pinch' untuk membuka kotak filter")

# --- SETUP MODEL MEDIAPIPE ---
MODEL_PATH = Path("hand_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

@st.cache_resource
def ensure_model():
    if not MODEL_PATH.exists():
        with st.spinner("Mengunduh model AI..."):
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

ensure_model()

@st.cache_resource
def init_mediapipe():
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.7,
    )
    return HandLandmarker.create_from_options(options)

hands = init_mediapipe()

# --- KONFIGURASI WEBRTC (Agar koneksi stabil di Cloud) ---
# --- KONFIGURASI WEBRTC (Agar koneksi stabil di Cloud) ---
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [
        # 1. STUN Server (Cadangan)
        {"urls": ["stun:stun.l.google.com:19302"]},
        
        # 2. TURN Server (ExpressTurn milikmu untuk menembus Firewall)
        {
            "urls": [
                "turn:free.expressturn.com:3478",
                "turn:free.expressturn.com:3478?transport=tcp"
            ],
            "username": "000000002099492358",
            "credential": "yHLU/Gv4hvsg9qyYTGbkgibM9iQ="
        }
    ]}
)

# --- CLASS UNTUK MEMPROSES VIDEO REAL-TIME ---
class HandPortalProcessor:
    def __init__(self):
        # State management dipindah ke dalam class
        self.portal_active = False
        self.filters = ["Normal", "Invert", "Heatmap", "Emboss", "Cartoon", "B & W", "4K HDR", "Neon Glow"]
        self.current_filter_idx = 0
        self.cooldown = 0
        self.timestamp_ms = 0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # Convert frame WebRTC ke OpenCV format
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)
        h, w, _ = img.shape
        
        rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # MediaPipe butuh timestamp video yang terus bertambah
        self.timestamp_ms += 33
        results = hands.detect_for_video(mp_image, self.timestamp_ms)

        status_teks = "Mencari Tangan..."

        if self.cooldown > 0:
            self.cooldown -= 1

        if results.hand_landmarks:
            for hand_landmarks in results.hand_landmarks:
                draw_landmarks(img, hand_landmarks, HandLandmarksConnections.HAND_CONNECTIONS)

            if len(results.hand_landmarks) == 2:
                hand1 = results.hand_landmarks[0]
                hand2 = results.hand_landmarks[1]

                x1_idx, y1_idx = int(hand1[8].x * w), int(hand1[8].y * h)
                x1_thb, y1_thb = int(hand1[4].x * w), int(hand1[4].y * h)
                x2_idx, y2_idx = int(hand2[8].x * w), int(hand2[8].y * h)
                x2_thb, y2_thb = int(hand2[4].x * w), int(hand2[4].y * h)

                jarak_tangan1 = math.hypot(x1_idx - x1_thb, y1_idx - y1_thb)
                jarak_tangan2 = math.hypot(x2_idx - x2_thb, y2_idx - y2_thb)

                pinch1 = jarak_tangan1 < 40
                pinch2 = jarak_tangan2 < 40

                if self.cooldown == 0:
                    if pinch1 and pinch2:
                        self.portal_active = not self.portal_active
                        self.cooldown = 30
                    elif self.portal_active and (pinch1 != pinch2):
                        self.current_filter_idx = (self.current_filter_idx + 1) % len(self.filters)
                        self.cooldown = 20

                if self.portal_active:
                    x_min = max(0, min(x1_idx, x1_thb, x2_idx, x2_thb))
                    x_max = min(w, max(x1_idx, x1_thb, x2_idx, x2_thb))
                    y_min = max(0, min(y1_idx, y1_thb, y2_idx, y2_thb))
                    y_max = min(h, max(y1_idx, y1_thb, y2_idx, y2_thb))

                    if x_max > x_min + 10 and y_max > y_min + 10:
                        roi = img[y_min:y_max, x_min:x_max]
                        filter_name = self.filters[self.current_filter_idx]

                        if filter_name == "Invert":
                            roi = cv2.bitwise_not(roi)
                        elif filter_name == "Heatmap":
                            roi = cv2.applyColorMap(roi, cv2.COLORMAP_JET)
                        elif filter_name == "Emboss":
                            kernel = np.array([[0, -1, -1], [1, 0, -1], [1, 1, 0]])
                            roi = cv2.filter2D(roi, -1, kernel) + 128
                        elif filter_name == "Cartoon":
                            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                            gray = cv2.medianBlur(gray, 5)
                            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
                            color = cv2.bilateralFilter(roi, 9, 250, 250)
                            roi = cv2.bitwise_and(color, color, mask=edges)
                        elif filter_name == "B & W":
                            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                            roi = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                        elif filter_name == "4K HDR":
                            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                            roi = cv2.filter2D(roi, -1, kernel)
                            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                            hsv[:, :, 1] = cv2.add(hsv[:, :, 1], 30)
                            roi = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                            roi = cv2.convertScaleAbs(roi, alpha=1.1, beta=0)
                        elif filter_name == "Neon Glow":
                            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                            edges = cv2.Canny(blurred, 50, 150)
                            kernel = np.ones((3, 3), np.uint8)
                            edges = cv2.dilate(edges, kernel, iterations=1)
                            neon_color = np.full(roi.shape, (255, 50, 255), dtype=np.uint8)
                            neon_edges = cv2.bitwise_and(neon_color, neon_color, mask=edges)
                            dark_roi = cv2.convertScaleAbs(roi, alpha=0.3, beta=0)
                            roi = cv2.add(dark_roi, neon_edges)

                        img[y_min:y_max, x_min:x_max] = roi
                        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 255), 2)
                        cv2.putText(img, f"Filter: {filter_name}", (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    
                    status_teks = "Pinch 1 change filter"
                else:
                    status_teks = "Pinch 2 tangan untuk open persegi"
            elif len(results.hand_landmarks) == 1:
                status_teks = "Butuh 2 tangan untuk membuka Kotak Filter."

        cv2.putText(img, status_teks, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Kembalikan gambar yang sudah diproses ke layar browser
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# --- MENAMPILKAN KAMERA DI HALAMAN WEB ---
webrtc_streamer(
    key="portal-filter",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTC_CONFIGURATION,
    video_processor_factory=HandPortalProcessor,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True
)
