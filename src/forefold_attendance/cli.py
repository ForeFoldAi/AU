"""CLI entrypoint for report generation."""

from __future__ import annotations

import argparse
import sys

from .engine import generate_report


def main() -> int:
    parser = argparse.ArgumentParser(description="BioTime Attendance Report CLI")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--company", default="")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    cfg = {
        "base_url": args.base_url,
        "company": args.company,
        "email": args.email,
        "password": args.password,
        "month": args.month,
        "year": args.year,
    }

    try:
        output, logs = generate_report(cfg, output=args.output)
        if logs.strip():
            print(logs)
        print(f"Report generated: {output}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
