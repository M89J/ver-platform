"""
VER ETL Pipeline Runner
Orchestrates the full ETL pipeline for one or all villages.
Supports multi-state, multi-language processing.

Usage:
    python run_pipeline.py <village_name> --state maharashtra
    python run_pipeline.py <village_name> --state gujarat
    python run_pipeline.py --all                                # Uses village_registry.json for state info
    python run_pipeline.py <village_name> --state odisha --step 2  # Run specific step only

Steps:
    1. PDF → Page images
    2. Page images → OCR text (language auto-detected from state)
    3. OCR text → Section detection (multilingual headers)
    4. Section text → Structured JSON
    5. All JSONs → GeoJSON map layer
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from config import RAW_DIR, DATA_DIR, STATE_LANGUAGE_MAP


def run_step(step_script: str, args: list) -> bool:
    """Run an ETL step script and return success status."""
    cmd = [sys.executable, step_script] + args
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=str(Path(__file__).parent))
    return result.returncode == 0


def process_village(village_name: str, state: str = "", start_step: int = 1, end_step: int = 5):
    """Run ETL pipeline for a single village."""
    print(f"\n{'#'*60}")
    print(f"Processing village: {village_name}")
    if state:
        lang_info = STATE_LANGUAGE_MAP.get(state.lower(), {})
        print(f"State: {state} | Languages: {lang_info.get('languages', ['unknown'])}")
    print(f"Steps: {start_step} to {end_step}")
    print(f"{'#'*60}")

    # Build step arguments — pass --state to step 2 for language detection
    ocr_args = [village_name]
    if state:
        ocr_args.extend(["--state", state])

    steps = [
        (1, "step1_pdf_to_images.py", [village_name]),
        (2, "step2_ocr_extract.py", ocr_args),
        (3, "step3_section_detect.py", [village_name]),
        (4, "step4_structure_data.py", [village_name]),
        (5, "step5_build_geojson.py", []),
    ]

    for step_num, script, args in steps:
        if step_num < start_step or step_num > end_step:
            continue

        success = run_step(script, args)
        if not success:
            print(f"\nStep {step_num} failed for {village_name}. Stopping.")
            return False

    print(f"\nPipeline complete for {village_name}")
    return True


def load_village_registry() -> dict:
    """Load village registry mapping village names to states.
    Used for --all batch processing.
    """
    registry_path = DATA_DIR / "village_registry.json"
    if registry_path.exists():
        return json.loads(registry_path.read_text(encoding="utf-8"))
    return {}


def main():
    parser = argparse.ArgumentParser(description="VER ETL Pipeline Runner (Multi-state)")
    parser.add_argument("village_name", nargs="?", help="Village to process")
    parser.add_argument("--state", default="", help="State for language detection (maharashtra, gujarat, odisha, etc.)")
    parser.add_argument("--all", action="store_true", help="Process all villages using village_registry.json")
    parser.add_argument("--step", type=int, help="Run specific step only (1-5)")
    parser.add_argument("--from-step", type=int, default=1, help="Start from step (default: 1)")
    parser.add_argument("--to-step", type=int, default=5, help="End at step (default: 5)")
    args = parser.parse_args()

    if args.step:
        args.from_step = args.step
        args.to_step = args.step

    if args.all:
        registry = load_village_registry()
        villages = [d.name for d in RAW_DIR.iterdir() if d.is_dir()]
        if not villages:
            print(f"No village directories found in {RAW_DIR}")
            sys.exit(1)

        print(f"Found {len(villages)} villages: {villages}")
        print(f"Supported states: {list(STATE_LANGUAGE_MAP.keys())}")
        results = {}
        for v in sorted(villages):
            v_state = registry.get(v, {}).get("state", args.state)
            results[v] = process_village(v, v_state, args.from_step, min(args.to_step, 4))

        # Run GeoJSON build once at the end
        if args.to_step >= 5:
            run_step("step5_build_geojson.py", [])

        print(f"\n{'='*60}")
        print("SUMMARY")
        for v, success in results.items():
            status = "OK" if success else "FAILED"
            print(f"  {v}: {status}")

    elif args.village_name:
        process_village(args.village_name, args.state, args.from_step, args.to_step)

    else:
        parser.print_help()
        print(f"\nSupported states and languages:")
        for state, info in STATE_LANGUAGE_MAP.items():
            print(f"  {state:20s} → {', '.join(info['languages']):30s} (tesseract: {info['tesseract_lang']})")


if __name__ == "__main__":
    main()
