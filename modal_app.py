import os
import modal

# Define cache volume
CACHE_DIR = "/models"
cache_vol = modal.Volume.from_name("models", create_if_missing=True)

# Define container image
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git")
    .pip_install(
        "torch>=2.4.0",
        "transformers>=4.48.0",
        "accelerate>=1.3.0",
        "sentencepiece>=0.2.0",
        "decord>=0.6.0",
        "numpy>=1.26.0",
        "pillow>=10.0.0",
        "huggingface_hub>=0.28.0",
        "opencv-python-headless>=4.0.0",
        "imageio>=2.30.0",
        "imageio-ffmpeg>=0.4.8"
    )
    .pip_install("git+https://github.com/huggingface/diffusers.git") # diffusers from main for WanPipeline
)

app = modal.App("wan-video-horror", image=image)

@app.cls(
    gpu="A10G",
    timeout=600,
    volumes={CACHE_DIR: cache_vol},
    env={"HF_HOME": f"{CACHE_DIR}/huggingface", "HF_HUB_ENABLE_HF_TRANSFER": "1"}
)
class Wan13BModel:
    @modal.enter()
    def load_model(self):
        import torch
        from diffusers import WanPipeline
        
        print("Loading Wan2.1 1.3B Model...")
        model_id = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
        self.pipe = WanPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            cache_dir=f"{CACHE_DIR}/huggingface"
        )
        self.pipe.to("cuda")
        print("Wan2.1 1.3B Model Loaded Successfully.")

    @modal.method()
    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        num_frames: int = 81,
        width: int = 832,
        height: int = 480,
        guidance_scale: float = 5.0,
        num_inference_steps: int = 30,
        seed: int = -1
    ) -> bytes:
        import torch
        import tempfile
        import os
        from diffusers.utils import export_to_video
        
        print(f"Generating video (1.3B) for prompt: '{prompt}'")
        
        generator = None
        if seed != -1:
            generator = torch.Generator(device="cuda").manual_seed(seed)
            
        video = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=num_frames,
            width=width,
            height=height,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator
        ).frames[0]
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmpfile:
            export_to_video(video, tmpfile.name, fps=16)
            tmpfile.seek(0)
            video_bytes = tmpfile.read()
            
        try:
            os.unlink(tmpfile.name)
        except Exception:
            pass
            
        print("Video generation (1.3B) completed.")
        return video_bytes


@app.cls(
    gpu="A10G",
    timeout=600,
    volumes={CACHE_DIR: cache_vol},
    env={"HF_HOME": f"{CACHE_DIR}/huggingface", "HF_HUB_ENABLE_HF_TRANSFER": "1"}
)
class Wan14BModel:
    @modal.enter()
    def load_model(self):
        import torch
        from diffusers import WanPipeline
        
        print("Loading Wan2.1 14B Model...")
        model_id = "Wan-AI/Wan2.1-T2V-14B-Diffusers"
        self.pipe = WanPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            cache_dir=f"{CACHE_DIR}/huggingface"
        )
        self.pipe.enable_model_cpu_offload()
        print("Wan2.1 14B Model Loaded Successfully.")

    @modal.method()
    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        num_frames: int = 81,
        width: int = 832,
        height: int = 480,
        guidance_scale: float = 5.0,
        num_inference_steps: int = 30,
        seed: int = -1
    ) -> bytes:
        import torch
        import tempfile
        import os
        from diffusers.utils import export_to_video
        
        print(f"Generating video (14B) for prompt: '{prompt}'")
        
        generator = None
        if seed != -1:
            generator = torch.Generator(device="cuda").manual_seed(seed)
            
        video = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=num_frames,
            width=width,
            height=height,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator
        ).frames[0]
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmpfile:
            export_to_video(video, tmpfile.name, fps=16)
            tmpfile.seek(0)
            video_bytes = tmpfile.read()
            
        try:
            os.unlink(tmpfile.name)
        except Exception:
            pass
            
        print("Video generation (14B) completed.")
        return video_bytes
