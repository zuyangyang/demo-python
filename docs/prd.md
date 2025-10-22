# Project: TextRenderService

## 1. Elevator Pitch (1 line)
Render custom-styled text into PNG images using downloadable OTF fonts, returning image bytes for downstream use.

## 2. Core Entities
- **TextRenderRequest**: font_url:str, text:str, font_size:float, padding:int
- **RenderedImage**: image_bytes:bytes, width:int, height:int, format:str
- **FontCache**: url:str, font_data:bytes, last_accessed:datetime

## 3. Function Interface (no HTTP server)
```python
def render_text(font_url: str, text: str, font_size: float, padding: int) -> bytes
```
**Purpose:** Download OTF font from URL, render text with styling, return PNG bytes.

**Parameters:**
- `font_url`: HTTP/HTTPS URL to OTF font file
- `text`: Text content to render (supports Unicode)
- `font_size`: Font size in points (float, e.g., 24.0)
- `padding`: Padding around text in pixels (int)

**Returns:** PNG image as bytes

**Raises:**
- `ValueError`: Invalid parameters (empty text, negative font_size/padding)
- `requests.HTTPError`: Font download failed
- `IOError`: Font file invalid or unsupported format

## 4. Business Rules
1. Download font from `font_url` using HTTP GET request with 30-second timeout.
2. Cache downloaded fonts in memory by URL to avoid redundant downloads within same session.
3. Calculate image dimensions automatically: width = text_width + (padding * 2), height = text_height + (padding * 2).
4. Use white background (#FFFFFF) with black text (#000000) by default.
5. Render text centered horizontally and vertically within the calculated canvas.
6. Support only OTF font format; reject other formats with clear error message.
7. Output PNG format with transparency disabled (RGB mode, not RGBA).
8. Clear font cache entry if font fails to load to allow retry on next call.

## 5. Acceptance Criteria
- [ ] Function signature matches: `render_text(font_url: str, text: str, font_size: float, padding: int) -> bytes`
- [ ] Successfully downloads and caches OTF fonts from valid URLs
- [ ] Returns valid PNG bytes that can be written to file or displayed
- [ ] Text is rendered with correct font, size, and padding
- [ ] Handles Unicode text (emoji, CJK characters) correctly
- [ ] Raises appropriate exceptions for invalid inputs (empty text, negative values)
- [ ] Raises exception when font URL is unreachable or returns non-200 status
- [ ] Raises exception when font file is not valid OTF format
- [ ] `pytest app/tests/unit/test_text_render_service.py` runs with ≥ 80% coverage
- [ ] Unit tests include: valid render, font caching, error cases (bad URL, invalid font, invalid params)
- [ ] Integration test with real OTF font URL completes successfully
- [ ] Type hints present for all parameters and return values
- [ ] Docstrings follow Google/NumPy style with clear parameter descriptions

## 6. Tech & Run

**Stack:**
- Python >=3.10
- Pillow (PIL) for image rendering
- requests for HTTP font download
- pytest for testing
- No FastAPI/HTTP server required

**Dependencies to add:**
```toml
[project]
dependencies = [
    "fastapi>=0.119.0",
    "pydantic>=2.12.2",
    "pydantic-settings>=2.11.0",
    "uvicorn[standard]>=0.37.0",
    "Pillow>=10.0.0",      # Add this
    "requests>=2.31.0",    # Add this
]
```

**Project Structure:**
```
app/
├── services/
│   ├── __init__.py
│   └── text_render_service.py    # Main implementation
├── utils/
│   ├── __init__.py
│   └── font_cache.py              # In-memory font cache
└── tests/
    ├── unit/
    │   └── test_text_render_service.py
    └── integration/
        └── test_render_with_real_font.py
```

**Run Tests:**
```bash
uv run pytest app/tests/unit/test_text_render_service.py -v
uv run pytest app/tests/integration/test_render_with_real_font.py -v
```

**Usage Example:**
```python
from app.services.text_render_service import render_text

# Render text with Google Fonts OTF
font_url = "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Regular.ttf"
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

## 7. Implementation Notes
- Use `requests.get(font_url, timeout=30)` for font download
- Use `io.BytesIO` to load font bytes into Pillow without temp files
- Use `ImageFont.truetype(font_bytesio, size=font_size)` to load OTF
- Use `ImageDraw.textbbox((0, 0), text, font=font)` to calculate text dimensions
- Use `Image.new('RGB', (width, height), 'white')` for canvas
- Use `io.BytesIO` with `image.save(buffer, format='PNG')` to get bytes
- Implement simple dict-based font cache: `{url: font_bytes}`
- Follow PEP 8 naming: `render_text`, not `renderText`

## 8. Out of Scope (for MVP)
- Custom text colors (always black on white)
- Custom background colors or transparency
- Text alignment options (left, right, justify)
- Multiple output formats (JPEG, WebP)
- Persistent font caching (disk-based)
- Advanced text effects (shadows, outlines, gradients)
- Multiline text support with line breaks
- Font fallback mechanism
- Performance optimization for batch rendering
- HTTP server/REST API wrapper

