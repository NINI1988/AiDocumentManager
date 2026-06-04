from pathlib import Path
import shutil

from utils.common import FOLDER_REVIEW, unique_path, print_rows_table

DEST_ROOT = Path(r"G:\Dropbox\Dokumente")


def move_review_files() -> None:
    if not FOLDER_REVIEW.exists():
        print(f"Review folder not found: {FOLDER_REVIEW}")
        return

    if not DEST_ROOT.exists():
        print(f"Destination folder not found: {DEST_ROOT}")
        return

    files = [path for path in FOLDER_REVIEW.rglob("*") if path.is_file()]
    moved = 0
    rows: list[tuple[str, str]] = []

    for src_path in files:
        relative_path = src_path.relative_to(FOLDER_REVIEW)
        dest_path = DEST_ROOT / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path = unique_path(dest_path)

        try:
            shutil.move(str(src_path), str(dest_path))
            moved += 1
            rows.append((str(src_path), str(dest_path)))
        except Exception as exc:
            print(f"Failed to move {src_path}: {exc}")

    if not files:
        print("No files found to move.")

    if moved == 0:
        if not files:
            return
        print("No files were moved.")
        return

    print_rows_table(rows)
    print(f"Done. {moved}/{len(files)} file(s) moved.")
    
    removed_dirs = remove_empty_directories(FOLDER_REVIEW)
    if removed_dirs:
        print(f"Removed {removed_dirs} empty folder(s) from '{FOLDER_REVIEW}'.")


def remove_empty_directories(root: Path) -> int:
    """Remove empty directories recursively under root and return how many were removed."""
    removed = 0
    for directory in sorted((p for p in root.rglob("*") if p.is_dir()), reverse=True):
        try:
            directory.rmdir()
            removed += 1
        except OSError:
            continue
    return removed


if __name__ == "__main__":
    move_review_files()
    input("Press Enter to exit...")
