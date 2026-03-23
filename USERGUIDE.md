# VER Platform — User Guide

## Accessing the Platform

**Live URL:** https://m89j.github.io/ver-platform/

**Repository:** https://github.com/M89J/ver-platform

---

## Viewing Village Data

1. Open the platform URL in your browser
2. The map displays India with the official administrative boundary (country + 36 state/UT borders)
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
- **Search:** Click the search bar to see a dropdown list of all villages. Type to filter by name, state, or block. Click a village to zoom to it.
- **Filter by state:** Use the dropdown to filter villages by state — a list of matching villages appears automatically.
- **Language toggle:** Switch between English (EN), Hindi (हिं), and Marathi (मरा)
- **Photo map:** In the Document tab, red markers show where each photo was taken — click for popup with image and GPS data

---

## How Data Processing Works

```
Your PDF (any source) → Upload to Google Drive → GitHub Actions (auto OCR + ETL) → JSON stored in GitHub → Live site updates
```

**Key points:**
- You upload the PDF to Google Drive (or any source that provides a public download link)
- GitHub Actions **temporarily downloads** the PDF, runs OCR in the correct language (8 languages supported), and extracts structured data
- **The PDF is deleted after processing** — it is never stored in GitHub
- Only the lightweight extracted data is stored in GitHub:
  - Structured JSON (~50 KB per village)
  - Selected geotagged photos (~3 MB per village)
- The live site auto-updates when new data is merged

### What gets stored where

| What | Size | Where | Permanent? |
|------|------|-------|:---:|
| Raw scanned PDFs | ~40 MB each | Your system / Google Drive | Yes — you keep them |
| Structured JSON | ~50 KB each | GitHub repo (auto-generated) | Yes |
| Selected photos | ~3 MB each | GitHub repo (auto-extracted) | Yes |
| GeoJSON map layer | ~1 MB total | GitHub repo (auto-rebuilt) | Yes |
| OCR intermediate files | ~300 MB each | GitHub Actions runner | No — deleted after processing |

At 200 villages: ~10 MB of JSON + ~600 MB of photos in GitHub. Well within GitHub's limits.

---

## Processing a New Village PDF

### Step 1: Upload PDF to Google Drive
1. Upload the village PDF to your Google Drive
2. Right-click the file → **Share**
3. Change access to **"Anyone with the link"** → **Viewer**
4. Click **"Copy link"**

> You can also use Dropbox or any direct HTTP download link.

### Step 2: Run the Pipeline
1. Go to **https://github.com/M89J/ver-platform/actions**
2. In the left sidebar, click **"Process Village PDF"**
3. Click the **"Run workflow"** button (top right)
4. Fill in the form:

| Field | Description | Example |
|-------|-------------|---------|
| **village_name** | Lowercase, use underscores for spaces | `karjat` |
| **state** | Select from dropdown (auto-selects OCR language) | `maharashtra` |
| **pdf_url** | Public URL to download the PDF | `https://drive.google.com/file/d/abc123/view` |
| **district** | District name (optional) | `Raigad` |
| **block** | Block/Taluka name (optional) | `Karjat` |

5. Click **"Run workflow"**

### Step 3: What happens automatically
The pipeline runs these steps without any further action from you:
1. Downloads the PDF from your link
2. Converts each page to an image
3. Runs OCR with the correct language for the selected state
4. Detects the 20 VER sections in the document
5. Structures the OCR text into JSON format
6. Extracts and selects the best field photos
7. Rebuilds the GeoJSON map layer with the new village
8. Creates a **Pull Request** with all the results
9. **Deletes the PDF** — only JSON and photos remain

### Step 4: Review and merge
1. Go to **https://github.com/M89J/ver-platform/pulls** to see the PR
2. Check the processing summary (OCR confidence, sections detected, photo count)
3. **Merge the PR** to make the data live on the platform
4. The site updates automatically within 1-2 minutes

### Processing Time
- Typical: **15-30 minutes** for a 100-150 page PDF
- Monitor progress in the Actions tab

### Supported Languages (8 languages across 9 states)

The OCR language is **automatically selected** based on the state you choose:

| State | OCR Language | Tesseract Code |
|-------|-------------|----------------|
| Maharashtra | Marathi + English | mar+eng |
| Gujarat | Gujarati + English | guj+eng |
| Chhattisgarh | Hindi + English | hin+eng |
| Rajasthan | Hindi + English | hin+eng |
| Odisha | Odia + Hindi + English | ori+hin+eng |
| North-East | English | eng |
| Andhra Pradesh | Telugu + English | tel+eng |
| Telangana | Telugu + English | tel+eng |
| Karnataka | Kannada + English | kan+eng |

You just select the state — the language is handled automatically.

---

## Reviewing and Editing Data (Admin)

### Using the Review Tool
1. Go to **https://m89j.github.io/ver-platform/review.html** (admin only — not linked from public site)
2. Upload the village's structured JSON file
3. The tool shows the scanned page alongside the extracted data
4. Edit fields directly in the form to correct OCR errors
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

## Batch Processing

For processing multiple villages:

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
| Workflow fails at download | Check PDF URL is publicly accessible (try opening in incognito browser) |
| Low OCR quality | Expected for handwritten documents (~50% confidence). Use the Review Tool to correct data |
| Photos not showing | Ensure `image_path` in JSON matches actual file path in repo |
| Map not loading | Clear browser cache with Ctrl+Shift+R |
| Tabs show no data | Structured JSON arrays may be empty — use Review Tool or edit JSON to populate |
| Repository must stay public | GitHub Pages requires a public repo on the free plan |

---

## Contact & Support

- **Repository Issues:** https://github.com/M89J/ver-platform/issues
- **Data Standards:** See `DATA_STANDARDS.md` in the repository
- **Schema Reference:** See `schema/ver_schema.json` for the complete data structure
