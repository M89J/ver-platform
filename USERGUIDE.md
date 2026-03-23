# VER Platform — User Guide

## Accessing the Platform

**Live URL:** https://m89j.github.io/ver-platform/

**Repository:** https://github.com/M89J/ver-platform

---

## Viewing Village Data

1. Open the platform URL in your browser
2. The map displays India with the official administrative boundary
3. Green dots represent villages with VER data
4. **Click a village dot** to open the sidebar with 5 tabs:

| Tab | Content |
|-----|---------|
| **Overview** | Population, area, households, species count, land use chart, livelihoods |
| **Biodiversity** | Species bar chart (trees, birds, mammals, etc.), species name tags |
| **Livestock** | Livestock trends over 10/25/50 years, data table |
| **Water** | Water sources (tube wells, open wells, ponds), counts |
| **Document** | Village history, geotagged photo map, photo gallery, data download |

### Features
- **Search:** Type a village name in the search bar
- **Filter by state:** Use the dropdown to filter villages by state
- **Language toggle:** Switch between English (EN), Hindi (हिं), and Marathi (मरा)
- **Photo map:** In the Document tab, red markers show where each photo was taken — click for popup with image and GPS data

---

## Processing a New Village PDF

### Prerequisites
- The PDF must be publicly accessible via a URL (Google Drive sharing link, Dropbox, or direct HTTP link)
- For Google Drive: Right-click file → Share → "Anyone with the link" → Copy link

### Steps

1. Go to **https://github.com/M89J/ver-platform/actions**
2. In the left sidebar, click **"Process Village PDF"**
3. Click the **"Run workflow"** button (top right)
4. Fill in the form:

| Field | Description | Example |
|-------|-------------|---------|
| **village_name** | Lowercase, use underscores for spaces | `karjat` |
| **state** | Select from dropdown | `maharashtra` |
| **pdf_url** | Public URL to download the PDF | `https://drive.google.com/file/d/abc123/view` |
| **district** | District name (optional) | `Raigad` |
| **block** | Block/Taluka name (optional) | `Karjat` |

5. Click **"Run workflow"**
6. The pipeline will:
   - Download the PDF
   - Extract page images (Step 1)
   - Run OCR with the correct language (Step 2)
   - Detect VER sections (Step 3)
   - Structure data into JSON (Step 4)
   - Select field photos (Step 5)
   - Rebuild the GeoJSON map layer
   - Create a **Pull Request** with the results

7. Go to **https://github.com/M89J/ver-platform/pulls** to review the PR
8. Check the processing summary (OCR confidence, sections detected, photos)
9. **Merge the PR** to make the data live on the platform

### Processing Time
- Depends on PDF size (number of pages)
- Typical: **15-30 minutes** for a 100-150 page PDF
- You can monitor progress in the Actions tab

### Supported States & Languages

| State | Language | Auto-detected |
|-------|----------|:---:|
| Maharashtra | Marathi + English | ✓ |
| Gujarat | Gujarati + English | ✓ |
| Chhattisgarh | Hindi + English | ✓ |
| Odisha | Odia + Hindi + English | ✓ |
| Rajasthan | Hindi + English | ✓ |
| North-East | English | ✓ |
| Andhra Pradesh | Telugu + English | ✓ |
| Telangana | Telugu + English | ✓ |
| Karnataka | Kannada + English | ✓ |

---

## Preparing Google Drive PDF Links

1. Upload the village PDF to Google Drive
2. Right-click the file → **Share**
3. Change access to **"Anyone with the link"** → **Viewer**
4. Click **"Copy link"**
5. Use this link as the `pdf_url` in the workflow

---

## Reviewing and Editing Data

### Using the Review Tool
1. Go to **https://m89j.github.io/ver-platform/review.html**
2. Upload the village's structured JSON file
3. The tool shows the scanned page alongside the extracted data
4. Edit fields directly in the form
5. Export the corrected JSON

### Manual Editing
1. Edit `data/structured/<village>.json` directly on GitHub
2. Or clone the repo locally and edit:
   ```bash
   git clone https://github.com/M89J/ver-platform.git
   cd ver-platform
   # Edit the JSON file
   git add data/structured/<village>.json
   git commit -m "Correct data for <village>"
   git push
   ```

---

## Adding Geotagged Photos Manually

Photos with GPS coordinates can be added to `data/photos/<village>/` and referenced in the village JSON:

```json
{
  "photos": [
    {
      "image_path": "data/photos/<village>/photo_name.jpeg",
      "caption": "Description of the photo",
      "caption_local": "स्थानिक भाषेत वर्णन",
      "coordinates": {"latitude": 20.001, "longitude": 78.198},
      "elevation_m": 330.5,
      "timestamp": "2025-01-17",
      "category": "water_source"
    }
  ]
}
```

**Photo categories:** `cultural_site`, `old_tree`, `water_source`, `traditional_crop`, `cultural_event`, `biodiversity`, `flora`, `sacred_grove`, `forest`, `grassland`

---

## Storage & Limits

| What | Per village | 200 villages | Where |
|------|-----------|-------------|-------|
| Raw PDFs | ~40 MB | ~8 GB | Google Drive (NOT in GitHub) |
| Structured JSON | ~50 KB | ~10 MB | GitHub repo |
| Selected photos | ~3 MB | ~600 MB | GitHub repo |
| GeoJSON | Single file | ~1 MB | GitHub repo |

**Important:** The repository must remain **public** for free GitHub Pages hosting. Raw PDFs are stored externally (Google Drive) and never committed to the repo.

---

## Batch Processing

For processing multiple villages at once:

1. Edit `data/batch_manifest.json` to add villages to the `pending` list:
   ```json
   {
     "pending": [
       {
         "village_name": "village_a",
         "state": "maharashtra",
         "pdf_url": "https://drive.google.com/...",
         "district": "Pune",
         "block": "Mulshi"
       }
     ]
   }
   ```
2. Run each village through the "Process Village PDF" workflow
3. After processing, move the entry from `pending` to `completed`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Site shows 404 | Go to repo Settings → Pages → re-enable from `main` branch, `/` root |
| Workflow fails at download | Check PDF URL is publicly accessible (try opening in incognito) |
| Low OCR quality | Expected for handwritten docs. Use the Review Tool to correct data |
| Photos not showing | Ensure `image_path` in JSON matches actual file path in repo |
| Map not loading | Check browser console for errors. Clear cache with Ctrl+Shift+R |
| Tabs show no data | Structured JSON arrays may be empty — edit JSON to populate data |

---

## Contact & Support

- **Repository Issues:** https://github.com/M89J/ver-platform/issues
- **Data Standards:** See `DATA_STANDARDS.md` in the repository
- **Schema Reference:** See `schema/ver_schema.json` for the complete data structure
