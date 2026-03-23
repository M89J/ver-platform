# VER Data Standards & Framework

## 1. Overview

This document defines the data standards for the Village Ecological Register (VER) digital platform. All data collected from ~200 villages must conform to these standards to ensure interoperability, searchability, and consistent display on the web platform.

## 2. Data Flow

```
Paper Forms (field) → Scanned PDF → GitHub raw/ → ETL Pipeline → Structured JSON → Web Platform
```

### Pipeline Steps
| Step | Script | Input | Output |
|------|--------|-------|--------|
| 1 | `step1_pdf_to_images.py` | Scanned PDF | Page images (PNG) |
| 2 | `step2_ocr_extract.py` | Page images | OCR text + confidence |
| 3 | `step3_section_detect.py` | OCR text | Section-to-page map |
| 4 | `step4_structure_data.py` | OCR text + section map | Structured JSON |
| 5 | `step5_build_geojson.py` | All village JSONs | GeoJSON map layer |

## 3. Village ID Convention

Format: `{village}_{block}_{state}` — all lowercase, spaces as underscores.

Example: `manjari_khatav_maharashtra`

## 4. Data Status Lifecycle

Each village's data progresses through:

```
raw_pdf → ocr_extracted → human_reviewed → verified
```

- **raw_pdf**: Original scanned document uploaded
- **ocr_extracted**: ETL pipeline has run, structured JSON generated
- **human_reviewed**: A reviewer has corrected OCR errors
- **verified**: Data verified by a second person or domain expert

## 5. JSON Schema Structure

The master schema is at `schema/ver_schema.json`. Key design principles:

### 5.1 Bilingual Fields
Every text field that contains local language content has a paired `_local` field:
```json
{
  "village_name": "Manjari",
  "village_name_local": "मांजरी"
}
```

### 5.2 Temporal Trend Encoding
The VER template captures data across 4 time periods. Trends are encoded as:
- `"increase"` — corresponds to ↑ in paper form
- `"decrease"` — corresponds to ↓
- `"stable"` — corresponds to ↔
- `"unknown"` — not filled or illegible

When actual numeric counts are available (e.g., livestock), the value is stored as integer instead of trend string.

### 5.3 Habitat Presence (Section 20)
Plant species habitat is stored as boolean flags per land type:
```json
{
  "habitat": {
    "forest": true,
    "grazing_land": true,
    "revenue_wasteland": false,
    "near_water_bodies": false,
    "agriculture": true
  }
}
```

### 5.4 Geocoded Entries
Locations with GPS coordinates use:
```json
{
  "geocode": {
    "latitude": 20.601253,
    "longitude": 74.260039
  }
}
```

## 6. Section Mapping (20 Sections)

| Section | JSON Key | Data Type |
|---------|----------|-----------|
| 2. General Info | `section_2_general_info` | Demographics, land, livelihoods |
| 3. Village History | `section_3_village_history` | Narratives, timeline, myths, resource map |
| 4. Agro-ecological | `section_4_agroecological` | Cropping, varieties, soil, pests, weeds |
| 5. Livestock | `section_5_livestock` | Numbers, breeds, diseases, ethno-vet |
| 6. Waterscape | `section_6_waterscape` | Water sources, quality, conservation |
| 7. Forest Lands | `section_7_forest_lands` | Per-patch: species, NTFP |
| 8. Grassland | `section_8_grassland` | Per-patch: species, NTFP |
| 9. Revenue Wasteland | `section_9_revenue_wasteland` | Per-patch: species |
| 10. Sacred Groves | `section_10_sacred_groves` | Location, cultural significance |
| 11. Eco-important Sites | `section_11_ecologically_important_sites` | Location, description |
| 12. Old/Giant Trees | `section_12_old_giant_trees` | Location, geocode |
| 13. Bee Hives | `section_13_bee_hives` | Location, geocode |
| 14. Fire Incidence | `section_14_fire_incidence` | Events, damage, response |
| 15. Conservation Ethos | `section_15_conservation_ethos` | Narratives, practices |
| 16. Medicinal Plants | `section_16_medicinal_plants` | Name, uses, availability trend |
| 17. Invasive Plants | `section_17_invasive_plants` | Name, impact, spread trend |
| 18. Feral Animals | `section_18_feral_animals` | Name, impact, trend |
| 19. Protected Species | `section_19_culturally_protected_species` | Name, category, significance |
| 20. Flora & Fauna | `section_20_flora_fauna` | 11 sub-inventories (trees→soil macrofauna) |

## 7. GeoJSON Map Layer

`data/villages.geojson` aggregates all villages with:
- Point geometry (village coordinates)
- Summary properties for map popup (population, area, biodiversity counts, livestock total)
- Link to full structured JSON file

## 8. File Organization

```
ver-platform/
├── data/
│   ├── raw/{village}/VER_*.pdf          # Original scanned PDFs
│   ├── extracted/{village}/
│   │   ├── pages/page_*.png             # Page images
│   │   ├── ocr/page_*.txt               # OCR text per page
│   │   ├── ocr/*_conf.json              # Confidence scores
│   │   ├── photos/                      # Extracted photographs
│   │   └── section_map.json             # Section-to-page mapping
│   ├── structured/{village}.json        # Final structured data
│   ├── review/{village}_review.json     # Items needing human review
│   └── villages.geojson                 # Map layer
├── etl/                                 # Python ETL pipeline
├── schema/
│   └── ver_schema.json                  # JSON schema definition
├── web/                                 # Frontend (GitHub Pages)
└── i18n/                                # Multilingual translations
```

## 9. OCR & Quality Control

### Tesseract Configuration
- Languages: `mar+hin+eng` (Marathi + Hindi + English)
- PSM: 6 (uniform text block)
- OEM: 3 (LSTM engine)

### Confidence Thresholds
- **≥80%**: Auto-accepted
- **50-80%**: Accepted but flagged for review
- **<50%**: Mandatory human review required

### Review Process
Low-confidence extractions are written to `data/review/{village}_review.json` with:
- The section reference
- Raw OCR text
- Confidence score
- Required action (manual_entry_required / verify_extraction)

## 10. Languages Supported
- Marathi (primary, based on Manjari reference village)
- Hindi
- English
- Additional Indian languages can be added via Tesseract language packs and i18n translations
