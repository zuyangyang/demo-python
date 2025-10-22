"""Unit tests for text rendering service."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from PIL import Image, ImageFont

from app.services.text_render_service import (
    _calculate_dimensions,
    _create_image,
    _download_font,
)
from app.utils.font_cache import get_font_cache


class TestDownloadFont:
    """Test suite for font download functionality."""
    
    def setup_method(self) -> None:
        """Clear font cache before each test."""
        cache = get_font_cache()
        cache._cache.clear()
    
    def test_download_font_success(self) -> None:
        """Verify font bytes are returned on successful download."""
        mock_font_data = b"fake font data"
        
        with patch("app.services.text_render_service.requests.get") as mock_get:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.content = mock_font_data
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = _download_font("https://example.com/font.otf")
            
            assert result == mock_font_data
            mock_get.assert_called_once_with("https://example.com/font.otf", timeout=30)
            mock_response.raise_for_status.assert_called_once()
    
    def test_download_font_404(self) -> None:
        """Verify HTTPError is raised for 404 status code."""
        with patch("app.services.text_render_service.requests.get") as mock_get:
            # Mock 404 response
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            with pytest.raises(requests.HTTPError, match="404 Not Found"):
                _download_font("https://example.com/nonexistent.otf")
    
    def test_download_font_timeout(self) -> None:
        """Verify timeout error is properly raised."""
        with patch("app.services.text_render_service.requests.get") as mock_get:
            # Mock timeout
            mock_get.side_effect = requests.Timeout("Request timed out")
            
            with pytest.raises(requests.Timeout, match="Request timed out"):
                _download_font("https://example.com/slow-font.otf")
            
            mock_get.assert_called_once_with("https://example.com/slow-font.otf", timeout=30)
    
    def test_download_font_uses_cache(self) -> None:
        """Verify cache hit avoids making HTTP request."""
        cache = get_font_cache()
        font_url = "https://example.com/cached-font.otf"
        cached_data = b"cached font data"
        
        # Pre-populate cache
        cache.set_font(font_url, cached_data)
        
        with patch("app.services.text_render_service.requests.get") as mock_get:
            result = _download_font(font_url)
            
            # Should return cached data without making HTTP request
            assert result == cached_data
            mock_get.assert_not_called()
    
    def test_download_font_stores_in_cache(self) -> None:
        """Verify downloaded font is stored in cache."""
        cache = get_font_cache()
        font_url = "https://example.com/new-font.otf"
        mock_font_data = b"new font data"
        
        with patch("app.services.text_render_service.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_font_data
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            _download_font(font_url)
            
            # Verify font is now in cache
            assert cache.get_font(font_url) == mock_font_data
    
    def test_download_font_network_error(self) -> None:
        """Verify network errors are properly raised."""
        with patch("app.services.text_render_service.requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")
            
            with pytest.raises(requests.RequestException, match="Network error"):
                _download_font("https://example.com/font.otf")


class TestImageRendering:
    """Test suite for image rendering functionality."""
    
    @pytest.fixture
    def mock_font(self) -> ImageFont.FreeTypeFont:
        """Create a mock font for testing."""
        # Use a simple default font for testing
        # Create a font that returns predictable textbbox values
        mock_font = MagicMock(spec=ImageFont.FreeTypeFont)
        return mock_font
    
    def test_calculate_dimensions(self) -> None:
        """Verify correct width/height calculation with padding."""
        # Create a mock font that returns predictable textbbox
        mock_font = MagicMock(spec=ImageFont.FreeTypeFont)
        
        with patch("app.services.text_render_service.ImageDraw.Draw") as mock_draw_class:
            mock_draw = MagicMock()
            # Mock textbbox to return (left, top, right, bottom)
            # Simulate text that is 100x50 pixels
            mock_draw.textbbox.return_value = (0, 0, 100, 50)
            mock_draw_class.return_value = mock_draw
            
            width, height = _calculate_dimensions("Test", mock_font, padding=20)
            
            # Expected: 100 + (20 * 2) = 140 width, 50 + (20 * 2) = 90 height
            assert width == 140
            assert height == 90
            
            # Verify textbbox was called with correct parameters
            mock_draw.textbbox.assert_called_once_with((0, 0), "Test", font=mock_font)
    
    def test_create_image_returns_pil_image(self) -> None:
        """Verify Image object is returned."""
        mock_font = MagicMock(spec=ImageFont.FreeTypeFont)
        
        with patch("app.services.text_render_service.ImageDraw.Draw") as mock_draw_class:
            mock_draw = MagicMock()
            # Mock textbbox for text positioning
            mock_draw.textbbox.return_value = (0, 0, 50, 20)
            mock_draw_class.return_value = mock_draw
            
            result = _create_image(100, 60, "Test", mock_font, padding=10)
            
            # Verify it returns a PIL Image
            assert isinstance(result, Image.Image)
    
    def test_image_has_white_background(self) -> None:
        """Verify RGB white background is used."""
        mock_font = MagicMock(spec=ImageFont.FreeTypeFont)
        
        with patch("app.services.text_render_service.ImageDraw.Draw") as mock_draw_class:
            mock_draw = MagicMock()
            mock_draw.textbbox.return_value = (0, 0, 50, 20)
            mock_draw_class.return_value = mock_draw
            
            image = _create_image(100, 60, "Test", mock_font, padding=10)
            
            # Verify image mode is RGB
            assert image.mode == 'RGB'
            
            # Verify image dimensions
            assert image.size == (100, 60)
            
            # Check that background is white (255, 255, 255)
            # Sample a corner pixel that shouldn't have text
            pixel = image.getpixel((0, 0))
            assert pixel == (255, 255, 255), f"Expected white background, got {pixel}"
    
    def test_text_is_centered(self) -> None:
        """Verify text position calculation centers the text."""
        mock_font = MagicMock(spec=ImageFont.FreeTypeFont)
        
        with patch("app.services.text_render_service.ImageDraw.Draw") as mock_draw_class:
            mock_draw = MagicMock()
            # Simulate text that is 60x30 pixels
            mock_draw.textbbox.return_value = (0, 0, 60, 30)
            mock_draw_class.return_value = mock_draw
            
            # Create 100x60 image with 60x30 text
            _create_image(100, 60, "Test", mock_font, padding=10)
            
            # Verify draw.text was called
            assert mock_draw.text.called
            
            # Extract the position from the call
            call_args = mock_draw.text.call_args
            position = call_args[0][0]  # First positional argument
            
            # Expected position: x = (100 - 60) // 2 = 20, y = (60 - 30) // 2 = 15
            assert position == (20, 15), f"Expected position (20, 15), got {position}"
            
            # Verify text was drawn with correct parameters
            assert call_args[0][1] == "Test"  # Text content
            assert call_args[1]["font"] == mock_font  # Font
            assert call_args[1]["fill"] == 'black'  # Text color
