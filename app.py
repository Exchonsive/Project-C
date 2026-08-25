import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Project-C", layout="wide")
st.title("Project-C")
st.write("Nyalakan kamera, angkat kedua tanganmu, dan lakukan gerakan 'Pinch' untuk membuka kotak filter")

HAND_PORTAL_HTML = """
<div style="position:relative; width:100%; max-width:960px; margin:auto;">
  <video id="video" autoplay playsinline muted style="display:none;"></video>
  <canvas id="canvas" style="width:100%; border-radius:10px; background:#111;"></canvas>
  <div id="status"
       style="position:absolute; top:10px; left:10px; color:#0f0; font-family:monospace;
              background:rgba(0,0,0,0.55); padding:3px 8px; border-radius:6px; font-size:11px;">
    Memuat model AI...
  </div>
</div>

<script type="module">
import { HandLandmarker, FilesetResolver } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest";

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d", { willReadFrequently: true });
const statusEl = document.getElementById("status");

const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";

const FILTERS = ["Normal", "Invert", "B & W", "Sepia", "Warm HDR", "Neon Edge"];
const PINCH_THRESHOLD = 0.055; // jarak normalisasi (0-1). Makin kecil = pinch harus makin rapat.

let handLandmarker = null;
let portalActive = false;
let filterIdx = 0;
let cooldown = 0;

function dist(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function applyFilter(x, y, w, h, name) {
  if (name === "Normal" || w <= 0 || h <= 0) return;
  const roi = ctx.getImageData(x, y, w, h);
  const d = roi.data;

  if (name === "Invert") {
    for (let i = 0; i < d.length; i += 4) {
      d[i] = 255 - d[i];
      d[i + 1] = 255 - d[i + 1];
      d[i + 2] = 255 - d[i + 2];
    }
  } else if (name === "B & W") {
    for (let i = 0; i < d.length; i += 4) {
      const g = 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
      d[i] = d[i + 1] = d[i + 2] = g;
    }
  } else if (name === "Sepia") {
    for (let i = 0; i < d.length; i += 4) {
      const r = d[i], g = d[i + 1], b = d[i + 2];
      d[i] = Math.min(255, 0.393 * r + 0.769 * g + 0.189 * b);
      d[i + 1] = Math.min(255, 0.349 * r + 0.686 * g + 0.168 * b);
      d[i + 2] = Math.min(255, 0.272 * r + 0.534 * g + 0.131 * b);
    }
  } else if (name === "Warm HDR") {
    for (let i = 0; i < d.length; i += 4) {
      d[i] = Math.min(255, d[i] * 1.15 + 8);
      d[i + 1] = Math.min(255, d[i + 1] * 1.05);
      d[i + 2] = Math.min(255, d[i + 2] * 0.88);
    }
  } else if (name === "Neon Edge") {
    // deteksi tepi sederhana (selisih terhadap piksel di kanan+bawah)
    const w4 = w * 4;
    const src = new Uint8ClampedArray(d); // salinan sebelum ditimpa
    for (let y0 = 0; y0 < h - 1; y0++) {
      for (let x0 = 0; x0 < w - 1; x0++) {
        const i = y0 * w4 + x0 * 4;
        const g0 = src[i], g1 = src[i + 4], g2 = src[i + w4];
        const edge = Math.abs(g0 - g1) + Math.abs(g0 - g2) > 40 ? 255 : 0;
        d[i] = edge;
        d[i + 1] = 0;
        d[i + 2] = edge;
      }
    }
  }

  ctx.putImageData(roi, x, y);
}

async function init() {
  try {
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
    );
    handLandmarker = await HandLandmarker.createFromOptions(vision, {
      baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
      runningMode: "VIDEO",
      numHands: 2,
      minHandDetectionConfidence: 0.7,
    });

    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    video.srcObject = stream;
    await video.play();

    statusEl.textContent = "Mencari tangan...";
    requestAnimationFrame(loop);
  } catch (err) {
    statusEl.textContent = "Error: " + err.message;
    console.error(err);
  }
}

function loop() {
  if (video.readyState >= 2) {
    if (canvas.width === 0) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }
    const w = canvas.width, h = canvas.height;

    const result = handLandmarker.detectForVideo(video, performance.now());

    // Gambar frame kamera (di-mirror biar berasa cermin)
    ctx.save();
    ctx.scale(-1, 1);
    ctx.drawImage(video, -w, 0, w, h);
    ctx.restore();

    if (cooldown > 0) cooldown--;
    let statusTxt = "Mencari tangan...";

    if (result.landmarks && result.landmarks.length === 2) {
      const [hand1, hand2] = result.landmarks;
      const pinch1 = dist(hand1[8], hand1[4]) < PINCH_THRESHOLD;
      const pinch2 = dist(hand2[8], hand2[4]) < PINCH_THRESHOLD;

      if (cooldown === 0) {
        if (pinch1 && pinch2) {
          portalActive = !portalActive;
          cooldown = 20;
        } else if (portalActive && pinch1 !== pinch2) {
          filterIdx = (filterIdx + 1) % FILTERS.length;
          cooldown = 15;
        }
      }

      if (portalActive) {
        // koordinat di-mirror (1 - x) karena canvas digambar terbalik
        const xs = [hand1[8].x, hand1[4].x, hand2[8].x, hand2[4].x].map((x) => (1 - x) * w);
        const ys = [hand1[8].y, hand1[4].y, hand2[8].y, hand2[4].y].map((y) => y * h);
        const x1 = Math.max(0, Math.min(...xs));
        const x2 = Math.min(w, Math.max(...xs));
        const y1 = Math.max(0, Math.min(...ys));
        const y2 = Math.min(h, Math.max(...ys));

        if (x2 - x1 > 15 && y2 - y1 > 15) {
          applyFilter(Math.round(x1), Math.round(y1), Math.round(x2 - x1), Math.round(y2 - y1), FILTERS[filterIdx]);
          ctx.strokeStyle = "#ffff00";
          ctx.lineWidth = 2;
          ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
          ctx.fillStyle = "#ffff00";
          ctx.font = "12px monospace";
          ctx.fillText("Filter: " + FILTERS[filterIdx], x1, y1 - 6);
        }
        statusTxt = "Pinch 1 tangan untuk ganti filter";
      } else {
        statusTxt = "Pinch 2 tangan untuk buka kotak filter";
      }
    } else if (result.landmarks && result.landmarks.length === 1) {
      statusTxt = "Butuh 2 tangan untuk membuka kotak filter";
    }

    statusEl.textContent = statusTxt;
  }
  requestAnimationFrame(loop);
}

init();
</script>
"""

components.html(HAND_PORTAL_HTML, height=640, scrolling=False)
