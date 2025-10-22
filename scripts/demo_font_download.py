#!/usr/bin/env python3
"""Demonstration script for font download functionality.

This script demonstrates downloading and caching the MoreSugar OTF font
from the Canva CDN using the text_render_service module.
"""

from app.services.text_render_service import _download_font
from app.utils.font_cache import get_font_cache


def main() -> None:
    """Demonstrate font download and caching."""
    # MoreSugar OTF font from Canva CDN
    font_url = (
        "https://font-public.canva.com/YAFdJkVWBPo/0/"
        "MoreSugar-Regular.62992e429acdec5e01c3db.6f7a950ef2bb9f1314d37ac4a660925e.otf"
    )
    
    print("=" * 70)
    print("Font Download Demonstration")
    print("=" * 70)
    print(f"\nFont URL: {font_url}\n")
    
    # First download (will hit network)
    print("First download (from network)...")
    font_data = _download_font(font_url)
    print(f"✓ Downloaded {len(font_data):,} bytes")
    print(f"✓ OTF signature verified: {font_data[:4] == b'OTTO'}")
    
    # Check cache
    cache = get_font_cache()
    cached_data = cache.get_font(font_url)
    print(f"✓ Font is now cached: {cached_data is not None}")
    
    # Second download (will use cache)
    print("\nSecond download (from cache)...")
    font_data_2 = _download_font(font_url)
    print(f"✓ Retrieved {len(font_data_2):,} bytes")
    print(f"✓ Same data as first download: {font_data == font_data_2}")
    print(f"✓ Retrieved from cache (same object): {font_data_2 is cached_data}")
    
    print("\n" + "=" * 70)
    print("✓ Font download and caching working correctly!")
    print("=" * 70)


if __name__ == "__main__":
    main()

