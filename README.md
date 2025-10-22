## Demo Python API (FastAPI)

Minimal FastAPI "Hello, World" scaffold with tests and `uv` workflows, plus a TextRenderService for converting text to PNG images using downloadable fonts.

### Prerequisites
- Python 3.10+
- uv installed

### Install
```bash
uv venv
uv sync
```

The project includes the following key dependencies:
- **FastAPI** (>=0.115.0) - Web framework
- **Uvicorn** (>=0.30.0) - ASGI server
- **Pillow** (>=10.0.0) - Image processing for text rendering
- **requests** (>=2.31.0) - HTTP client for font downloads
- **pytest** (>=8.0.0) - Testing framework

### Run (development)
```bash
uv run uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/api/v1/hello`.

### Test
```bash
# Run all tests
uv run pytest -q

# Run with coverage
uv run pytest --cov=app --cov-report=term

# Run specific test suites
uv run pytest app/tests/unit/ -v
uv run pytest app/tests/integration/ -v
```

### Structure
```
app/
  api/v1/endpoints/hello.py
  api/v1/router.py
  core/config.py
  main.py
  schemas/hello.py
  services/
    text_render_service.py  # Text-to-PNG rendering
  utils/
    font_cache.py          # In-memory font caching
  tests/
    unit/                  # Unit tests
    integration/           # Integration tests
scripts/
  example_text_render.py   # Example usage
```

### API
- GET `/api/v1/hello` → `{ "message": "Hello, World" }`
  - Optional query `name` to personalize the greeting

---

## TextRenderService

The `TextRenderService` provides functionality to render custom-styled text into PNG images using downloadable OTF/TTF fonts.

### Features
- 🖼️ Render text to PNG images with custom fonts
- 🌐 Download fonts from HTTP/HTTPS URLs
- 💾 Automatic font caching to avoid redundant downloads
- 🌍 Full Unicode support (emoji, CJK characters, etc.)
- ⚡ Fast and efficient with PIL/Pillow
- 🎨 Configurable font size and padding

### Function Signature

```python
def render_text(font_url: str, text: str, font_size: float, padding: int) -> bytes
```

**Parameters:**
- `font_url` (str): HTTP/HTTPS URL to OTF or TTF font file
- `text` (str): Text content to render (supports Unicode)
- `font_size` (float): Font size in points (must be positive)
- `padding` (int): Padding around text in pixels (must be non-negative)

**Returns:**
- `bytes`: PNG image as bytes

**Raises:**
- `ValueError`: If text is empty, font_size is negative, or padding is negative
- `requests.HTTPError`: If font download fails or returns non-200 status
- `requests.Timeout`: If font download exceeds 30-second timeout
- `IOError`: If font file is invalid or unsupported format

### Usage Example

```python
from app.services.text_render_service import render_text

# Render text with an OTF font
font_url = (
    "https://font-public.canva.com/YAFdJkVWBPo/0/"
    "MoreSugar-Regular.62992e429acdec5e01c3db.6f7a950ef2bb9f1314d37ac4a660925e.otf"
)
image_bytes = render_text(
    font_url=font_url,
    text="Hello, World!",
    font_size=48.0,
    padding=20
)

# Save to file
with open("output.png", "wb") as f:
    f.write(image_bytes)
```

### Unicode Support

The service fully supports Unicode characters including emoji and CJK:

```python
# Emoji
image_bytes = render_text(font_url, "Python 🐍 FastAPI 🚀", 36.0, 20)

# Chinese characters
image_bytes = render_text(font_url, "你好世界", 48.0, 25)
```

### Font Caching

Fonts are automatically cached in memory after the first download. Subsequent calls with the same `font_url` will retrieve the font from cache without making additional HTTP requests:

```python
# First call: downloads and caches font
img1 = render_text(font_url, "First", 24.0, 10)

# Second call: uses cached font (no download)
img2 = render_text(font_url, "Second", 24.0, 10)
```

### Output Format

- **Format**: PNG (RGB mode, no transparency)
- **Background**: White (#FFFFFF)
- **Text color**: Black (#000000)
- **Text alignment**: Centered horizontally and vertically
- **Dimensions**: Automatically calculated based on text size and padding

### Run Example Script

The project includes a comprehensive example script:

```bash
uv run python scripts/example_text_render.py
```

This will generate 6 example PNG images in the `output/` directory demonstrating:
1. Basic usage
2. Unicode emoji support
3. Large font sizes
4. Minimal padding
5. CJK character rendering
6. Font caching

### Testing

The TextRenderService includes comprehensive test coverage:

```bash
# Run unit tests for text rendering
uv run pytest app/tests/unit/test_text_render_service.py -v

# Run unit tests for font cache
uv run pytest app/tests/unit/test_font_cache.py -v

# Run integration tests with real fonts
uv run pytest app/tests/integration/test_render_with_real_font.py -v

# Run all tests with coverage report
uv run pytest app/tests/ --cov=app/services --cov=app/utils --cov-report=term
```

### Configuration

The service uses the following defaults:
- **HTTP timeout**: 30 seconds for font downloads
- **Cache type**: In-memory (session-based, not persistent)
- **Supported formats**: OTF and TTF fonts

### Limitations (MVP)

The current implementation does not support:
- Custom text or background colors (always black on white)
- Text alignment options (always centered)
- Multiple output formats (PNG only)
- Persistent font caching across sessions
- Multiline text with line breaks
- Advanced text effects (shadows, outlines, gradients)

---


