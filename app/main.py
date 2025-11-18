from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict
import os

# Import from absolute path for Vercel
try:
    from app.utils.color_extractor import extract_colors
except ImportError:
    from .utils.color_extractor import extract_colors

app = FastAPI(title="Image Color Palette Extractor")

# Get the base directory
BASE_DIR = Path(__file__).parent

# Mount static files only if not on Vercel
if not os.environ.get('VERCEL'):
    static_path = BASE_DIR / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/static/css/styles.css")
async def get_styles():
    """Serve CSS file."""
    css_path = BASE_DIR / "static" / "css" / "styles.css"
    if not css_path.exists():
        raise HTTPException(status_code=404, detail="CSS file not found")
    return FileResponse(css_path, media_type="text/css")


@app.get("/static/js/app.js")
async def get_js():
    """Serve JavaScript file."""
    js_path = BASE_DIR / "static" / "js" / "app.js"
    if not js_path.exists():
        raise HTTPException(status_code=404, detail="JS file not found")
    return FileResponse(js_path, media_type="application/javascript")


@app.get("/favicon.ico")
async def get_favicon():
    """Handle favicon requests."""
    from fastapi.responses import Response
    # Return empty response for favicon
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main HTML page."""
    template_path = BASE_DIR / "templates" / "index.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/extract-colors")
async def extract_colors_endpoint(file: UploadFile = File(...), sort_by: str = 'frequency', limit: int = None, auto_limit: bool = False):
    """Extract colors from uploaded image."""
    contents = await file.read()
    colors = extract_colors(contents, sort_by, limit, auto_limit)
    
    return {
        "colors": colors,
        "total_colors": len(colors)
    }


@app.post("/extract-colors-base64")
async def extract_colors_base64(data: Dict = Body(...)):
    """Extract colors from base64 encoded image."""
    try:
        import base64
        
        base64_string = data.get('image', '')
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_bytes = base64.b64decode(base64_string)
        sort_by = data.get('sort_by', 'frequency')
        limit = data.get('limit')
        auto_limit = data.get('auto_limit', False)
        colors = extract_colors(image_bytes, sort_by, limit, auto_limit)
        
        return {
            "colors": colors,
            "total_colors": len(colors)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")
