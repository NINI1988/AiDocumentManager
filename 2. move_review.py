from pathlib import Path
import shutil

from utils.common import FOLDER_REVIEW, print_rows_table

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
    # rows: list[tuple[str, str]] = []

    for src_path in files:
        relative_path = src_path.relative_to(FOLDER_REVIEW)
        dest_path = DEST_ROOT / relative_path

        # Do not overwrite existing files; raise an error if destination exists.
        if dest_path.exists():
            raise FileExistsError(f"Destination exists: {dest_path}")

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(str(src_path), str(dest_path))
            moved += 1
            # rows.append((str(src_path), str(dest_path)))
            print(f"Moved: {dest_path}")
        except Exception as exc:
            print(f"Failed to move {src_path}: {exc}")

    if not files:
        print("No files found to move.")
    elif moved == 0:
        print("No files were moved.")
        return

    # print_rows_table(rows)
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
    try:
        move_review_files() 
    except Exception as e:
        print(f"Error during moving files: {e}")
    finally:
        input("Press Enter to exit...")
