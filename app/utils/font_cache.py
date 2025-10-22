"""Font cache utility for storing downloaded fonts in memory.

This module provides a simple in-memory cache for font data to avoid
redundant downloads within the same session.
"""

from typing import Optional


class FontCache:
    """In-memory cache for storing downloaded font data.
    
    Attributes:
        _cache: Dictionary mapping font URLs to font bytes.
    """
    
    def __init__(self) -> None:
        """Initialize an empty font cache."""
        self._cache: dict[str, bytes] = {}
    
    def get_font(self, url: str) -> Optional[bytes]:
        """Retrieve font data from cache by URL.
        
        Args:
            url: The URL of the font to retrieve.
            
        Returns:
            Font data as bytes if found in cache, None otherwise.
        """
        return self._cache.get(url)
    
    def set_font(self, url: str, font_data: bytes) -> None:
        """Store font data in cache.
        
        Args:
            url: The URL of the font to cache.
            font_data: The font file data as bytes.
        """
        self._cache[url] = font_data
    
    def clear_font(self, url: str) -> None:
        """Remove a font from the cache.
        
        This is useful for error recovery when a cached font fails to load.
        
        Args:
            url: The URL of the font to remove from cache.
        """
        self._cache.pop(url, None)


# Global font cache instance
_font_cache = FontCache()


def get_font_cache() -> FontCache:
    """Get the global font cache instance.
    
    Returns:
        The global FontCache instance.
    """
    return _font_cache

