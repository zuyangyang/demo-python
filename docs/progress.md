# TextRenderService Implementation Progress

Project: Render text to PNG images using downloadable OTF fonts
PRD: [prd.md](./prd.md)

---

## Phase 1: Project Setup & Dependencies

Purpose: Add required dependencies and create directory structure for the text rendering service

Tasks:
- [x] Add Pillow>=10.0.0 to pyproject.toml dependencies
- [x] Add requests>=2.31.0 to pyproject.toml dependencies
- [x] Run `uv lock` to update uv.lock with new dependencies
- [x] Create app/services/__init__.py if not exists
- [x] Create app/utils/__init__.py if not exists
- [x] Create app/tests/unit/test_text_render_service.py scaffold
- [x] Create app/tests/integration/test_render_with_real_font.py scaffold

Unit Tests:
- [x] No unit tests for this phase (setup only)

Integration Tests:
- [x] No integration tests for this phase (setup only)

✅ Done: Phase 1 completed. Added Pillow 12.0.0 and requests 2.32.5 dependencies to pyproject.toml. Created app/services/__init__.py, app/utils/__init__.py, and test scaffolds for both unit and integration tests. All placeholder tests pass. 

---

## Phase 2: Font Cache Utility

Purpose: Implement in-memory font caching to avoid redundant downloads

Tasks:
- [x] Create app/utils/font_cache.py with FontCache class
- [x] Implement get_font(url: str) -> Optional[bytes] method
- [x] Implement set_font(url: str, font_data: bytes) method
- [x] Implement clear_font(url: str) method for error recovery
- [x] Add type hints and docstrings following Google style
- [x] Use dict-based storage {url: bytes}

Unit Tests:
- [x] test_font_cache.py::test_set_and_get_font – verify font data is stored and retrieved
- [x] test_font_cache.py::test_get_nonexistent_font – verify returns None for missing URL
- [x] test_font_cache.py::test_clear_font – verify font is removed from cache
- [x] test_font_cache.py::test_cache_multiple_fonts – verify multiple fonts can coexist

Integration Tests:
- [x] No integration tests for this phase (unit only)

✅ Done: Phase 2 completed. Implemented FontCache class in app/utils/font_cache.py with get_font(), set_font(), and clear_font() methods. Created comprehensive unit tests in app/tests/unit/test_font_cache.py with 6 test cases covering all functionality. All tests pass. Code follows PEP 8 standards with proper type hints and Google-style docstrings. 

---

## Phase 3: Font Download Logic

Purpose: Implement HTTP font downloading with error handling

Tasks:
- [ ] Create app/services/text_render_service.py
- [ ] Implement _download_font(font_url: str) -> bytes helper function
- [ ] Use requests.get(font_url, timeout=30) with proper error handling
- [ ] Raise requests.HTTPError for non-200 status codes
- [ ] Integrate FontCache to check before downloading
- [ ] Store downloaded font in cache after successful download
- [ ] Add type hints and docstrings

Unit Tests:
- [ ] test_text_render_service.py::test_download_font_success – verify font bytes returned with mocked requests
- [ ] test_text_render_service.py::test_download_font_404 – verify HTTPError raised for 404
- [ ] test_text_render_service.py::test_download_font_timeout – verify timeout error handling
- [ ] test_text_render_service.py::test_download_font_uses_cache – verify cache hit avoids download

Integration Tests:
- [ ] No integration tests for this phase (unit with mocks)

✅ Done: 

---

## Phase 4: Image Rendering Logic

Purpose: Implement text-to-image rendering with Pillow

Tasks:
- [ ] Implement _calculate_dimensions(text, font, padding) -> tuple[int, int] helper
- [ ] Use ImageDraw.textbbox() to get text dimensions
- [ ] Add padding * 2 to both width and height
- [ ] Implement _create_image(width, height, text, font, padding) -> Image
- [ ] Use Image.new('RGB', (width, height), 'white') for canvas
- [ ] Use ImageDraw.Draw() to draw centered text in black
- [ ] Calculate center position: ((width - text_width) // 2, (height - text_height) // 2)
- [ ] Add proper error handling for invalid font data

Unit Tests:
- [ ] test_text_render_service.py::test_calculate_dimensions – verify correct width/height with padding
- [ ] test_text_render_service.py::test_create_image_returns_pil_image – verify Image object returned
- [ ] test_text_render_service.py::test_image_has_white_background – verify RGB white background
- [ ] test_text_render_service.py::test_text_is_centered – verify text position calculation

Integration Tests:
- [ ] No integration tests for this phase (unit with mocks)

✅ Done: 

---

## Phase 5: Main render_text Function

Purpose: Implement the main public API function that orchestrates all components

Tasks:
- [ ] Implement render_text(font_url, text, font_size, padding) -> bytes function
- [ ] Validate parameters: raise ValueError for empty text or negative font_size/padding
- [ ] Download font using _download_font() helper
- [ ] Load font with ImageFont.truetype(BytesIO(font_bytes), size=font_size)
- [ ] Raise IOError if font fails to load, clear cache entry
- [ ] Calculate dimensions and create image
- [ ] Convert image to PNG bytes using BytesIO and image.save(buffer, 'PNG')
- [ ] Return bytes from buffer.getvalue()
- [ ] Add comprehensive docstring with all parameters, returns, raises

Unit Tests:
- [ ] test_text_render_service.py::test_render_text_success – verify PNG bytes returned
- [ ] test_text_render_service.py::test_render_text_empty_text_raises – verify ValueError for empty text
- [ ] test_text_render_service.py::test_render_text_negative_font_size_raises – verify ValueError
- [ ] test_text_render_service.py::test_render_text_negative_padding_raises – verify ValueError
- [ ] test_text_render_service.py::test_render_text_invalid_font_raises – verify IOError and cache cleared
- [ ] test_text_render_service.py::test_render_text_unicode_support – verify emoji/CJK characters work

Integration Tests:
- [ ] No integration tests for this phase (covered in Phase 6)

✅ Done: 

---

## Phase 6: Integration Testing

Purpose: Test end-to-end with real font URLs and validate output

Tasks:
- [ ] Implement test_render_with_real_font.py::test_render_with_google_fonts
- [ ] Use real OTF font URL from Google Fonts or similar
- [ ] Verify returned bytes are valid PNG (check PNG header signature)
- [ ] Save bytes to temporary file and verify can be opened with PIL
- [ ] Test with different font sizes (12.0, 24.0, 48.0)
- [ ] Test with different padding values (0, 10, 50)
- [ ] Test with Unicode text (emoji, CJK characters)
- [ ] Verify cache works across multiple calls with same font_url

Integration Tests:
- [ ] test_render_with_real_font.py::test_render_with_google_fonts – verify end-to-end with real font
- [ ] test_render_with_real_font.py::test_png_output_is_valid – verify PNG header and PIL can open
- [ ] test_render_with_real_font.py::test_multiple_font_sizes – verify different sizes work
- [ ] test_render_with_real_font.py::test_different_padding – verify padding applied correctly
- [ ] test_render_with_real_font.py::test_unicode_text_rendering – verify emoji/CJK support
- [ ] test_render_with_real_font.py::test_font_caching_works – verify cache hit on second call

Unit Tests:
- [ ] No additional unit tests for this phase

✅ Done: 

---

## Phase 7: Code Quality & Coverage

Purpose: Ensure code quality, test coverage, and PEP 8 compliance

Tasks:
- [ ] Run `uv run pytest app/tests/unit/test_text_render_service.py --cov=app/services --cov-report=term`
- [ ] Verify ≥ 80% test coverage for text_render_service.py
- [ ] Run `uv run pytest app/tests/unit/test_font_cache.py --cov=app/utils --cov-report=term`
- [ ] Verify ≥ 80% test coverage for font_cache.py
- [ ] Run `uv run ruff check app/services app/utils` to verify PEP 8 compliance
- [ ] Fix any linting errors (naming, spacing, imports)
- [ ] Verify all functions have type hints
- [ ] Verify all public functions have docstrings

Unit Tests:
- [ ] No new tests, verify existing test coverage meets threshold

Integration Tests:
- [ ] Run all integration tests: `uv run pytest app/tests/integration/ -v`

✅ Done: 

---

## Phase 8: Documentation & Finalization

Purpose: Update README and verify all acceptance criteria met

Tasks:
- [ ] Update README.md with TextRenderService section
- [ ] Add installation instructions for new dependencies
- [ ] Add usage example from PRD section 6
- [ ] Document function signature and parameters
- [ ] Add example of saving output to file
- [ ] Review all PRD acceptance criteria checkboxes
- [ ] Run full test suite: `uv run pytest app/tests/ -v`
- [ ] Create example script in scripts/example_text_render.py
- [ ] Test example script to verify it works end-to-end

Unit Tests:
- [ ] No new tests for this phase

Integration Tests:
- [ ] No new tests for this phase

✅ Done: 

---

## Summary

**Total Phases:** 8
**Completed:** 2/8
**Overall Progress:** 25.0%

**Next Action:** Start Phase 3 - Font Download Logic

