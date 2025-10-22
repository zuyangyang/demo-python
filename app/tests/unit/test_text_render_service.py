"""Unit tests for text rendering service."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services.text_render_service import _download_font
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
