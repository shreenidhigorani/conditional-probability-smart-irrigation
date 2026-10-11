"""Sort the flat results/ folder into sub-folders.  Safe: never overwrites, never deletes.

Run from the repo root:
    python organize_results.py --dry-run     # show what would move
    python organize_results.py               # do it
"""
import argparse
import shutil
from pathlib import Path

RESULTS = Path("results")


def destination(name: str):
    """Return the sub-folder for a file, or None to leave it where it is."""
    if name == "README.md":
        return None
    if name.endswith(".png"):
        return "figures"
    if name.endswith(".xlsx"):
        return "verification"
    if name.endswith(".txt") or name.endswith(".log"):
        return "logs"
    if name.startswith("partB_"):
        return "tables/decision"
    if name.startswith("worked_example"):
        return "tables/worked_example"
    if name.startswith("table_"):
        return "tables/independence"
    return "tables/other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not RESULTS.is_dir():
        raise SystemExit(
            "Run this from the repo root (the folder that contains results/).")

    moved = 0
    for f in sorted(RESULTS.iterdir()):
        if not f.is_file():
            continue
        sub = destination(f.name)
        if sub is None:
            continue
        target = RESULTS / sub / f.name
        if target.exists():
            print(f"SKIP (already exists): {target}")
            continue
        print(f"{f}  ->  {target}")
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(target))
        moved += 1
    print(f"\n{'Would move' if args.dry_run else 'Moved'} {moved} files.")


if __name__ == "__main__":
    main()
