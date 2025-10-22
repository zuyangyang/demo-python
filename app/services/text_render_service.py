"""Text rendering service for converting text to PNG images.

This module provides functionality to download OTF fonts and render
text into PNG images with custom styling.
"""

import requests
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

