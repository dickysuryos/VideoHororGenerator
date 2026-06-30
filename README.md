# Project Terranova: AI Horror Video Generator (Wan 2.1)

Project Terranova is a web application that generates highly realistic horror videos based on Indonesian folklore ghosts (*Pocong*, *Kuntilanak*, *Genderuwo*, and *Rumah Hantu*). It uses the **Wan 2.1 (1.3B/14B)** Text-to-Video models running serverless on **Modal.com** (utilizing A10G GPUs with smart CPU offloading), combined with **Gemini 2.5 Flash** for atmospheric prompt expansion and Indonesian story caption generation.

---

## 🔮 Features
- **Ghost Selection Interface**: Visual cards to pick reference folklore ghosts alongside actual uploaded reference images (`reference-image/` directory).
- **Gemini-Powered Expansion**: Analyzes local reference images, expands short Indonesian prompts into highly detailed, cinematic English scripts, and drafts Indonesian narrative captions.
- **Serverless Modal.com Integration**: Deploys Wan 2.1 models on high-performance GPUs with automatic persistent model caching (`/models` Volume) to eliminate future download overheads.
- **Live Logging Console**: Streaming Server-Sent Events (SSE) logs from the background GPU worker directly to the web UI.
- **Archive Gallery**: Browse and watch previously generated manifest videos.

---

## 📂 Project Structure
```
AppGenerateVideo/
├── app.py                # FastAPI Backend-for-Frontend (BFF)
├── modal_app.py          # Modal worker app (executes GPU denoising)
├── history.json          # Persistent local storage for projects database
├── requirements.txt      # Python dependencies for the local server
├── .env                  # Secrets configuration (Gemini & Modal tokens)
├── reference-image/      # Reference ghost pictures catalog
├── static/               # HTML/CSS/JS frontend files
└── output/               # Local folder containing downloaded video outputs (.mp4)
```

---

## ⚙️ Configuration Setup

### 1. Credentials File (`.env`)
Create a `.env` file in the root directory to store your API keys:
```env
GEMINI_API_KEY="your-gemini-api-key"
MODAL_TOKEN_ID="your-modal-token-id"
MODAL_TOKEN_SECRET="your-modal-token-secret"
```

### 2. Dependencies
Install requirements on your local system:
```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run Locally

### 1. Launch the BFF Server
Run the FastAPI application. By default, it binds to port `8005` on `127.0.0.1`:
```bash
python3 app.py
```

### 2. Access the UI
Open your browser and navigate to:
```
http://127.0.0.1:8005
```

---

## ☁️ How to Deploy on Modal.com

The background worker automatically builds a container image with the required GPU libraries (`torch`, `diffusers`, `imageio`, `opencv-python-headless`) and deploys the generation methods.

### 1. Authenticate with Modal
Ensure you have initialized your credentials in the shell:
```bash
modal setup
```
*(Or the credentials from `.env` will be automatically used by the backend server code).*

### 2. Deploy the Worker Application
Deploy the app definition to register it permanently under your Modal account workspace:
```bash
modal deploy modal_app.py
```
This registers the serverless endpoint `wan-video-horror` which the FastAPI backend will call directly when a user clicks **"Mulai Ritual"** in the UI.
