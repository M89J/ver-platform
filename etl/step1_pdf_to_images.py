"""
Step 1: PDF to Images
Extracts each page of a scanned VER PDF as a high-resolution image.
Also extracts embedded photographs separately.

Usage:
    python step1_pdf_to_images.py <village_name> [--dpi 200]

Input:  data/raw/<village_name>/VER_*.pdf
Output: data/extracted/<village_name>/pages/page_001.png, page_002.png, ...
        data/extracted/<village_name>/photos/photo_001.png, ...
"""
import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF

from config import RAW_DIR, EXTRACTED_DIR, PDF_DPI


def extract_pages(pdf_path: Path, output_dir: Path, dpi: int = PDF_DPI) -> int:
    """Extract all PDF pages as PNG images."""
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    total = doc.page_count
    print(f"Processing {pdf_path.name}: {total} pages at {dpi} DPI")

    for i in range(total):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        out_path = pages_dir / f"page_{i+1:03d}.png"
        pix.save(str(out_path))

        if (i + 1) % 20 == 0 or i == total - 1:
            print(f"  Extracted {i+1}/{total} pages")

    doc.close()
    return total


def extract_embedded_photos(pdf_path: Path, output_dir: Path, min_size: int = 50000) -> int:
    """Extract large embedded images (photos, not template graphics).

    Args:
        min_size: Minimum image byte size to consider as a photo (filters out icons/logos)
    """
    photos_dir = output_dir / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    photo_count = 0

    for page_num in range(doc.page_count):
        page = doc[page_num]
        images = page.get_images(full=True)

        for img_idx, img_info in enumerate(images):
            xref = img_info[0]
            base_image = doc.extract_image(xref)

            if base_image and len(base_image["image"]) > min_size:
                photo_count += 1
                ext = base_image["ext"]
                out_path = photos_dir / f"photo_p{page_num+1:03d}_{photo_count:03d}.{ext}"
                with open(out_path, "wb") as f:
                    f.write(base_image["image"])

    doc.close()
    print(f"  Extracted {photo_count} photos")
    return photo_count


def main():
    parser = argparse.ArgumentParser(description="Step 1: Extract PDF pages as images")
    parser.add_argument("village_name", help="Village directory name (e.g., manjari)")
    parser.add_argument("--dpi", type=int, default=PDF_DPI, help=f"Image resolution (default: {PDF_DPI})")
    args = parser.parse_args()

    village = args.village_name.lower().replace(" ", "_")

    # Find PDF in raw directory
    raw_village_dir = RAW_DIR / village
    if not raw_village_dir.exists():
        print(f"Error: Directory not found: {raw_village_dir}")
        sys.exit(1)

    pdfs = list(raw_village_dir.glob("*.pdf")) + list(raw_village_dir.glob("*.PDF"))
    if not pdfs:
        print(f"Error: No PDF files found in {raw_village_dir}")
        sys.exit(1)

    pdf_path = pdfs[0]
    output_dir = EXTRACTED_DIR / village

    # Extract pages
    total_pages = extract_pages(pdf_path, output_dir, args.dpi)

    # Extract embedded photos
    photo_count = extract_embedded_photos(pdf_path, output_dir)

    # Write extraction manifest
    manifest = {
        "village": village,
        "source_pdf": str(pdf_path.relative_to(RAW_DIR.parent.parent)),
        "total_pages": total_pages,
        "photos_extracted": photo_count,
        "dpi": args.dpi,
    }

    import json
    manifest_path = output_dir / "extraction_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone. Output: {output_dir}")
    print(f"  Pages: {total_pages}")
    print(f"  Photos: {photo_count}")
    print(f"  Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
