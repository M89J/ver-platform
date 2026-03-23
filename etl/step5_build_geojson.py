"""
Step 5: Build GeoJSON
Aggregates all structured village JSONs into a single GeoJSON file for the map layer.
Computes summary statistics per village for map popups.

Usage:
    python step5_build_geojson.py

Input:  data/structured/*.json
Output: data/villages.geojson
"""
import json
import sys
from pathlib import Path

from config import STRUCTURED_DIR, DATA_DIR


def compute_village_summary(village_data: dict) -> dict:
    """Compute summary stats for map popup display."""
    gen = village_data.get("section_2_general_info", {})
    livestock = village_data.get("section_5_livestock", {})
    flora = village_data.get("section_20_flora_fauna", {})
    water = village_data.get("section_6_waterscape", {})

    # Count biodiversity entries
    bio_counts = {}
    if flora:
        for group_key in ["trees", "shrubs", "herbs_and_grasses", "mammals", "birds",
                          "reptiles_amphibians", "butterflies", "dragonflies",
                          "fish_insects_others", "soil_macrofauna"]:
            items = flora.get(group_key, [])
            if items:
                bio_counts[group_key] = len(items)

    # Count livestock
    livestock_total = 0
    for entry in livestock.get("livestock_numbers", []):
        count = entry.get("current_count", 0)
        if isinstance(count, int):
            livestock_total += count

    return {
        "population": gen.get("caste_composition", {}).get("total_population"),
        "total_area_ha": gen.get("land_details", {}).get("total_village_area_ha"),
        "forest_area_ha": gen.get("land_details", {}).get("forest_land_ha"),
        "agricultural_area_ha": gen.get("land_details", {}).get("agricultural_land_ha"),
        "total_households": sum([
            gen.get("landholding", {}).get(k, 0) or 0
            for k in ["large_above_10ha", "medium_4_to_10ha", "semi_medium_2_to_4ha",
                       "small_1_to_2ha", "marginal_below_1ha", "landless"]
        ]),
        "livestock_total": livestock_total,
        "biodiversity_counts": bio_counts,
        "total_species_recorded": sum(bio_counts.values()),
        "water_sources_count": len(water.get("drinking_water", [])),
        "livelihoods": [l.get("name", "") for l in gen.get("major_livelihoods", [])[:5]],
        "data_status": village_data.get("metadata", {}).get("data_status", "unknown"),
        "ver_year": village_data.get("metadata", {}).get("ver_year", ""),
    }


def main():
    village_files = sorted(STRUCTURED_DIR.glob("*.json"))

    if not village_files:
        print(f"No structured village files found in {STRUCTURED_DIR}")
        sys.exit(1)

    features = []
    skipped = []

    for vf in village_files:
        data = json.loads(vf.read_text(encoding="utf-8"))
        gen = data.get("section_2_general_info", {})
        coords = gen.get("coordinates", {})
        lat = coords.get("latitude")
        lon = coords.get("longitude")

        if lat is None or lon is None:
            skipped.append(vf.stem)
            print(f"  Skipping {vf.stem}: no coordinates")
            continue

        summary = compute_village_summary(data)

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]  # GeoJSON uses [lon, lat]
            },
            "properties": {
                "village_id": data.get("metadata", {}).get("village_id", vf.stem),
                "village_name": gen.get("village_name", vf.stem),
                "village_name_local": gen.get("village_name_local", ""),
                "state": gen.get("state", ""),
                "district": gen.get("district", ""),
                "block": gen.get("block", ""),
                "gram_panchayat": gen.get("gram_panchayat", ""),
                **summary,
                "data_file": f"data/structured/{vf.name}",
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "title": "Village Ecological Register - Village Locations",
            "description": "GeoJSON layer of all VER villages with summary data for map display",
            "total_villages": len(features),
            "skipped_no_coords": len(skipped),
        },
        "features": features
    }

    output_path = DATA_DIR / "villages.geojson"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)

    print(f"\nBuilt GeoJSON with {len(features)} villages")
    if skipped:
        print(f"Skipped (no coordinates): {skipped}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
