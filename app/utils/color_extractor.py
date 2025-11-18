from PIL import Image
from fastapi import HTTPException
import io
from typing import List, Dict
import colorsys


def rgb_to_hue(rgb):
    """Convert RGB to hue value for rainbow sorting."""
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h


def rgb_to_luminosity(rgb):
    """Calculate luminosity of an RGB color."""
    r, g, b = rgb
    # Using the standard luminosity formula
    return 0.299 * r + 0.587 * g + 0.114 * b


def quantize_to_palette(image: Image.Image, num_colors: int) -> tuple:
    """
    Quantize image to exact number of colors using PIL's built-in quantization.
    Returns the quantized image and the palette colors with their counts.
    """
    # Use PIL's adaptive palette quantization (method=2 is MEDIANCUT)
    quantized = image.quantize(colors=num_colors, method=2)
    
    # Get the palette
    palette = quantized.getpalette()
    
    # Convert back to RGB to count colors
    quantized_rgb = quantized.convert('RGB')
    
    # Get colors and their counts from the quantized image
    colors = quantized_rgb.getcolors(maxcolors=num_colors + 10)
    
    return colors


def auto_detect_color_limit(image: Image.Image) -> int:
    """
    Automatically detect the optimal color limit for an image.
    This analyzes the image to find natural color groupings, ignoring compression artifacts.
    """
    # Resize for faster processing
    max_dimension = 400
    if image.width > max_dimension or image.height > max_dimension:
        image = image.copy()
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    
    # Get all unique colors
    colors = image.getcolors(maxcolors=10000)
    
    if colors is None:
        # Too many colors, likely a photo - default to 32
        return 32
    
    num_colors = len(colors)
    
    # If already very few colors, return that count
    if num_colors <= 8:
        return num_colors
    
    # For pixel art, we expect significant clustering
    # Try different palette sizes and find where the quality difference plateaus
    test_sizes = [8, 12, 16, 24, 32, 48, 64]
    
    # Find the smallest palette size that captures most of the color variation
    # We'll use a heuristic: if the image has many similar colors (compression artifacts),
    # a smaller palette will represent it well
    
    # Calculate color variance - if colors are very similar, we need fewer palette colors
    if num_colors <= 16:
        return min(num_colors, 16)
    elif num_colors <= 32:
        return min(num_colors, 24)
    elif num_colors <= 64:
        return 32
    elif num_colors <= 128:
        return 40
    elif num_colors <= 256:
        return 48
    else:
        # Likely a complex image or photo
        return 64


def extract_colors(image_bytes: bytes, sort_by: str = 'frequency', limit: int = None, auto_limit: bool = False) -> List[Dict[str, str]]:
    """Extract unique colors from an image."""
    try:
        # Open image and convert to RGB
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert('RGB')
        
        # Auto-detect limit if requested
        if auto_limit:
            limit = auto_detect_color_limit(image)
        
        # Optimization: Resize very large images
        max_dimension = 800
        if image.width > max_dimension or image.height > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # If a color limit is specified, quantize the image to that exact number of colors
        if limit and limit > 0:
            # Use PIL's quantization to reduce to exact number of colors
            colors = quantize_to_palette(image, limit)
        else:
            # No limit specified, extract all unique colors (with some optimizations)
            colors = image.getcolors(maxcolors=1024)
            
            if colors is None:
                # Too many colors, use quantization to reduce complexity
                colors = quantize_to_palette(image, 256)
            
            # If still too many colors, limit to 512 max
            if colors and len(colors) > 512:
                colors = quantize_to_palette(image, 128)
        
        # Calculate total pixels
        total_pixels = sum(count for count, _ in colors)
        
        # Convert to hex format
        color_list = []
        for count, rgb in colors:
            hex_color = '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
            percentage = (count / total_pixels) * 100
            color_list.append({
                'hex': hex_color,
                'rgb': f'rgb({rgb[0]}, {rgb[1]}, {rgb[2]})',
                'rgb_tuple': rgb,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        # Sort based on the requested method
        if sort_by == 'luminosity':
            color_list.sort(key=lambda x: rgb_to_luminosity(x['rgb_tuple']), reverse=True)
        elif sort_by == 'rainbow':
            color_list.sort(key=lambda x: rgb_to_hue(x['rgb_tuple']))
        else:  # frequency (default)
            color_list.sort(reverse=True, key=lambda x: x['count'])
        
        # Remove rgb_tuple from output
        for color in color_list:
            del color['rgb_tuple']
        
        return color_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")



