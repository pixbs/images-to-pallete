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


def color_distance(rgb1, rgb2):
    """Calculate the Euclidean distance between two RGB colors."""
    return sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5


def quantize_image_colors(image: Image.Image, max_colors: int = 256) -> Image.Image:
    """Reduce the number of colors in an image using quantization."""
    # Convert to P mode (palette mode) with adaptive palette
    return image.quantize(colors=max_colors, method=2)


def merge_similar_colors(color_list: List[Dict], max_colors: int) -> List[Dict]:
    """Merge similar colors to reduce palette to max_colors while maintaining balance."""
    if len(color_list) <= max_colors:
        return color_list
    
    # Create a working copy with rgb_tuple
    working_colors = []
    for color in color_list:
        # Parse RGB from string
        rgb_str = color['rgb'].replace('rgb(', '').replace(')', '')
        r, g, b = map(int, rgb_str.split(', '))
        working_colors.append({
            **color,
            'rgb_tuple': (r, g, b)
        })
    
    # Keep merging until we reach the target
    while len(working_colors) > max_colors:
        # Find the two most similar colors
        min_distance = float('inf')
        merge_i, merge_j = 0, 1
        
        for i in range(len(working_colors)):
            for j in range(i + 1, len(working_colors)):
                distance = color_distance(working_colors[i]['rgb_tuple'], working_colors[j]['rgb_tuple'])
                if distance < min_distance:
                    min_distance = distance
                    merge_i, merge_j = i, j
        
        # Merge the two colors (keep the one with higher count)
        color_a = working_colors[merge_i]
        color_b = working_colors[merge_j]
        
        # Determine which color to keep based on count
        if color_a['count'] >= color_b['count']:
            keep_idx, remove_idx = merge_i, merge_j
        else:
            keep_idx, remove_idx = merge_j, merge_i
        
        # Merge counts and recalculate percentage
        working_colors[keep_idx]['count'] += working_colors[remove_idx]['count']
        
        # Remove the merged color
        working_colors.pop(remove_idx)
    
    # Recalculate percentages
    total_pixels = sum(c['count'] for c in working_colors)
    for color in working_colors:
        color['percentage'] = round((color['count'] / total_pixels) * 100, 2)
        # Remove rgb_tuple before returning
        if 'rgb_tuple' in color:
            del color['rgb_tuple']
    
    return working_colors


def extract_colors(image_bytes: bytes, sort_by: str = 'frequency', limit: int = None) -> List[Dict[str, str]]:
    """Extract unique colors from an image."""
    try:
        # Open image and convert to RGB
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert('RGB')
        
        # Optimization 1: Resize very large images
        max_dimension = 800
        if image.width > max_dimension or image.height > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # Optimization 2: Pre-quantize if image has too many colors
        # This significantly speeds up processing for complex images
        colors = image.getcolors(maxcolors=1024)
        
        if colors is None:
            # Too many colors, use quantization to reduce complexity
            image = quantize_image_colors(image, max_colors=256)
            image = image.convert('RGB')
            colors = image.getcolors(maxcolors=1000000)
        
        # Optimization 3: If still too many colors after quantization, limit further
        if colors and len(colors) > 512:
            # Apply more aggressive quantization
            image = quantize_image_colors(image, max_colors=128)
            image = image.convert('RGB')
            colors = image.getcolors(maxcolors=1000000)
        
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
        
        # Optimization 4: Cap at 64 colors max before sorting
        if len(color_list) > 64:
            # Sort by frequency and take top 64
            color_list.sort(reverse=True, key=lambda x: x['count'])
            color_list = color_list[:64]
            # Recalculate percentages after filtering
            total_pixels = sum(c['count'] for c in color_list)
            for color in color_list:
                color['percentage'] = round((color['count'] / total_pixels) * 100, 2)
        
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
        
        # Apply color limit if specified
        if limit and limit > 0:
            color_list = merge_similar_colors(color_list, limit)
            
            # Re-sort after merging
            if sort_by == 'frequency':
                color_list.sort(reverse=True, key=lambda x: x['count'])
        
        return color_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


