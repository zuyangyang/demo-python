"""Text rendering service for converting text to PNG images.

This module provides functionality to download OTF fonts and render
text into PNG images with custom styling.
"""

import io

import requests
from PIL import Image, ImageDraw, ImageFont
from app.utils.font_cache import get_font_cache


def _download_font(font_url: str) -> bytes:
    """Download font file from URL with caching support.
    
    This function first checks the cache for the font. If not found,
    it downloads the font from the provided URL and stores it in cache
    for future use.
    
    Args:
        font_url: HTTP/HTTPS URL to the font file.
        
    Returns:
        Font file data as bytes.
        
    Raises:
        requests.HTTPError: If the HTTP request fails or returns non-200 status.
        requests.Timeout: If the request exceeds the 30-second timeout.
        requests.RequestException: For other request-related errors.
    """
    cache = get_font_cache()
    
    # Check cache first
    cached_font = cache.get_font(font_url)
    if cached_font is not None:
        return cached_font
    
    # Download font with timeout
    response = requests.get(font_url, timeout=30)
    response.raise_for_status()
    
    font_data = response.content
    
    # Store in cache
    cache.set_font(font_url, font_data)
    
    return font_data


def _calculate_dimensions(
    text: str, font: ImageFont.FreeTypeFont, padding: int
) -> tuple[int, int]:
    """Calculate image dimensions based on text size and padding.
    
    Uses ImageDraw.textbbox() to measure the text dimensions and adds
    padding on all sides to determine the final image size.
    
    Args:
        text: The text to measure.
        font: PIL FreeTypeFont object to use for text measurement.
        padding: Padding in pixels to add around the text.
        
    Returns:
        A tuple of (width, height) for the final image dimensions.
    """
    # Create a temporary image to measure text
    temp_image = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(temp_image)
    
    # Get bounding box of the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Add padding on all sides
    width = text_width + (padding * 2)
    height = text_height + (padding * 2)
    
    return (width, height)


def _create_image(
    width: int,
    height: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    padding: int
) -> Image.Image:
    """Create an image with centered text on white background.
    
    Creates an RGB image with white background and draws the provided
    text in black, centered both horizontally and vertically.
    
    Args:
        width: Width of the image in pixels.
        height: Height of the image in pixels.
        text: The text to render.
        font: PIL FreeTypeFont object to use for text rendering.
        padding: Padding in pixels (used for position calculation).
        
    Returns:
        PIL Image object with rendered text.
    """
    # Create white background canvas
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Calculate text position for centering
    # Get bounding box to determine text dimensions
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text in black
    draw.text((x, y), text, font=font, fill='black')
    
    return image


def render_text(font_url: str, text: str, font_size: float, padding: int) -> bytes:
    """Render text to PNG image using downloadable OTF font.
    
    Downloads an OTF font from the provided URL (with caching), renders
    the given text with specified styling, and returns the result as PNG
    image bytes. The text is rendered in black on a white background,
    centered both horizontally and vertically with the specified padding.
    
    Args:
        font_url: HTTP/HTTPS URL to OTF font file.
        text: Text content to render (supports Unicode).
        font_size: Font size in points (must be positive).
        padding: Padding around text in pixels (must be non-negative).
        
    Returns:
        PNG image as bytes.
        
    Raises:
        ValueError: If text is empty, font_size is negative, or padding is negative.
        requests.HTTPError: If font download fails or returns non-200 status.
        requests.Timeout: If font download exceeds 30-second timeout.
        requests.RequestException: For other network-related errors.
        IOError: If font file is invalid or unsupported format.
        
    Example:
        >>> font_url = "https://example.com/font.otf"
        >>> image_bytes = render_text(font_url, "Hello", 48.0, 20)
        >>> with open("output.png", "wb") as f:
        ...     f.write(image_bytes)
    """
    # Validate parameters
    if not text or text.strip() == "":
        raise ValueError("Text cannot be empty")
    
    if font_size <= 0:
        raise ValueError("Font size must be positive")
    
    if padding < 0:
        raise ValueError("Padding cannot be negative")
    
    # Download font (with caching)
    font_data = _download_font(font_url)
    
    # Load font from bytes
    cache = get_font_cache()
    try:
        font_bytesio = io.BytesIO(font_data)
        font = ImageFont.truetype(font_bytesio, size=font_size)
    except Exception as e:
        # Clear cache entry if font fails to load
        cache.clear_font(font_url)
        raise IOError(f"Failed to load font from {font_url}: {e}") from e
    
    # Calculate image dimensions
    width, height = _calculate_dimensions(text, font, padding)
    
    # Create image with rendered text
    image = _create_image(width, height, text, font, padding)
    
    # Convert image to PNG bytes
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()

