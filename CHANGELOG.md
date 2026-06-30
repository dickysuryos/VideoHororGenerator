# Changelog

All notable changes to **Project Terranova** will be documented in this file.

---

## [1.0.1] - 2026-06-30

### Fixed
- Fixed container export failures by adding `opencv-python-headless`, `imageio`, and `imageio-ffmpeg` to the serverless container definition in `modal_app.py`.
- Resolved deprecation warnings regarding legacy OpenCV export backends in HF Diffusers' `export_to_video`.

### Added
- Added `README.md` containing local setup and remote Modal.com deployment guidelines.
- Added `.env-example` configuration template.
- Verified system functionality using full integration script tests, writing completed outputs under `output/`.

---

## [1.0.0] - 2026-06-29

### Added
- Created backend BFF in `app.py` utilizing FastAPI, Server-Sent Events (SSE) log streams, and path traversal shields for local outputs.
- Developed `modal_app.py` serverless class structures with persistent cache Volume setups for loading Wan2.1 T2V 1.3B and 14B models on A10G GPUs with CPU offloading hooks.
- Implemented Gemini 2.5 Flash logic to analyze folklore ghost references and expand prompts into cinematic English descriptions alongside narrative Indonesian captions.
- Built interactive spooky dark web frontend interface under `static/` with floating mist animations, candles loaders, flickering layouts, and real-time SSE console displays.
