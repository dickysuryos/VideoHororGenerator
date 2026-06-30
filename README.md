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

## 🎬 Output Showcase

Here are some example video generations created by Project Terranova and saved in the `output/` directory:

### 👻 Kuntilanak (Landscape)
- **Original Prompt:** *Kuntilanak tertawa di atas pohon kelapa tua malam hari kabut tebal*
- **Indonesian Caption:** *Di bawah naungan malam pekat, kabut tebal menari di antara pohon kelapa tua yang bengkok. Tawa melengking, dingin menusuk tulang, menggema dari sesosok Kuntilanak yang bertengger di dahan, siap meneror jiwa yang tersesat.*
- **Video URL:** [http://horror.videoharbor.space/api/video/output/0088b74e-2009-49e1-81be-f43c31158f03.mp4](http://horror.videoharbor.space/api/video/output/0088b74e-2009-49e1-81be-f43c31158f03.mp4)

https://github.com/dickysuryos/VideoHororGenerator/assets/0088b74e-2009-49e1-81be-f43c31158f03.mp4

<video src="http://horror.videoharbor.space/api/video/output/0088b74e-2009-49e1-81be-f43c31158f03.mp4" width="100%" controls></video>

### 👻 Pocong (Portrait)
- **Original Prompt:** *pocong bersembunyi di balik pohon pisang , di malam hari diterangi cahaya bulan*
- **Indonesian Caption:** *Di tengah pekatnya malam dan kabut yang memeluk rumpun pisang, sesosok Pocong mengintai, terbungkus kafan lusuh yang membusuk. Mata putihnya bersinar dingin di bawah rembulan, sementara wajah pucatnya terkunci dalam jeritan tanpa suara, siap meneror di kegelapan abadi.*
- **Video URL:** [http://horror.videoharbor.space/api/video/output/3c8eb377-ad54-449f-bc3a-a2be59817c27.mp4](http://horror.videoharbor.space/api/video/output/3c8eb377-ad54-449f-bc3a-a2be59817c27.mp4)

<video src="http://horror.videoharbor.space/api/video/output/3c8eb377-ad54-449f-bc3a-a2be59817c27.mp4" width="100%" controls></video>

### 🌳 Creepy Forest Atmosphere (Landscape)
- **Original Prompt:** *berjalan menelusuri hutan lebat di malam hari yang menyeramkan , tiba tiba mendengar sesuatu terjatuh di arah belakang pohon*
- **Indonesian Caption:** *Malam merayap sunyi di hutan belantara, kabut tebal menyelimuti setiap sudut, mencekik napas. Tiba-tiba, suara dentuman misterius memecah keheningan, menggema dari balik bayangan pohon tua, seolah ada sesuatu yang mengintai di kedalaman gelap.*
- **Video URL:** [http://horror.videoharbor.space/api/video/output/5232233b-8bc1-4fdc-a34b-a1fb3ee6608e.mp4](http://horror.videoharbor.space/api/video/output/5232233b-8bc1-4fdc-a34b-a1fb3ee6608e.mp4)

<video src="http://horror.videoharbor.space/api/video/output/5232233b-8bc1-4fdc-a34b-a1fb3ee6608e.mp4" width="100%" controls></video>

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

## 🐳 How to Run in Docker

If you prefer to run the FastAPI BFF server inside a Docker container:

### 1. Build and Start the Container
Ensure Docker and Docker Compose are installed, then build and run the services:
```bash
docker compose up -d --build
```

### 2. Access the UI
Open your browser and navigate to:
```
http://localhost:8005
```
*(Note: Port `8005` is exposed on all network interfaces of the host, allowing access via local hostnames or specific IP addresses like `http://100.93.237.81:8005`).*

### 3. Container Administration
- To stream container logs:
  ```bash
  docker compose logs -f
  ```
- To stop and remove the container:
  ```bash
  docker compose down
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
