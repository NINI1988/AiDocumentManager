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
        return

    if moved == 0:
        print("No files were moved.")
        return

    print_rows_table(rows)
    print(f"Done. {moved}/{len(files)} file(s) moved.")


if __name__ == "__main__":
    move_review_files()
