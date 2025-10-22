"""Integration tests for text rendering with real font URLs."""

import io
import tempfile
import pytest
from PIL import Image

from app.services.text_render_service import _download_font, render_text
from app.utils.font_cache import get_font_cache


# Real font URLs for testing
# Using Canva CDN font URL which is known to work
TEST_FONT_URL = (
    "https://font-public.canva.com/YAFdJkVWBPo/0/"
    "MoreSugar-Regular.62992e429acdec5e01c3db.6f7a950ef2bb9f1314d37ac4a660925e.otf"
)


class TestRealFontDownload:
    """Integration tests with real font URLs."""
    
    def setup_method(self) -> None:
        """Clear font cache before each test."""
        cache = get_font_cache()
        cache._cache.clear()
    
    @pytest.mark.integration
    def test_download_real_font_moresugar(self) -> None:
        """Test downloading a real OTF font from Canva CDN."""
        font_url = TEST_FONT_URL
        
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
        font_url = TEST_FONT_URL
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


class TestRenderTextIntegration:
    """End-to-end integration tests for render_text function."""
    
    def setup_method(self) -> None:
        """Clear font cache before each test."""
        cache = get_font_cache()
        cache._cache.clear()
    
    @pytest.mark.integration
    def test_render_with_google_fonts(self) -> None:
        """Test end-to-end rendering with real font from CDN."""
        # Render text with real font
        image_bytes = render_text(
            font_url=TEST_FONT_URL,
            text="Hello, World!",
            font_size=48.0,
            padding=20
        )
        
        # Verify we got bytes back
        assert image_bytes is not None
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        
        # Verify it's a valid PNG by checking header
        assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n', "Should have PNG signature"
    
    @pytest.mark.integration
    def test_png_output_is_valid(self) -> None:
        """Verify PNG output is valid and can be opened by PIL."""
        # Render text
        image_bytes = render_text(
            font_url=TEST_FONT_URL,
            text="Test Image",
            font_size=36.0,
            padding=15
        )
        
        # Check PNG header signature
        assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'
        
        # Try to open with PIL
        image = Image.open(io.BytesIO(image_bytes))
        assert image.mode == 'RGB'
        assert image.width > 0
        assert image.height > 0
        
        # Save to temporary file and verify it can be read back
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name
        
        # Read back the saved file
        saved_image = Image.open(tmp_path)
        assert saved_image.mode == 'RGB'
        assert saved_image.size == image.size
        
        # Clean up
        import os
        os.unlink(tmp_path)
    
    @pytest.mark.integration
    def test_multiple_font_sizes(self) -> None:
        """Test rendering with different font sizes."""
        test_sizes = [12.0, 24.0, 48.0]
        previous_size = 0
        
        for font_size in test_sizes:
            image_bytes = render_text(
                font_url=TEST_FONT_URL,
                text="Size Test",
                font_size=font_size,
                padding=10
            )
            
            # Verify valid PNG
            assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'
            
            # Open and check dimensions
            image = Image.open(io.BytesIO(image_bytes))
            image_size = image.width * image.height
            
            # Larger font size should produce larger image (generally)
            assert image_size > previous_size, (
                f"Font size {font_size} should produce larger image than previous"
            )
            previous_size = image_size
    
    @pytest.mark.integration
    def test_different_padding(self) -> None:
        """Test rendering with different padding values."""
        test_paddings = [0, 10, 50]
        previous_size = 0
        
        for padding in test_paddings:
            image_bytes = render_text(
                font_url=TEST_FONT_URL,
                text="Padding Test",
                font_size=24.0,
                padding=padding
            )
            
            # Verify valid PNG
            assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'
            
            # Open and check dimensions
            image = Image.open(io.BytesIO(image_bytes))
            image_size = image.width * image.height
            
            # More padding should produce larger image
            assert image_size >= previous_size, (
                f"Padding {padding} should produce same or larger image than previous"
            )
            previous_size = image_size
    
    @pytest.mark.integration
    def test_unicode_text_rendering(self) -> None:
        """Test rendering with Unicode text (emoji and CJK characters)."""
        # Test with emoji
        emoji_bytes = render_text(
            font_url=TEST_FONT_URL,
            text="Hello 😊 World!",
            font_size=36.0,
            padding=20
        )
        assert emoji_bytes[:8] == b'\x89PNG\r\n\x1a\n'
        
        # Test with CJK characters
        cjk_bytes = render_text(
            font_url=TEST_FONT_URL,
            text="你好世界",
            font_size=36.0,
            padding=20
        )
        assert cjk_bytes[:8] == b'\x89PNG\r\n\x1a\n'
        
        # Test with mixed Unicode
        mixed_bytes = render_text(
            font_url=TEST_FONT_URL,
            text="Test 测试 テスト 🎨",
            font_size=36.0,
            padding=20
        )
        assert mixed_bytes[:8] == b'\x89PNG\r\n\x1a\n'
        
        # All should be valid images
        for image_bytes in [emoji_bytes, cjk_bytes, mixed_bytes]:
            image = Image.open(io.BytesIO(image_bytes))
            assert image.mode == 'RGB'
            assert image.width > 0
            assert image.height > 0
    
    @pytest.mark.integration
    def test_font_caching_works(self) -> None:
        """Verify font caching works across multiple render_text calls."""
        cache = get_font_cache()
        
        # First render - should download font
        image_bytes_1 = render_text(
            font_url=TEST_FONT_URL,
            text="First Call",
            font_size=24.0,
            padding=10
        )
        
        # Verify font is cached
        cached_font = cache.get_font(TEST_FONT_URL)
        assert cached_font is not None
        
        # Second render - should use cached font
        image_bytes_2 = render_text(
            font_url=TEST_FONT_URL,
            text="Second Call",
            font_size=24.0,
            padding=10
        )
        
        # Both should be valid PNGs
        assert image_bytes_1[:8] == b'\x89PNG\r\n\x1a\n'
        assert image_bytes_2[:8] == b'\x89PNG\r\n\x1a\n'
        
        # Verify cache still has the same font
        cached_font_after = cache.get_font(TEST_FONT_URL)
        assert cached_font_after is cached_font  # Same object reference
