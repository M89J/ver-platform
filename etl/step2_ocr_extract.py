"""
Step 2: OCR Text Extraction
Runs Tesseract OCR on extracted page images to produce text + confidence scores.
Supports all VER data collection languages: Marathi, Hindi, Gujarati, Odia, Telugu, Kannada, English.

Usage:
    python step2_ocr_extract.py <village_name> [--state maharashtra] [--lang mar+eng] [--pages 1-134]

    If --state is provided, language is auto-detected from STATE_LANGUAGE_MAP.
    If --lang is provided, it overrides state-based detection.

Input:  data/extracted/<village_name>/pages/page_*.png
Output: data/extracted/<village_name>/ocr/page_001.txt, page_001_conf.json, ...
        data/extracted/<village_name>/ocr/full_text.txt

Prerequisites:
    sudo apt install tesseract-ocr tesseract-ocr-{mar,hin,guj,ori,tel,kan}
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("Install dependencies: pip install pytesseract Pillow")
    print("Also install Tesseract: sudo apt install tesseract-ocr tesseract-ocr-mar tesseract-ocr-hin")
    sys.exit(1)

from config import EXTRACTED_DIR, DEFAULT_TESSERACT_LANG, TESSERACT_PSM, TESSERACT_OEM, get_tesseract_lang


def preprocess_image(image_path: Path) -> Image.Image:
    """Basic image preprocessing for better OCR results on scanned handwriting."""
    img = Image.open(image_path)

    # Convert to grayscale if not already
    if img.mode != "L":
        img = img.convert("L")

    return img


def ocr_page(image_path: Path, lang: str = DEFAULT_TESSERACT_LANG) -> dict:
    """Run OCR on a single page image.

    Returns dict with:
        - text: extracted text
        - confidence: average confidence score (0-100)
        - word_data: per-word confidence data for review flagging
    """
    img = preprocess_image(image_path)

    # Get detailed word-level data
    custom_config = f"--oem {TESSERACT_OEM} --psm {TESSERACT_PSM}"
    data = pytesseract.image_to_data(img, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)

    # Get plain text
    text = pytesseract.image_to_string(img, lang=lang, config=custom_config)

    # Calculate average confidence (only for actual words, not empty entries)
    confidences = [
        int(c) for c, t in zip(data["conf"], data["text"])
        if int(c) > 0 and t.strip()
    ]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    # Identify low-confidence words for human review
    low_conf_words = []
    for i, (word, conf) in enumerate(zip(data["text"], data["conf"])):
        if word.strip() and int(conf) < 50:
            low_conf_words.append({
                "word": word,
                "confidence": int(conf),
                "position": {
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                }
            })

    return {
        "text": text,
        "confidence": round(avg_confidence, 2),
        "total_words": len(confidences),
        "low_confidence_words": low_conf_words,
    }


def parse_page_range(page_range: str, max_pages: int) -> list:
    """Parse page range string like '1-10' or '5,10,15' into list of page numbers."""
    if not page_range:
        return list(range(1, max_pages + 1))

    pages = []
    for part in page_range.split(","):
        if "-" in part:
            start, end = part.split("-")
            pages.extend(range(int(start), int(end) + 1))
        else:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= max_pages]


def main():
    parser = argparse.ArgumentParser(description="Step 2: OCR text extraction")
    parser.add_argument("village_name", help="Village directory name")
    parser.add_argument("--state", default="", help="State name for auto language detection (e.g., maharashtra, gujarat, odisha)")
    parser.add_argument("--lang", default="", help="Override Tesseract languages (e.g., mar+eng, guj+eng, ori+hin+eng)")
    parser.add_argument("--pages", default="", help="Page range (e.g., 1-10 or 5,10,15). Default: all")
    args = parser.parse_args()

    village = args.village_name.lower().replace(" ", "_")
    village_dir = EXTRACTED_DIR / village
    pages_dir = village_dir / "pages"
    ocr_dir = village_dir / "ocr"
    ocr_dir.mkdir(parents=True, exist_ok=True)

    if not pages_dir.exists():
        print(f"Error: Pages directory not found: {pages_dir}")
        print("Run step1_pdf_to_images.py first.")
        sys.exit(1)

    # Find all page images
    all_pages = sorted(pages_dir.glob("page_*.png"))
    if not all_pages:
        print(f"Error: No page images found in {pages_dir}")
        sys.exit(1)

    # Determine OCR language
    if args.lang:
        ocr_lang = args.lang
    elif args.state:
        ocr_lang = get_tesseract_lang(args.state)
    else:
        ocr_lang = DEFAULT_TESSERACT_LANG

    target_pages = parse_page_range(args.pages, len(all_pages))
    print(f"OCR processing {len(target_pages)} pages for village: {village}")
    print(f"Languages: {ocr_lang}")

    full_text_lines = []
    page_summaries = []

    for page_num in target_pages:
        image_path = pages_dir / f"page_{page_num:03d}.png"
        if not image_path.exists():
            print(f"  Warning: {image_path.name} not found, skipping")
            continue

        print(f"  Processing page {page_num}/{len(all_pages)}...", end=" ")

        result = ocr_page(image_path, ocr_lang)

        # Save per-page text
        text_path = ocr_dir / f"page_{page_num:03d}.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(result["text"])

        # Save per-page confidence data
        conf_path = ocr_dir / f"page_{page_num:03d}_conf.json"
        conf_data = {
            "page": page_num,
            "confidence": result["confidence"],
            "total_words": result["total_words"],
            "low_confidence_count": len(result["low_confidence_words"]),
            "low_confidence_words": result["low_confidence_words"],
        }
        with open(conf_path, "w", encoding="utf-8") as f:
            json.dump(conf_data, f, indent=2, ensure_ascii=False)

        full_text_lines.append(f"\n=== PAGE {page_num} ===\n")
        full_text_lines.append(result["text"])

        page_summaries.append({
            "page": page_num,
            "confidence": result["confidence"],
            "words": result["total_words"],
            "low_conf": len(result["low_confidence_words"]),
        })

        status = "OK" if result["confidence"] >= 50 else "LOW_CONF"
        print(f"conf={result['confidence']:.0f}% words={result['total_words']} [{status}]")

    # Save combined full text
    full_text_path = ocr_dir / "full_text.txt"
    with open(full_text_path, "w", encoding="utf-8") as f:
        f.writelines(full_text_lines)

    # Save OCR summary
    avg_conf = sum(p["confidence"] for p in page_summaries) / len(page_summaries) if page_summaries else 0
    summary = {
        "village": village,
        "language": ocr_lang,
        "pages_processed": len(page_summaries),
        "average_confidence": round(avg_conf, 2),
        "pages_needing_review": [p["page"] for p in page_summaries if p["confidence"] < 50],
        "per_page": page_summaries,
    }
    summary_path = ocr_dir / "ocr_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Average confidence: {avg_conf:.1f}%")
    print(f"Pages needing review: {len(summary['pages_needing_review'])}")
    print(f"Output: {ocr_dir}")


if __name__ == "__main__":
    main()
