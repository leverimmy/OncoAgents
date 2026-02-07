import argparse
import json
import random
import shutil
from pathlib import Path

names = ["张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十"]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Move processed files to a new directory.")
    parser.add_argument('--source_dir', type=str, help='Path to the source directory containing processed files.')
    parser.add_argument('--dest_dir', type=str, help='Path to the destination directory to move files to.')
    args = parser.parse_args()

    # 将 source_dir 下的所有文件，编号为 1.json, 2.json, ... 复制到 dest_dir
    source_path = Path(args.source_dir)
    dest_path = Path(args.dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    for idx, file in enumerate(source_path.iterdir(), start=1):
        if file.is_file() and file.suffix == '.json':
            new_file_name = dest_path / f"{idx}.json"
            shutil.copy(str(file), str(new_file_name))
            print(f"Copied {file.name} to {new_file_name}")
    print("All files copied successfully.")

    # 每个 Copied File，修改 "personal_info"."demographics"."name" 为随机姓名
    for file in dest_path.iterdir():
        if file.is_file() and file.suffix == '.json':
            with open(file, encoding='utf-8') as f:
                data = json.load(f)

            random_name = random.choice(names)
            if "personal_info" in data and "demographics" in data["personal_info"]:
                data["personal_info"]["demographics"]["name"] = random_name

            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Updated name in {file.name} to {random_name}")
    print("All names updated successfully.")
