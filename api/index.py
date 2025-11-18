import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.main import app
    # Vercel serverless function handler
    handler = app
except Exception as e:
    # Create a simple error handler if import fails
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    handler = FastAPI()
    
    @handler.get("/{full_path:path}")
    async def error_handler(full_path: str):
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to load application: {str(e)}"}
        )
