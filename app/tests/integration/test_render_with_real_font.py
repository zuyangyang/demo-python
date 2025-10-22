"""Integration tests for text rendering with real font URLs."""

import pytest

from app.services.text_render_service import _download_font
from app.utils.font_cache import get_font_cache


class TestRealFontDownload:
    """Integration tests with real font URLs."""
    
    def setup_method(self) -> None:
        """Clear font cache before each test."""
        cache = get_font_cache()
        cache._cache.clear()
    
    @pytest.mark.integration
    def test_download_real_font_moresugar(self) -> None:
        """Test downloading a real OTF font from Canva CDN."""
        font_url = (
            "https://font-public.canva.com/YAFdJkVWBPo/0/"
            "MoreSugar-Regular.62992e429acdec5e01c3db.6f7a950ef2bb9f1314d37ac4a660925e.otf"
        )
        
        # Download font
        font_data = _download_font(font_url)
        
        # Verify font data is not empty
        assert font_data is not None
        assert len(font_data) > 0
        assert isinstance(font_data, bytes)
        
        # Verify OTF signature (starts with 'OTTO' for OTF fonts)
        assert font_data[:4] == b'OTTO', "Font should have OTF signature"
    
    @pytest.mark.integration
    def test_real_font_caching_works(self) -> None:
        """Verify that real font is cached after first download."""
        font_url = (
            "https://font-public.canva.com/YAFdJkVWBPo/0/"
            "MoreSugar-Regular.62992e429acdec5e01c3db.6f7a950ef2bb9f1314d37ac4a660925e.otf"
        )
        cache = get_font_cache()
        
        # First download
        font_data_1 = _download_font(font_url)
        
        # Verify it's in cache
        cached_data = cache.get_font(font_url)
        assert cached_data is not None
        assert cached_data == font_data_1
        
        # Second call should return same data from cache
        font_data_2 = _download_font(font_url)
        assert font_data_2 == font_data_1
        assert font_data_2 is cached_data  # Should be same object reference
    
    @pytest.mark.integration
    def test_download_invalid_url_raises_error(self) -> None:
        """Test that invalid URL raises appropriate error."""
        import requests
        
        invalid_url = "https://font-public.canva.com/nonexistent/font.otf"
        
        with pytest.raises(requests.HTTPError):
            _download_font(invalid_url)
