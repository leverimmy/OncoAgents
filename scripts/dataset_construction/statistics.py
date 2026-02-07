import argparse
import json
from matplotlib import pyplot as plt
from pathlib import Path

KEYS = ["education_level", "financial_status", "personality", "communication_style"]
TRANSLATION = {
    # Education levels
    "小学及以下：识字/医学术语理解有限": "low_literacy",
    "初中：可理解生活化解释，需避免复杂概念": "basic_education",
    "高中/中专：能跟随基本因果解释，愿意听结论": "secondary_education",
    "本科：能理解风险概率与方案对比": "undergraduate",
    "硕博/医学相关背景：会追问证据等级与指南出处": "expert_level",

    # Financial statuses
    "困难：治疗费用压力大，倾向选择低成本方案": "financially_strained",
    "较差：依赖医保，关注报销范围与额度": "insurance_dependent",
    "中等：有医保但自付敏感，可承担常规治疗": "cost_sensitive",
    "较好：愿为疗效/舒适度付费，重视体验与效率": "value_oriented",
    "充裕：费用不是主要约束，优先考虑最优方案/专家资源": "cost_unconstrained",

    # Personalities
    "不耐烦：易怒、易激动、缺乏耐心": "impatient",
    "过度焦虑：总是感到担忧和紧张，难以放松": "anxious",
    "过度乐观：忽视风险，过分相信治疗效果": "overoptimistic",
    "不信任：对医疗系统或医生持怀疑态度": "distrustful",
    "啰嗦：喜欢详细讨论，难以集中主题": "verbose",
    "中性：情绪稳定，易于沟通": "neutral",

    # Communication styles
    "问题驱动型：喜欢提出问题，针对具体问题寻求解答": "question_driven",
    "信息收集型：喜欢获取大量背景信息和细节": "information_seeking",
    "情绪表达型：倾向于表达自己的情感和感受": "emotion_expressive",
    "沉默顺从型：被动回应，很少表达自己的想法": "passive",
    "冷静理性型：交流中一直保持冷静和理性，不受情绪影响": "analytical",
}


def load_from_dir(path: str):
    data = []
    path = Path(path)
    for file in path.glob('*.json'):
        with open(file, encoding='utf-8') as f:
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
                    value = TRANSLATION[profile[key1][key]]
                    values[value] = values.get(value, 0) + 1

        plt.figure(figsize=(10, 6))
        plt.bar(values.keys(), values.values())
        plt.title(f'{key} distribution')
        plt.xlabel(key)
        plt.ylabel('Numbers')
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
