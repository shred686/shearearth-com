#!/usr/bin/env python3
"""Package the child theme and setup plugin for WordPress admin uploads.

Run build-divi.py and check-layouts.py first so the bundled layouts are current.
"""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "wordpress" / "dist"


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for source in (
        ROOT / "wordpress/themes/shear-performance",
        ROOT / "wordpress/plugin/spe-site-importer",
    ):
        target = DEST / f"{source.name}.zip"
        with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(source.parent))
        print(f"{target.relative_to(ROOT)} ({target.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
