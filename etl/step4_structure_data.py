"""
Step 4: Structure Extracted Data
Takes OCR text + section mapping and structures it into the VER JSON schema.
This is the core transformation step — maps raw OCR output to standardized fields.

For handwritten Marathi content with low OCR confidence, data is flagged for human review.

Usage:
    python step4_structure_data.py <village_name>

Input:  data/extracted/<village_name>/ocr/*.txt
        data/extracted/<village_name>/section_map.json
Output: data/structured/<village_name>.json
        data/review/<village_name>_review.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

from config import (
    EXTRACTED_DIR, STRUCTURED_DIR, REVIEW_DIR,
    HIGH_CONFIDENCE, LOW_CONFIDENCE
)


def load_section_texts(village_dir: Path, section_map: dict) -> dict:
    """Load OCR text for each section's page range."""
    ocr_dir = village_dir / "ocr"
    section_texts = {}

    for section_id, info in section_map.items():
        texts = []
        for page_num in range(info["start_page"], info["end_page"] + 1):
            text_file = ocr_dir / f"page_{page_num:03d}.txt"
            if text_file.exists():
                texts.append(text_file.read_text(encoding="utf-8"))
        section_texts[section_id] = "\n".join(texts)

    return section_texts


def load_page_confidences(village_dir: Path) -> dict:
    """Load OCR confidence scores per page."""
    ocr_dir = village_dir / "ocr"
    confidences = {}
    for conf_file in ocr_dir.glob("page_*_conf.json"):
        match = re.search(r"page_(\d+)", conf_file.name)
        if match:
            page_num = int(match.group(1))
            data = json.loads(conf_file.read_text(encoding="utf-8"))
            confidences[page_num] = data.get("confidence", 0)
    return confidences


def extract_numbers(text: str) -> list:
    """Extract numeric values from OCR text."""
    return [int(n) for n in re.findall(r'\b\d+\b', text)]


def extract_table_rows(text: str) -> list:
    """Attempt to extract table-like rows from OCR text.

    Heuristic: lines with multiple whitespace-separated values
    or lines with pipe/tab separators.
    """
    rows = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Split by multiple spaces or tabs
        cells = re.split(r'\s{2,}|\t', line)
        if len(cells) >= 2:
            rows.append([c.strip() for c in cells if c.strip()])
    return rows


def build_skeleton(village_name: str, village_id: str) -> dict:
    """Build an empty VER JSON skeleton following the schema."""
    return {
        "metadata": {
            "village_id": village_id,
            "ver_year": "",
            "language": "",
            "data_status": "ocr_extracted",
            "source_pdf": f"data/raw/{village_name}/",
            "total_pages": 0,
            "extraction_date": "",
            "reviewer": "",
            "ocr_confidence": 0.0,
            "notes": "Auto-extracted via ETL pipeline. Needs human review."
        },
        "section_2_general_info": {
            "village_name": village_name.replace("_", " ").title(),
            "village_name_local": "",
            "gram_panchayat": "",
            "block": "",
            "district": "",
            "state": "",
            "coordinates": {"latitude": None, "longitude": None},
            "date_of_preparation": "",
            "land_details": {},
            "caste_composition": {},
            "landholding": {},
            "major_livelihoods": []
        },
        "section_3_village_history": {"village_history": {"narrative": "", "narrative_local": "", "timeline_events": []}, "traditional_methods": [], "myths_and_beliefs": [], "resource_map": {}},
        "section_4_agroecological": {"cropping_pattern": {}, "traditional_varieties": [], "farming_practices": [], "hedge_biodiversity": [], "soil_health": {}, "soil_health_indicators": [], "traditional_climate_practices": [], "pest_incidences": [], "major_weeds": []},
        "section_5_livestock": {"livestock_numbers": [], "indigenous_breeds": [], "common_diseases": [], "ethno_veterinary_practices": [], "traditional_livestock_practices": []},
        "section_6_waterscape": {"drinking_water": [], "livestock_water": [], "irrigation_sources": "", "water_quality_changes": [], "traditional_water_conservation": [], "important_water_bodies": []},
        "section_7_forest_lands": [],
        "section_8_grassland": [],
        "section_9_revenue_wasteland": [],
        "section_10_sacred_groves": [],
        "section_11_ecologically_important_sites": [],
        "section_12_old_giant_trees": [],
        "section_13_bee_hives": [],
        "section_14_fire_incidence": [],
        "section_15_conservation_ethos": {"narrative": "", "narrative_local": "", "practices": []},
        "section_16_medicinal_plants": [],
        "section_17_invasive_plants": [],
        "section_18_feral_animals": [],
        "section_19_culturally_protected_species": [],
        "section_20_flora_fauna": {"trees": [], "shrubs": [], "herbs_and_grasses": [], "lower_plants": [], "mammals": [], "birds": [], "reptiles_amphibians": [], "butterflies": [], "dragonflies": [], "fish_insects_others": [], "soil_macrofauna": []},
        "photos": []
    }


def populate_section_2(skeleton: dict, text: str, review_items: list, section_conf: float):
    """Attempt to extract Section 2 data from OCR text."""
    numbers = extract_numbers(text)
    rows = extract_table_rows(text)

    # Store raw OCR text for review
    skeleton["section_2_general_info"]["_raw_ocr"] = text[:2000]

    if section_conf < LOW_CONFIDENCE:
        review_items.append({
            "section": "section_2_general_info",
            "reason": "Low OCR confidence",
            "confidence": section_conf,
            "raw_text": text[:2000],
            "action": "manual_entry_required"
        })

    # Try to extract coordinates (pattern: XX.XXXXX, YY.YYYYY)
    coord_match = re.findall(r'(\d{1,3}\.\d{4,8})', text)
    if len(coord_match) >= 2:
        try:
            lat = float(coord_match[0])
            lon = float(coord_match[1])
            if 6 <= lat <= 38 and 68 <= lon <= 98:  # India bounds
                skeleton["section_2_general_info"]["coordinates"] = {
                    "latitude": lat, "longitude": lon
                }
        except ValueError:
            pass


def populate_section_5(skeleton: dict, text: str, review_items: list, section_conf: float):
    """Attempt to extract Section 5 (Livestock) data."""
    rows = extract_table_rows(text)

    # Livestock type keywords (English + Marathi transliterations)
    livestock_keywords = {
        "cow": "Indigenous Cows", "gai": "Indigenous Cows", "गाय": "Indigenous Cows",
        "hybrid": "Hybrid Cows",
        "oxen": "Oxen", "bail": "Oxen", "बैल": "Oxen",
        "buffalo": "Buffaloes", "mhais": "Buffaloes", "म्हैस": "Buffaloes",
        "goat": "Goats", "bakri": "Goats", "बकरी": "Goats",
        "sheep": "Sheep", "mendi": "Sheep", "मेंडी": "Sheep",
        "camel": "Camel", "unt": "Camel",
    }

    skeleton["section_5_livestock"]["_raw_ocr"] = text[:2000]

    if section_conf < LOW_CONFIDENCE:
        review_items.append({
            "section": "section_5_livestock",
            "reason": "Low OCR confidence",
            "confidence": section_conf,
            "raw_text": text[:2000],
            "action": "manual_entry_required"
        })


def populate_section_6(skeleton: dict, text: str, review_items: list, section_conf: float):
    """Attempt to extract Section 6 (Waterscape) data."""
    skeleton["section_6_waterscape"]["_raw_ocr"] = text[:2000]

    water_keywords = {
        "tap": "tap", "नळ": "tap",
        "tubewell": "tubewell", "बोअर": "tubewell",
        "well": "open_well", "विहीर": "open_well",
        "spring": "spring",
        "river": "river", "नदी": "river",
    }


def main():
    parser = argparse.ArgumentParser(description="Step 4: Structure OCR data into VER JSON")
    parser.add_argument("village_name", help="Village directory name")
    parser.add_argument("--village-id", default="", help="Village ID (auto-generated if empty)")
    args = parser.parse_args()

    village = args.village_name.lower().replace(" ", "_")
    village_dir = EXTRACTED_DIR / village

    # Load section map
    section_map_path = village_dir / "section_map.json"
    if not section_map_path.exists():
        print(f"Error: Section map not found: {section_map_path}")
        print("Run step3_section_detect.py first.")
        sys.exit(1)

    section_map = json.loads(section_map_path.read_text(encoding="utf-8"))
    section_texts = load_section_texts(village_dir, section_map)
    page_confidences = load_page_confidences(village_dir)

    village_id = args.village_id or village
    skeleton = build_skeleton(village, village_id)
    review_items = []

    # Calculate per-section average confidence
    def section_confidence(section_id: str) -> float:
        if section_id not in section_map:
            return 0.0
        info = section_map[section_id]
        confs = [page_confidences.get(p, 0) for p in range(info["start_page"], info["end_page"] + 1)]
        return sum(confs) / len(confs) if confs else 0.0

    # Populate each section
    print(f"Structuring data for village: {village}")

    if "section_2" in section_texts:
        conf = section_confidence("section_2")
        print(f"  Section 2 (General Info): conf={conf:.0f}%")
        populate_section_2(skeleton, section_texts["section_2"], review_items, conf)

    if "section_5" in section_texts:
        conf = section_confidence("section_5")
        print(f"  Section 5 (Livestock): conf={conf:.0f}%")
        populate_section_5(skeleton, section_texts["section_5"], review_items, conf)

    if "section_6" in section_texts:
        conf = section_confidence("section_6")
        print(f"  Section 6 (Waterscape): conf={conf:.0f}%")
        populate_section_6(skeleton, section_texts["section_6"], review_items, conf)

    # For all other sections, store raw OCR text for human review
    for section_id, text in section_texts.items():
        section_key = section_id.replace("section_", "section_")
        # Find matching key in skeleton
        for key in skeleton:
            if section_id.replace("section_", "") in key:
                if isinstance(skeleton[key], dict):
                    skeleton[key]["_raw_ocr"] = text[:3000]
                break

    # Update metadata
    from datetime import date
    ocr_summary_path = village_dir / "ocr" / "ocr_summary.json"
    if ocr_summary_path.exists():
        ocr_summary = json.loads(ocr_summary_path.read_text(encoding="utf-8"))
        skeleton["metadata"]["ocr_confidence"] = ocr_summary.get("average_confidence", 0) / 100
        skeleton["metadata"]["total_pages"] = ocr_summary.get("pages_processed", 0)

    skeleton["metadata"]["extraction_date"] = date.today().isoformat()

    # Save structured JSON
    STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = STRUCTURED_DIR / f"{village}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(skeleton, f, indent=2, ensure_ascii=False)

    # Save review items
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    review_path = REVIEW_DIR / f"{village}_review.json"
    review_data = {
        "village": village,
        "total_review_items": len(review_items),
        "items": review_items
    }
    with open(review_path, "w", encoding="utf-8") as f:
        json.dump(review_data, f, indent=2, ensure_ascii=False)

    print(f"\nDone.")
    print(f"  Structured data: {output_path}")
    print(f"  Review items: {len(review_items)} -> {review_path}")


if __name__ == "__main__":
    main()
