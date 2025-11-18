from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse, Response
from pathlib import Path
from typing import Dict
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.color_extractor import extract_colors

app = FastAPI(title="Image Color Palette Extractor")

# Get the base directory
BASE_DIR = Path(__file__).parent.parent / "app"

@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon."""
    return Response(status_code=204)


@app.get("/static/css/styles.css")
async def get_styles():
    """Serve CSS file."""
    css_path = BASE_DIR / "static" / "css" / "styles.css"
    if css_path.exists():
        return FileResponse(str(css_path), media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS not found")


@app.get("/static/js/app.js")
async def get_js():
    """Serve JavaScript file."""
    js_path = BASE_DIR / "static" / "js" / "app.js"
    if js_path.exists():
        return FileResponse(str(js_path), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JS not found")


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main HTML page."""
    template_path = BASE_DIR / "templates" / "index.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    raise HTTPException(status_code=404, detail="Template not found")


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
