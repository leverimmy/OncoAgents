import argparse
import json
from pathlib import Path
from tqdm import tqdm

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Reformat processed JSON files.")
    parser.add_argument('--input_dir', type=str, required=False, default='.', help='Path to the directory containing processed JSON files.')
    parser.add_argument('--output_dir', type=str, required=False, default='./output', help='Path to the output directory for reformatted JSON files.')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(input_dir.glob("*_processed.json"))
    for json_file in tqdm(json_files, desc="Reformatting JSON files"):
        with open(json_file, 'r') as f:
            data = json.load(f)
        with open(output_dir / (json_file.stem + ".json"), 'w') as f:
            personal = data.get('personal_info', {})
            demo = personal.get('demographics', {})
            hist = personal.get('personal_history', {})
            symptom = data.get('symptom', {})
            phy = data.get('physical_examination', {})

            aux_list = []
            for item in data.get('auxiliary_examination', []):
                print(f"item: {item}")
                aux_list.append({
                    "检查类型": item.get('check_type', ''),
                    "检查项目": item.get('item', ''),
                    "结果": item.get('result', ''),
                })
        
            output_content = {
                "个人信息": {
                    "人口信息": {
                        "姓名": demo.get('name', ''),
                        "年龄": str(demo.get('age', '')),
                        "性别": demo.get('gender', ''),
                    },
                    "个人史": {
                        "吸烟史": hist.get('smoking_status', ''),
                        "饮酒史": hist.get('alcohol_use', ''),
                        "婚育史": hist.get('marriage_childbearing_history', ''),
                        "家族史": hist.get('family_history', ''),
                    }
                },
                "症状信息": {
                   "主诉": symptom.get('chief_complaint', ''),
                   "伴随症状": symptom.get('additional_symptom', ''),
                   "持续时间": symptom.get('symptom_duration', ''),
                },
                "体格检查": {
                    "基本信息": phy.get('basic_info', ''),
                    "一般状况": phy.get('general_condition', ''),
                    "专科检查": phy.get('special_examination', ''),
                },
                "辅助检查": aux_list,
                "诊断结果": data.get('diagnosis', ''),
                "治疗方案": data.get('treatment', '')
            }
            
            json.dump(output_content, f, ensure_ascii=False, indent=4)
