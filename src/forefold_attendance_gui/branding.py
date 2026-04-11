"""ForeFold app display name and logo path (dev + Nuitka standalone)."""

from __future__ import annotations

import sys
from pathlib import Path

APP_DISPLAY_NAME = "ForeFold Report Generator"


def public_logo_path() -> Path | None:
    """Logo next to the .exe when bundled, or src/public when running from source."""
    exe_dir = Path(sys.argv[0]).resolve().parent
    here = Path(__file__).resolve()
    src_public = here.parents[1] / "public" / "forefold-logo.png"
    for p in (exe_dir / "forefold-logo.png", src_public):
        if p.is_file():
            return p
    return None
