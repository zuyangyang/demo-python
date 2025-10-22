"""Unit tests for font cache utility."""

from app.utils.font_cache import FontCache


class TestFontCache:
    """Test suite for FontCache class."""
    
    def test_set_and_get_font(self) -> None:
        """Verify font data is stored and retrieved correctly."""
        cache = FontCache()
        url = "https://example.com/font.otf"
        font_data = b"fake font data"
        
        cache.set_font(url, font_data)
        retrieved = cache.get_font(url)
        
        assert retrieved == font_data
    
    def test_get_nonexistent_font(self) -> None:
        """Verify returns None for missing URL."""
        cache = FontCache()
        url = "https://example.com/nonexistent.otf"
        
        retrieved = cache.get_font(url)
        
        assert retrieved is None
    
    def test_clear_font(self) -> None:
        """Verify font is removed from cache."""
        cache = FontCache()
        url = "https://example.com/font.otf"
        font_data = b"fake font data"
        
        cache.set_font(url, font_data)
        assert cache.get_font(url) == font_data
        
        cache.clear_font(url)
        assert cache.get_font(url) is None
    
    def test_cache_multiple_fonts(self) -> None:
        """Verify multiple fonts can coexist in cache."""
        cache = FontCache()
        url1 = "https://example.com/font1.otf"
        url2 = "https://example.com/font2.otf"
        url3 = "https://example.com/font3.otf"
        font_data1 = b"font data 1"
        font_data2 = b"font data 2"
        font_data3 = b"font data 3"
        
        cache.set_font(url1, font_data1)
        cache.set_font(url2, font_data2)
        cache.set_font(url3, font_data3)
        
        assert cache.get_font(url1) == font_data1
        assert cache.get_font(url2) == font_data2
        assert cache.get_font(url3) == font_data3
    
    def test_clear_nonexistent_font_no_error(self) -> None:
        """Verify clearing a nonexistent font doesn't raise an error."""
        cache = FontCache()
        url = "https://example.com/nonexistent.otf"
        
        # Should not raise any exception
        cache.clear_font(url)
    
    def test_overwrite_existing_font(self) -> None:
        """Verify that setting the same URL overwrites previous data."""
        cache = FontCache()
        url = "https://example.com/font.otf"
        font_data1 = b"original font data"
        font_data2 = b"updated font data"
        
        cache.set_font(url, font_data1)
        assert cache.get_font(url) == font_data1
        
        cache.set_font(url, font_data2)
        assert cache.get_font(url) == font_data2

