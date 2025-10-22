"""Example script demonstrating TextRenderService usage.

This script shows how to use the render_text function to create PNG images
from text using downloadable OTF fonts.
"""

import sys
from pathlib import Path

# Add project root to Python path - must be before app imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.text_render_service import render_text  # noqa: E402


def main():
    """Demonstrate text rendering with various configurations."""
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Example 1: Basic usage with MoreSugar font from Canva CDN
    print("Example 1: Rendering 'Hello, World!' with MoreSugar font...")
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
    output_path = output_dir / "example1_hello_world.png"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"✓ Saved to {output_path} ({len(image_bytes)} bytes)")
    
    # Example 2: Unicode support with emoji
    print("\nExample 2: Rendering Unicode text with emoji...")
    image_bytes = render_text(
        font_url=font_url,
        text="Python 🐍 FastAPI 🚀",
        font_size=36.0,
        padding=30
    )
    output_path = output_dir / "example2_emoji.png"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"✓ Saved to {output_path} ({len(image_bytes)} bytes)")
    
    # Example 3: Different font size
    print("\nExample 3: Large font size...")
    image_bytes = render_text(
        font_url=font_url,
        text="Big Text",
        font_size=72.0,
        padding=40
    )
    output_path = output_dir / "example3_large_font.png"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"✓ Saved to {output_path} ({len(image_bytes)} bytes)")
    
    # Example 4: Minimal padding
    print("\nExample 4: Minimal padding...")
    image_bytes = render_text(
        font_url=font_url,
        text="No Padding",
        font_size=24.0,
        padding=0
    )
    output_path = output_dir / "example4_no_padding.png"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"✓ Saved to {output_path} ({len(image_bytes)} bytes)")
    
    # Example 5: CJK characters
    print("\nExample 5: CJK (Chinese) characters...")
    image_bytes = render_text(
        font_url=font_url,
        text="你好世界",
        font_size=48.0,
        padding=25
    )
    output_path = output_dir / "example5_cjk.png"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"✓ Saved to {output_path} ({len(image_bytes)} bytes)")
    
    # Example 6: Font caching demonstration (reuses font from memory)
    print("\nExample 6: Demonstrating font caching (second call with same font)...")
    image_bytes = render_text(
        font_url=font_url,
        text="Cached Font!",
        font_size=32.0,
        padding=15
    )
    output_path = output_dir / "example6_cached.png"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"✓ Saved to {output_path} ({len(image_bytes)} bytes)")
    print("  (Font was retrieved from cache, no download occurred)")
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print(f"Output files saved to: {output_dir.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()

