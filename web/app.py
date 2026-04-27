from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
import uvicorn
import os

# Create FastAPI app for web UI
web_app = FastAPI(title="MxmzaPro Web UI")

# Setup templates
templates = Jinja2Templates(directory="web/templates")

# Mount static files
if os.path.exists("web/static"):
    web_app.mount("/static", StaticFiles(directory="web/static"), name="static")

@web_app.get("/", response_class=HTMLResponse)
async def web_dashboard(request: Request):
    """Serve the web dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@web_app.get("/health")
async def health():
    return {"status": "🔥 MxmzaPro Web UI is running"}

def start_web(host: str = "0.0.0.0", port: int = 8081):
    """Start web UI server"""
    uvicorn.run(web_app, host=host, port=port, log_level="info")
