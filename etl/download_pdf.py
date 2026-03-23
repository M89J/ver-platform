"""
Download PDF from a URL (supports Google Drive, Dropbox, direct HTTP).
Validates the downloaded file is a valid PDF.

Usage:
    python download_pdf.py --url "https://drive.google.com/file/d/FILE_ID/view" --output data/raw/village/VER.pdf
"""
import argparse
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path


def convert_drive_url(url: str) -> str:
    """Convert Google Drive sharing URL to direct download URL."""
    # Pattern: https://drive.google.com/file/d/FILE_ID/view...
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
    # Pattern: https://drive.google.com/open?id=FILE_ID
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
    return url


def convert_dropbox_url(url: str) -> str:
    """Convert Dropbox sharing URL to direct download URL."""
    if 'dropbox.com' in url:
        return url.replace('dl=0', 'dl=1').replace('www.dropbox.com', 'dl.dropboxusercontent.com')
    return url


def resolve_url(url: str) -> str:
    """Convert sharing URLs to direct download URLs."""
    if 'drive.google.com' in url:
        return convert_drive_url(url)
    if 'dropbox.com' in url:
        return convert_dropbox_url(url)
    return url


def download(url: str, output_path: Path, max_retries: int = 3) -> bool:
    """Download file from URL with retry logic."""
    direct_url = resolve_url(url)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Downloading (attempt {attempt}/{max_retries})...")
            print(f"  URL: {direct_url[:80]}...")
            req = urllib.request.Request(direct_url, headers={
                'User-Agent': 'Mozilla/5.0 (VER ETL Pipeline)'
            })
            with urllib.request.urlopen(req, timeout=300) as response:
                data = response.read()
                output_path.write_bytes(data)
                size_mb = len(data) / (1024 * 1024)
                print(f"  Downloaded: {size_mb:.1f} MB -> {output_path}")
                return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"  Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                print(f"ERROR: Failed to download after {max_retries} attempts")
                return False
    return False


def validate_pdf(path: Path) -> bool:
    """Check that the file is a valid PDF by reading magic bytes."""
    if not path.exists():
        print(f"ERROR: File does not exist: {path}")
        return False
    with open(path, 'rb') as f:
        header = f.read(5)
    if header != b'%PDF-':
        print(f"ERROR: File is not a valid PDF (header: {header!r})")
        print("  This may be an HTML page (e.g., Google Drive permission error)")
        return False
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"  Valid PDF: {size_mb:.1f} MB")
    return True


def main():
    parser = argparse.ArgumentParser(description="Download VER PDF from URL")
    parser.add_argument("--url", required=True, help="PDF download URL (Google Drive, Dropbox, or direct)")
    parser.add_argument("--output", required=True, help="Output file path")
    args = parser.parse_args()

    output = Path(args.output)
    if not download(args.url, output):
        sys.exit(1)
    if not validate_pdf(output):
        output.unlink(missing_ok=True)
        sys.exit(1)

    print("Download complete.")


if __name__ == "__main__":
    main()
