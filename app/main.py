from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict
from .utils.color_extractor import extract_colors

app = FastAPI(title="Image Color Palette Extractor")

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main HTML page."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/extract-colors")
async def extract_colors_endpoint(file: UploadFile = File(...), sort_by: str = 'frequency', limit: int = None):
    """Extract colors from uploaded image."""
    contents = await file.read()
    colors = extract_colors(contents, sort_by, limit)
    
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
        colors = extract_colors(image_bytes, sort_by, limit)
        
        return {
            "colors": colors,
            "total_colors": len(colors)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")
