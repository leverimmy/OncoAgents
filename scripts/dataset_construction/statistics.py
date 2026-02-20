import argparse
import json
from pathlib import Path

from matplotlib import pyplot as plt

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

TYPES_TRANSLATION = {
    "肺癌": "Lung Cancer",
    "乳腺癌": "Breast Cancer",
    "胃癌": "Gastric Cancer",
    "结直肠癌": "Colorectal Cancer",
    "前列腺癌": "Prostate Cancer",
}

def load_from_dir(path: Path) -> list[dict]:
    data = []
    for file in path.glob('**/*.json'):
        with open(file, encoding='utf-8') as f:
            profile = json.load(f)
            data.append({file: profile})
    return data

def plot_background(data: list[dict], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    for key in KEYS:
        values = {}
        for profile in data:
            file, profile = list(profile.items())[0]
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

def plot_background_2x2(data: list[dict], output_dir: Path):
    """画出背景信息的 2x2 宫格分布图"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 创建 2x2 的画布，设置足够大的尺寸以容纳 4 个图
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten() # 展平为一维数组，方便在下面的 for 循环中通过索引直接调用

    for i, key in enumerate(KEYS):
        values = {}
        for item in data:
            file, profile = list(item.items())[0]
            personal_info = profile.get("personal_info", {})
            
            # 查找并统计包含当前 key 的数据
            for category in personal_info:
                if key in personal_info[category]:
                    raw_value = personal_info[category][key]
                    # 使用 get 提供容错机制，如果遇到没有在 TRANSLATION 里定义的脏数据，能直接打印原值而不会报错
                    value = TRANSLATION.get(raw_value, raw_value)
                    values[value] = values.get(value, 0) + 1

        # 2. 准备作图数据
        x_labels = list(values.keys())
        y_counts = list(values.values())

        # 3. 在对应的子图 (ax) 上作图
        ax = axes[i]
        # 画饼图
        # 颜色列表，确保每个类别有不同的颜色
        colors = plt.cm.Paired.colors # 使用 matplotlib 内置的配色方案
        ax.pie(y_counts, labels=[f"{label} ({count})" for label, count in values.items()], autopct='%1.1f%%', startangle=140, colors=colors[:len(x_labels)])
        # ax.bar(x_labels, y_counts, color='#66b3ff', edgecolor='black')
        
        # 格式化标题，例如把 "education_level" 变成 "Education Level"
        title = key.replace('_', ' ').title()
        ax.set_title(f'{title} Distribution', fontsize=14)
        # ax.set_ylabel('Numbers')
        
        # 重点：设置 x 轴刻度和标签，旋转 30 度并右对齐，防止长单词重叠
        # ax.set_xticks(range(len(x_labels)))
        # ax.set_xticklabels(x_labels, rotation=30, ha='right')

    # 4. 自动调整子图间距，防止文字被遮挡
    plt.tight_layout()
    
    # 保存整合后的大图
    plt.savefig(output_dir / 'background_distribution_2x2.png', dpi=150)
    plt.close()

def plot_type(data: list[dict], output_dir: Path):
    """画出按癌种分布的分布图 pie chart，写清楚具体数量"""
    types = []
    for profile in data:
        file, profile = list(profile.items())[0]
        cancer_type = file.stem.split("_")[-1]
        types.append(TYPES_TRANSLATION.get(cancer_type, cancer_type))
    type_counts = {}
    for t in types:
        type_counts[t] = type_counts.get(t, 0) + 1
    plt.figure(figsize=(8, 8))
    plt.pie(type_counts.values(), labels=[f"{t} ({c})" for t, c in type_counts.items()], autopct='%1.1f%%', startangle=140)
    plt.title('Cancer Type Distribution')
    plt.tight_layout()
    plt.savefig(output_dir / 'cancer_type_distribution.png')
    plt.close()

def plot_stage(data: list[dict], output_dir: Path):
    """画出按分期分布的分布图"""
    stages = []
    for profile in data:
        file, profile = list(profile.items())[0]
        stage = profile["diagnosis"]["stage"]
        stages.append(stage)
    pass

def plot_gender(data: list[dict], output_dir: Path):
    """画出按性别分布的分布图, pie chart，写清楚具体数量"""
    genders = []
    for profile in data:
        file, profile = list(profile.items())[0]
        gender = profile["personal_info"]["demographics"]["gender"]
        if gender == "男":
            gender = 'Male'
        elif gender == "女":
            gender = 'Female'
        else:
            print(f"Invalid gender value: {file}")
            continue
        genders.append(gender)
    gender_counts = {}
    for g in genders:
        gender_counts[g] = gender_counts.get(g, 0) + 1

    plt.figure(figsize=(8, 8))
    plt.pie(gender_counts.values(), labels=[f"{g} ({c})" for g, c in gender_counts.items()], autopct='%1.1f%%', startangle=140)
    plt.title('Gender Distribution')
    plt.tight_layout()
    plt.savefig(output_dir / 'gender_distribution.png')
    plt.close()

def plot_age_gender_stacked(data: list[dict], output_dir: Path):
    """画出按年龄和性别分布的堆叠直方图"""
    male_ages = []
    female_ages = []
    for item in data:
        # 获取文件名和对应的 profile 数据
        file, profile = list(item.items())[0]
        demographics = profile["personal_info"]["demographics"]
        
        # 1. 提取并校验性别
        gender = demographics.get("gender")
        if gender == "男":
            is_male = True
        elif gender == "女":
            is_male = False
        else:
            print(f"Invalid gender value: {file}")
            continue # 性别不合法则跳过这条数据

        # 2. 提取并校验年龄
        age_str = demographics.get("age", "")
        if "岁" in age_str:
            age_str = age_str.replace("岁", "")
            
        try:
            age = int(age_str)
        except ValueError:
            print(f"Invalid age value: {file}")
            continue # 年龄不合法则跳过这条数据
            
        # 3. 根据性别将年龄分装到不同的列表中
        if is_male:
            male_ages.append(age)
        else:
            female_ages.append(age)

    # 4. 开始绘图
    plt.figure(figsize=(10, 6))
    
    # plt.hist([female_ages, male_ages], bins=20, stacked=True, 
            #  color=['#ff9999', '#66b3ff'], label=['Female', 'Male'], edgecolor='black')
    plt.hist([male_ages, female_ages], bins=20, stacked=True, 
             color=['#66b3ff', '#ff9999'], label=['Male', 'Female'], edgecolor='black')
    
    plt.title('Age Distribution by Gender')
    plt.xlabel('Age')
    plt.ylabel('Numbers')
    plt.legend() # 显示图例，让人知道哪种颜色代表哪个性别
    plt.tight_layout()
    
    # 保存图片
    plt.savefig(output_dir / 'age_gender_stacked_distribution.png')
    plt.close()

def plot_age(data: list[dict], output_dir: Path):
    """画出按年龄分布的分布图"""
    ages = []
    for profile in data:
        file, profile = list(profile.items())[0]
        age = profile["personal_info"]["demographics"]["age"]
        if "岁" in age:
            age = age.replace("岁", "")
        try:
            ages.append(int(age))
        except ValueError:
            print(f"Invalid age value: {file}")
    plt.figure(figsize=(10, 6))
    plt.hist(ages, bins=20)
    plt.title('Age distribution')
    plt.xlabel('Age')
    plt.ylabel('Numbers')
    plt.tight_layout()
    plt.savefig(output_dir / 'age_distribution.png')
    plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate statistics and visualizations for patient profiles.")
    parser.add_argument('--input_dir', type=str, required=True, help='Path to the input directory containing patient profiles.')
    parser.add_argument('--output_dir', type=str, required=True, help='Path to the output directory for saving statistics and visualizations.')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    data = load_from_dir(input_dir)
    # plot_background(data, output_dir)
    plot_background_2x2(data, output_dir)
    plot_type(data, output_dir)
    # plot_stage(data, output_dir)
    plot_gender(data, output_dir)
    # plot_age(data, output_dir)
    plot_age_gender_stacked(data, output_dir)
