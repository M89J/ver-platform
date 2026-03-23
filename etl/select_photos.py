"""
Select and copy field photos from extracted page images to the deployable photos directory.
Filters by file size (skips tiny template graphics), optionally resizes for web.

Usage:
    python select_photos.py <village_name> [--max-width 1200] [--min-size 50000] [--max-photos 15]
"""
import argparse
import json
import shutil
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from config import EXTRACTED_DIR, DATA_DIR


def select_photos(village_name: str, min_size: int = 50000, max_width: int = 1200, max_photos: int = 15):
    """Select best photos from extracted page images."""
    src_dir = EXTRACTED_DIR / village_name / "photos"
    dst_dir = DATA_DIR / "photos" / village_name

    if not src_dir.exists():
        print(f"No photos directory found: {src_dir}")
        return []

    dst_dir.mkdir(parents=True, exist_ok=True)

    # Get all photos sorted by size (largest = likely real photographs)
    photos = []
    for f in sorted(src_dir.iterdir()):
        if f.suffix.lower() in ('.jpeg', '.jpg', '.png'):
            size = f.stat().st_size
            if size >= min_size:
                photos.append((f, size))

    # Sort by size descending (biggest files are likely real photos, not blank pages)
    photos.sort(key=lambda x: x[1], reverse=True)
    selected = photos[:max_photos]

    copied = []
    for src_file, size in selected:
        dst_file = dst_dir / src_file.name
        size_kb = size / 1024

        # Resize if PIL available and image is too wide
        if HAS_PIL and max_width:
            try:
                img = Image.open(src_file)
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                    img.save(dst_file, quality=85)
                    new_size_kb = dst_file.stat().st_size / 1024
                    print(f"  Resized: {src_file.name} ({size_kb:.0f}KB -> {new_size_kb:.0f}KB)")
                    copied.append(dst_file)
                    continue
            except Exception as e:
                print(f"  Resize failed for {src_file.name}: {e}, copying as-is")

        shutil.copy2(src_file, dst_file)
        print(f"  Copied: {src_file.name} ({size_kb:.0f}KB)")
        copied.append(dst_file)

    print(f"\nSelected {len(copied)} photos for {village_name}")
    return copied


def main():
    parser = argparse.ArgumentParser(description="Select photos for web deployment")
    parser.add_argument("village_name", help="Village name")
    parser.add_argument("--min-size", type=int, default=50000, help="Min file size in bytes (default: 50KB)")
    parser.add_argument("--max-width", type=int, default=1200, help="Max image width in pixels (default: 1200)")
    parser.add_argument("--max-photos", type=int, default=15, help="Max photos to select (default: 15)")
    args = parser.parse_args()

    photos = select_photos(args.village_name, args.min_size, args.max_width, args.max_photos)
    if not photos:
        print("No photos selected.")


if __name__ == "__main__":
    main()
