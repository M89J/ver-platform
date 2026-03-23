"""
Step 3: Section Detection
Identifies which VER sections appear on which pages using OCR text + section header patterns.
Creates a section-to-page mapping that guides structured data extraction.

Usage:
    python step3_section_detect.py <village_name>

Input:  data/extracted/<village_name>/ocr/page_*.txt
Output: data/extracted/<village_name>/section_map.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

from config import EXTRACTED_DIR, SECTION_HEADERS, get_section_keywords


def detect_sections(ocr_dir: Path) -> dict:
    """Scan OCR text of each page for section header keywords.
    Uses multilingual keywords (English, Hindi, Marathi, Gujarati, Odia, Telugu, Kannada).

    Returns a mapping of section_id -> {start_page, end_page, header_found}
    """
    text_files = sorted(ocr_dir.glob("page_*.txt"))
    if not text_files:
        return {}

    page_texts = {}
    for tf in text_files:
        # Extract page number from filename
        match = re.search(r"page_(\d+)", tf.name)
        if match:
            page_num = int(match.group(1))
            page_texts[page_num] = tf.read_text(encoding="utf-8")

    # Detect sections using all language variants
    section_pages = {}
    for page_num in sorted(page_texts.keys()):
        text = page_texts[page_num].lower()

        for section_id in SECTION_HEADERS:
            keywords = get_section_keywords(section_id)
            for keyword in keywords:
                if keyword.lower() in text:
                    if section_id not in section_pages:
                        section_pages[section_id] = {
                            "start_page": page_num,
                            "end_page": page_num,
                            "header_found": keyword,
                            "confidence": "auto_detected",
                        }
                    else:
                        # Extend end page
                        section_pages[section_id]["end_page"] = page_num
                    break

    # Fill in end pages based on next section's start
    sorted_sections = sorted(section_pages.items(), key=lambda x: x[1]["start_page"])
    for i in range(len(sorted_sections) - 1):
        current_id = sorted_sections[i][0]
        next_start = sorted_sections[i + 1][1]["start_page"]
        section_pages[current_id]["end_page"] = next_start - 1

    # Last section extends to last page
    if sorted_sections:
        last_id = sorted_sections[-1][0]
        max_page = max(page_texts.keys())
        section_pages[last_id]["end_page"] = max_page

    return section_pages


def main():
    parser = argparse.ArgumentParser(description="Step 3: Detect VER sections in OCR text")
    parser.add_argument("village_name", help="Village directory name")
    args = parser.parse_args()

    village = args.village_name.lower().replace(" ", "_")
    village_dir = EXTRACTED_DIR / village
    ocr_dir = village_dir / "ocr"

    if not ocr_dir.exists():
        print(f"Error: OCR directory not found: {ocr_dir}")
        print("Run step2_ocr_extract.py first.")
        sys.exit(1)

    print(f"Detecting sections for village: {village}")
    section_map = detect_sections(ocr_dir)

    if not section_map:
        print("Warning: No sections detected. OCR quality may be too low.")
        print("Consider manual section mapping.")

    # Save section map
    output_path = village_dir / "section_map.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(section_map, f, indent=2, ensure_ascii=False)

    print(f"\nDetected {len(section_map)} sections:")
    for section_id, info in sorted(section_map.items(), key=lambda x: x[1]["start_page"]):
        print(f"  {section_id}: pages {info['start_page']}-{info['end_page']} "
              f"(matched: '{info['header_found']}')")

    # Identify missing sections
    all_sections = set(SECTION_HEADERS.keys())
    found_sections = set(section_map.keys())
    missing = all_sections - found_sections
    if missing:
        print(f"\nMissing sections (may need manual mapping): {sorted(missing)}")

    print(f"\nOutput: {output_path}")


if __name__ == "__main__":
    main()
