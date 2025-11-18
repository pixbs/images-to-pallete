# Image Color Palette Extractor 🎨

A web application that extracts all unique colors from an image and displays them with the ability to copy color codes.

## Features

- 🖼️ Upload images (PNG, JPG, etc.)
- 📋 Paste images directly from clipboard (Ctrl+V)
- 🎨 Extract all unique colors from the image
- 🌈 Sort colors by:
  - Frequency (most common first)
  - Luminosity (brightest to darkest)
  - Rainbow spectrum (red → violet)
- 📊 Shows hex code, RGB values, percentage, and pixel count
- 💅 Beautiful, responsive UI
- ✨ Click any color to copy its hex code

## Project Structure

```
images-to-pallete/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css      # Styles
│   │   └── js/
│   │       └── app.js          # Frontend JavaScript
│   ├── templates/
│   │   └── index.html          # HTML template
│   └── utils/
│       ├── __init__.py
│       └── color_extractor.py  # Color extraction logic
├── hello.py                    # Development entry point
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project configuration
├── vercel.json                # Vercel deployment config
└── README.md
```

## Local Development

1. Install dependencies:
```bash
uv sync
```

2. Run the application:
```bash
uv run python hello.py
```

Or using uvicorn directly:
```bash
uv run uvicorn app.main:app --reload
```

3. Open your browser and navigate to:
```
http://localhost:8000
```

## Deploy to Vercel

1. Install Vercel CLI (if not already installed):
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel
```

Or connect your GitHub repository to Vercel for automatic deployments.

### Vercel Configuration

The project includes `vercel.json` with the proper configuration for FastAPI deployment. The static files are served from the `app/static` directory.

## Usage

1. **Upload**: Click "Choose Image" to select an image file
2. **Paste**: Press Ctrl+V to paste an image from clipboard
3. **Sort**: Use the dropdown to change color sorting order
4. **Copy**: Click any color card to copy its hex code to clipboard

## Technologies Used

- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pillow** - Image processing library
- **HTML/CSS/JavaScript** - Frontend
- **Vercel** - Deployment platform

## API Endpoints

### `GET /`
Returns the main HTML interface

### `POST /extract-colors`
Extracts colors from uploaded image
- **Parameters**: 
  - `file`: Image file (multipart/form-data)
  - `sort_by`: Optional sorting method (`frequency`, `luminosity`, `rainbow`)
- **Returns**: JSON with colors array and total count

### `POST /extract-colors-base64`
Extracts colors from base64 encoded image
- **Body**: JSON with `image` (base64 string) and optional `sort_by`
- **Returns**: JSON with colors array and total count
