import argparse
import json
from matplotlib import pyplot as plt
from pathlib import Path

KEYS = ["education_level", "financial_status", "personality", "communication_style"]
TRANSLATION = {
    "education_level": "受教育水平",
    "financial_status": "经济状况",
    "personality": "性格特点",
    "communication_style": "沟通风格",
}

def load_from_dir(path: str):
    data = []
    path = Path(path)
    for file in path.glob('*.json'):
        with open(file, 'r', encoding='utf-8') as f:
            profile = json.load(f)
            data.append(profile)
    return data

def save_figs(data, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for key in KEYS:
        values = {}
        for profile in data:
            profile = profile["personal_info"]
            for key1 in profile:
                if key in profile[key1]:
                    value = profile[key1][key].split("：")[0]
                    values[value] = values.get(value, 0) + 1

        plt.rcParams["font.sans-serif"] = ["SimHei"]
        plt.figure(figsize=(10, 6))
        plt.bar(values.keys(), values.values())
        plt.title(f'{TRANSLATION[key]}分布')
        plt.xlabel(TRANSLATION[key])
        plt.ylabel('人数')
        plt.tight_layout()
        plt.savefig(output_dir / f'{key}_distribution.png')
        plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate statistics and visualizations for patient profiles.")
    parser.add_argument('--input_dir', type=str, required=True, help='Path to the input directory containing patient profiles.')
    parser.add_argument('--output_dir', type=str, required=True, help='Path to the output directory for saving statistics and visualizations.')
    args = parser.parse_args()

    data = load_from_dir(args.input_dir)
    save_figs(data, args.output_dir)
