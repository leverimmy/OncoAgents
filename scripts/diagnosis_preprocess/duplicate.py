import argparse
import shutil
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Duplicate files in a directory.")
    parser.add_argument('--source_dir', type=str, help='Path to the source directory containing files to duplicate.')
    parser.add_argument('--dest_dir', type=str, help='Path to the destination directory to save duplicated files.')
    parser.add_argument('--start_id', type=int, help='Numbering start ID for duplicated files.')
    parser.add_argument('--num_duplicates', type=int, help='Number of duplicates to create.')
    args = parser.parse_args()

    source_path = Path(args.source_dir)
    dest_path = Path(args.dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    cnt = 0
    while True:
        for file in source_path.iterdir():
            if file.is_file() and file.suffix == '.json':
                new_file_name = dest_path / f"{args.start_id + cnt}.json"
                shutil.copy(str(file), str(new_file_name))
                print(f"Copied {file.name} to {new_file_name}")
                cnt += 1
            if cnt >= args.num_duplicates:
                break
        if cnt >= args.num_duplicates:
            break
    print("All files duplicated successfully.")
