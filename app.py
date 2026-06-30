import os
import uuid
import json
import logging
import asyncio
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image
from google import genai
from google.genai import types
import modal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TerranovaBackend")

# Load environment variables manually from local .env
def load_env():
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        os.environ[parts[0].strip()] = parts[1].strip()

load_env()

# Configure Directories
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
REF_DIR = BASE_DIR / "reference-image"
HISTORY_FILE = BASE_DIR / "history.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Schema definitions
class GenerateRequest(BaseModel):
    prompt: str
    ghost_type: str = "none"
    model_type: str = "14b"  # "1.3b" or "14b"
    aspect_ratio: str = "landscape"  # "landscape", "portrait", "square"
    steps: int = Field(30, ge=10, le=50)
    guidance: float = Field(5.0, ge=1.0, le=15.0)
    seed: int = -1

class HorrorPromptOutput(BaseModel):
    expanded_english_prompt: str = Field(description="A highly detailed cinematic English prompt for a realistic horror video. Focuses on shadows, atmospheric mist, camera panning, and chilling details.")
    indonesian_caption: str = Field(description="A scary and atmospheric description of the scene in Indonesian (Bahasa Indonesia). 2-3 sentences max.")

# In-Memory DB
PROJECTS: Dict[str, Dict[str, Any]] = {}

def load_history():
    global PROJECTS
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                PROJECTS = json.load(f)
            logger.info("History loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load history: {str(e)}")
            PROJECTS = {}
    else:
        PROJECTS = {}

def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(PROJECTS, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save history: {str(e)}")

load_history()

# Setup references mapping
GHOST_REFERENCES = {
    "pocong": {
        "id": "pocong",
        "name": "Pocong",
        "description": "Sesosok jasad terbungkus kain kafan putih khas Indonesia yang diikat erat. Mereka melompat dengan wajah hitam membusuk atau pucat mengerikan.",
        "images": ["pocong-ai.jpeg", "pocong-ai2.jpeg", "pocong-ai3.jpeg"]
    },
    "kuntilanak": {
        "id": "kuntilanak",
        "name": "Kuntilanak",
        "description": "Hantu wanita berambut sangat panjang terurai menutupi wajahnya, mengenakan daster putih bersih. Dikenal dengan tawanya yang melengking mengerikan.",
        "images": ["kuntilanak-ai.jpeg", "kuntilanak-ai2.jpeg", "kuntilanak-ai3.jpeg"]
    },
    "genderuwo": {
        "id": "genderuwo",
        "name": "Genderuwo",
        "description": "Raksasa menyerupai kera besar berbulu hitam lebat di sekujur tubuh, bermata merah membara, taring panjang, dan memancarkan aura kegelapan purba.",
        "images": ["genderuwo-ai.jpeg", "genderuwo-ai2.jpeg", "genderuwo-ai3.jpeg"]
    },
    "rumahhantu": {
        "id": "rumahhantu",
        "name": "Rumah Hantu",
        "description": "Bangunan kolonial tua yang terbengkalai, dipenuhi tanaman rambat liar, jendela berderit, kabut tipis di koridor gelap, dan entitas misterius.",
        "images": ["rumahhantu-ai.jpeg"]
    }
}

app = FastAPI(title="Terranova Horror Video AI", description="BFF Server for Terranova Horror Video Generator")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API: Get references list
@app.get("/api/references")
async def get_references():
    return GHOST_REFERENCES

# API: Get projects history
@app.get("/api/projects")
async def get_projects():
    # Return projects list sorted by timestamp descending
    res_list = []
    for p_id, p in PROJECTS.items():
        res_list.append({
            "id": p["id"],
            "prompt_original": p["prompt_original"],
            "indonesian_caption": p["indonesian_caption"],
            "ghost_type": p["ghost_type"],
            "model_type": p["model_type"],
            "aspect_ratio": p["aspect_ratio"],
            "status": p["status"],
            "progress": p["progress"],
            "video_url": p["video_url"],
            "timestamp": p["timestamp"]
        })
    res_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return res_list

# API: Get single project details
@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan.")
    return PROJECTS[project_id]

# Background Task for Modal execution
def generate_horror_video_task(project_id: str, payload: GenerateRequest):
    proj = PROJECTS[project_id]
    
    # 1. Map aspect ratio to pixels
    width, height = 832, 480  # Default landscape
    if payload.aspect_ratio == "portrait":
        width, height = 480, 832
    elif payload.aspect_ratio == "square":
        width, height = 624, 624
        
    class_name = "Wan14BModel" if payload.model_type == "14b" else "Wan13BModel"
    proj["logs"].append(f"Menghubungi serverless H100 di Modal.com untuk memuat {class_name}...")
    proj["progress"] = 25
    save_history()
    
    try:
        # Resolve credentials inside Task if running asynchronously
        os.environ["MODAL_TOKEN_ID"] = os.environ.get("MODAL_TOKEN_ID", "")
        os.environ["MODAL_TOKEN_SECRET"] = os.environ.get("MODAL_TOKEN_SECRET", "")
        
        proj["logs"].append("Mengirim permintaan pembuatan video ke Modal GPU...")
        proj["progress"] = 35
        save_history()
        
        Cls = modal.Cls.from_name("wan-video-horror", class_name)
        obj = Cls()
        
        proj["logs"].append("Memulai proses denoising Wan 2.1 pada GPU H100 (cold start mungkin memakan waktu 1-2 menit)...")
        proj["progress"] = 45
        save_history()
        
        # Standard scary negative prompt
        negative_prompt = "yellowness, low contrast, bad quality, worst quality, low resolution, watermarked, blurry, artifacts, cartoon, anime, 3d render"
        
        video_bytes = obj.generate.remote(
            prompt=proj["prompt_expanded"],
            negative_prompt=negative_prompt,
            num_frames=81,
            width=width,
            height=height,
            guidance_scale=payload.guidance,
            num_inference_steps=payload.steps,
            seed=payload.seed
        )
        
        proj["logs"].append("Video berhasil diproduksi di Modal. Mengunduh hasil video...")
        proj["progress"] = 85
        save_history()
        
        # Save video file locally
        out_name = f"{project_id}.mp4"
        out_path = OUTPUT_DIR / out_name
        with open(out_path, "wb") as f:
            f.write(video_bytes)
            
        proj["video_url"] = f"/api/video/output/{out_name}"
        proj["status"] = "completed"
        proj["progress"] = 100
        proj["logs"].append("Video selesai dibangkitkan sepenuhnya!")
        save_history()
        
    except Exception as e:
        logger.error(f"Video generation error for {project_id}: {str(e)}")
        proj["status"] = "failed"
        proj["progress"] = 100
        proj["logs"].append(f"Kesalahan pemrosesan: {str(e)}")
        save_history()

# API: Create generation project
@app.post("/api/generate")
async def generate_horror_video(payload: GenerateRequest, background_tasks: BackgroundTasks):
    # Retrieve API key
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY tidak diatur dalam file konfigurasi server.")
        
    project_id = str(uuid.uuid4())
    PROJECTS[project_id] = {
        "id": project_id,
        "prompt_original": payload.prompt,
        "prompt_expanded": "",
        "indonesian_caption": "",
        "ghost_type": payload.ghost_type,
        "model_type": payload.model_type,
        "aspect_ratio": payload.aspect_ratio,
        "status": "processing",
        "progress": 5,
        "logs": ["Memulai inisialisasi proyek Terranova..."],
        "video_url": None,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Check for reference image integration
    selected_image_pil = None
    ref_image_name = None
    if payload.ghost_type in GHOST_REFERENCES:
        ref_data = GHOST_REFERENCES[payload.ghost_type]
        # Pick a random image from list to maintain variety
        ref_image_name = random.choice(ref_data["images"])
        img_path = REF_DIR / ref_image_name
        if img_path.exists():
            try:
                selected_image_pil = Image.open(img_path)
                PROJECTS[project_id]["logs"].append(f"Menemukan gambar referensi: {ref_image_name}. Menganalisis estetika mistis...")
            except Exception as e:
                logger.error(f"Failed to load reference image {img_path}: {str(e)}")
    
    # 1. Trigger Gemini to expand prompt and translate to English, and get Indonesian caption
    try:
        client = genai.Client(api_key=gemini_key)
        
        contents = []
        if selected_image_pil:
            contents.append(selected_image_pil)
            
        ghost_context = ""
        if payload.ghost_type in GHOST_REFERENCES:
            ref_data = GHOST_REFERENCES[payload.ghost_type]
            ghost_context = f"The category is Indonesian Folklore Ghost: {ref_data['name']}. Description: {ref_data['description']}"
            
        system_instruction = (
            "You are a master Indonesian horror director. Your task is to translate and expand the user's idea into a highly cinematic, realistic text-to-video prompt in English for the Wan 2.1 model.\n"
            f"Context: {ghost_context}\n"
            "If an image is attached, treat it strictly as a visual folklore reference (for costume, hair, look, atmospheric lighting), but create a brand new original scene. DO NOT copy the image pose or composition.\n"
            "Rules for 'expanded_english_prompt':\n"
            "1. Must be in English.\n"
            "2. Describe realistic textures, spooky shadows, camera panning/movement, flickering candles/moonlight, and mist.\n"
            "3. Keep it terrifying and grounded in a dark Indonesian night setting.\n\n"
            "Rules for 'indonesian_caption':\n"
            "1. Must be in Bahasa Indonesia.\n"
            "2. Write a highly atmospheric, dark, spooky narrative or description of this generated video in 2-3 sentences. Make it poetic and chilling."
        )
        
        contents.append(f"{system_instruction}\n\nUser Input Idea: {payload.prompt}")
        
        PROJECTS[project_id]["logs"].append("Menghubungi Gemini 2.5 Flash untuk perluasan prompt...")
        PROJECTS[project_id]["progress"] = 15
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=HorrorPromptOutput,
            ),
        )
        
        # Load structured output
        res_json = json.loads(response.text)
        PROJECTS[project_id]["prompt_expanded"] = res_json.get("expanded_english_prompt", "")
        PROJECTS[project_id]["indonesian_caption"] = res_json.get("indonesian_caption", "")
        PROJECTS[project_id]["logs"].append(f"Prompt diperluas (Inggris): {res_json.get('expanded_english_prompt')[:60]}...")
        PROJECTS[project_id]["logs"].append("Takarir Bahasa Indonesia berhasil dibuat.")
        PROJECTS[project_id]["progress"] = 20
        save_history()
        
    except Exception as e:
        logger.error(f"Gemini generation failed: {str(e)}")
        PROJECTS[project_id]["status"] = "failed"
        PROJECTS[project_id]["logs"].append(f"Gemini LLM gagal: {str(e)}")
        save_history()
        return PROJECTS[project_id]
        
    # 2. Trigger background video generation
    background_tasks.add_task(generate_horror_video_task, project_id, payload)
    
    return PROJECTS[project_id]

# API: Stream execution logs via Server-Sent Events (SSE)
@app.get("/api/projects/{project_id}/logs/stream")
async def get_logs_stream(project_id: str):
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")
        
    async def log_generator():
        proj = PROJECTS[project_id]
        last_index = 0
        while proj["status"] == "processing" or last_index < len(proj["logs"]):
            if last_index < len(proj["logs"]):
                for i in range(last_index, len(proj["logs"])):
                    yield f"data: {json.dumps({'log': proj['logs'][i], 'progress': proj['progress'], 'status': proj['status']})}\n\n"
                last_index = len(proj["logs"])
            await asyncio.sleep(0.5)
        # Final status broadcast
        yield f"data: {json.dumps({'log': 'Siklus hidup pemrosesan proyek selesai.', 'progress': proj['progress'], 'status': proj['status']})}\n\n"
        
    return StreamingResponse(log_generator(), media_type="text/event-stream")

# Secure serving of output videos (prevents path traversal)
@app.get("/api/video/output/{filename}")
async def get_output_video(filename: str):
    # Prevent directory traversal securely by extracting base filename
    safe_filename = os.path.basename(filename)
    target_path = OUTPUT_DIR / safe_filename
    
    # Resolve absolute path boundaries strictly
    try:
        resolved_path = target_path.resolve()
        resolved_output_dir = OUTPUT_DIR.resolve()
        if not str(resolved_path).startswith(str(resolved_output_dir) + os.path.sep):
            raise HTTPException(status_code=403, detail="Akses ditolak.")
    except Exception:
         raise HTTPException(status_code=400, detail="Nama file tidak valid.")
         
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Video tidak ditemukan.")
        
    return FileResponse(target_path, media_type="video/mp4", filename=safe_filename)

# Mount reference images folder securely
app.mount("/reference-image", StaticFiles(directory=str(REF_DIR)), name="reference-image")

# Mount frontend static files
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Enforce localhost/127.0.0.1 for testing security by default, allow override in Docker
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8005))
    uvicorn.run("app:app", host=host, port=port, reload=True)
