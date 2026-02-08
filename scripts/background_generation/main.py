import argparse
import json
from pathlib import Path

EDUCATION_LEVELS = [
    "小学及以下：识字/医学术语理解有限",
    "初中：可理解生活化解释，需避免复杂概念",
    "高中/中专：能跟随基本因果解释，愿意听结论",
    "本科：能理解风险概率与方案对比",
    "硕博/医学相关背景：会追问证据等级与指南出处",
]

FINANCIAL_STATUSES = [
    "困难：治疗费用压力大，倾向选择低成本方案",
    "较差：依赖医保，关注报销范围与额度",
    "中等：有医保但自付敏感，可承担常规治疗",
    "较好：愿为疗效/舒适度付费，重视体验与效率",
    "充裕：费用不是主要约束，优先考虑最优方案/专家资源",
]

PERSONALITIES = [
    "不耐烦：易怒、易激动、缺乏耐心",
    "过度焦虑：总是感到担忧和紧张，难以放松",
    "过度乐观：忽视风险，过分相信治疗效果",
    "不信任：对医疗系统或医生持怀疑态度",
    "啰嗦：喜欢详细讨论，难以集中主题",
    "中性：情绪稳定，易于沟通",
]

COMMUNICATION_STYLES = [
    "问题驱动型：喜欢提出问题，针对具体问题寻求解答",
    "信息收集型：喜欢获取大量背景信息和细节",
    "情绪表达型：倾向于表达自己的情感和感受",
    "沉默顺从型：被动回应，很少表达自己的想法",
    "冷静理性型：交流中一直保持冷静和理性，不受情绪影响",
]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate patient profiles based on various attributes.")
    parser.add_argument('--output_dir', type=str, required=True, help='Path to the output directory for generated profiles.')
    args = parser.parse_args()

    idx = 0
    for ll, education_level in enumerate(EDUCATION_LEVELS):
        for k, financial_status in enumerate(FINANCIAL_STATUSES):
            if ll == 3 and k <= 1:
                continue
            if ll == 4 and k <= 2:
                continue
            for i, personality in enumerate(PERSONALITIES):
                if k >= 3 and i == 2:
                    continue
                for j, communication_style in enumerate(COMMUNICATION_STYLES):
                    if j >= 3 and i <= 2:
                        continue
                    result = {
                        "personal_info": {
                            "social_background": {
                                "education_level": education_level,
                                "financial_status": financial_status,
                            },
                            "characteristics": {
                                "personality": personality,
                                "communication_style": communication_style
                            }
                        }
                    }
                    with open(Path(args.output_dir) / f'{idx}.json', 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=4)
                        idx += 1
    print(f"Generated {idx} patient profiles in {args.output_dir}")
