import argparse
import json
import os
import sys
from pathlib import Path
from time import sleep

import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
from wordcloud import WordCloud

sys.path.append(os.path.abspath("../../"))

from src.prompt import DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE
from src.utils import SafeDict, render_diagnosis_data, render_user_profile

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
)
model_name = "o3"

def get_llm_output(prompt: str) -> dict:
    cnt = 0
    while True:
        try:
            cnt += 1
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=4096,
            )
            content = response.choices[0].message.content.strip()
            if "</think>" in content:
                content = content.split("</think>")[-1].strip()
            return json.loads(content)
        except Exception as e:
            print(f"请求失败，正在重试... 错误信息: {e}")
            if cnt >= 5:
                print("重试次数过多，返回空结果")
                return {}
            else:
                sleep(2 ** cnt - 1)

def render_dialogue_history(conversation_history: list[dict], role: str | None = None) -> str:
    dialogue_history = ""
    for turn in conversation_history:
        try:
            assert turn["speaker"] in ["Doctor", "Patient"]
            if role is not None and turn["speaker"] != role:
                continue
            if turn["speaker"] == "Doctor":
                dialogue_history += "医生：" + turn["message"]["response"] + "\n"
            else:
                dialogue_history += "患者：" + turn["message"]["response"] + "\n"

        except Exception as e:
            print(f'Error processing turn: {turn}, turn["speaker"]: {e}')
    return dialogue_history

def generate_wordcloud_from_dict(
    word_weights: dict[str, int],
    out_path: str | None = None,
    font_path: str | None = None,
    width: int = 1600,
    height: int = 1000,
    background_color: str = "white",
    max_words: int = 200,
    random_state: int = 42,
) -> tuple[WordCloud, plt.Figure]:
    """
    根据 {word: weight} 字典生成词云。

    参数
    ----
    word_weights : Dict[str, int]
        词频/权重字典，例如 {"共情": 100, "安抚": 80, "解释": 70}
    out_path : str | None
        保存路径，例如 "wordcloud.png"；为 None 时不保存
    font_path : str | None
        中文字体路径。中文词云通常必须提供，否则可能显示为方块。
        例如：
        - macOS: "/System/Library/Fonts/STHeiti Light.ttc"
        - Windows: "C:/Windows/Fonts/simhei.ttf"
        - Linux: "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    width, height : int
        输出图像尺寸
    background_color : str
        背景颜色
    max_words : int
        最大显示词数
    random_state : int
        随机种子，固定后结果更稳定

    返回
    ----
    wc : WordCloud
        生成后的 WordCloud 对象
    fig : matplotlib.figure.Figure
        matplotlib 图对象
    """
    if not isinstance(word_weights, dict) or not word_weights:
        raise ValueError("word_weights 必须是非空 dict，例如 {'共情': 100, '安抚': 80}")

    # 过滤非法值，确保权重为正数
    clean_weights = {}
    for k, v in word_weights.items():
        if not isinstance(k, str):
            continue
        try:
            v = int(v)
        except Exception:
            continue
        if v > 0:
            clean_weights[k] = v

    if not clean_weights:
        raise ValueError("清洗后没有可用词条，请检查输入 dict 是否包含正整数权重。")

    wc = WordCloud(
        font_path=font_path,
        width=width,
        height=height,
        background_color=background_color,
        max_words=max_words,
        random_state=random_state,
        collocations=False,   # 避免自动把相邻词拼成短语
        prefer_horizontal=0.9
    ).generate_from_frequencies(clean_weights)

    fig = plt.figure(figsize=(width / 100, height / 100))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)

    if out_path:
        wc.to_file(out_path)

    return wc, fig

BASELINE_PROMPT = """你是一个医生。你需要根据以下内容总结出“如何告知这个患者癌症诊断结果”的策略，输出一个词云图权重，输出格式为 JSON 字典，键为沟通策略关键词，值为权重（整数）。权重数值应根据策略的重要程度和频次进行合理分配，数值越大表示该策略越重要或出现频次越高。请确保输出的 JSON 格式正确且包含至少 20 个关键词。

## 患者画像
{user_profile}

## 诊断结果
{diagnosis_data}

## 输出格式（必须严格遵守）

请严格按照以下 JSON 格式输出（不要输出 markdown、解释或多余文本）：
{{
    "关键词1": 权重1,
    "关键词2": 权重2,
    ...
}}
"""

FRAMEWORK_PROMPT = """你是一个医生。你需要根据以下内容总结出“如何告知这个患者癌症诊断结果”的策略，输出一个词云图权重，输出格式为 JSON 字典，键为沟通策略关键词，值为权重（整数）。权重数值应根据策略的重要程度和频次进行合理分配，数值越大表示该策略越重要或出现频次越高。请确保输出的 JSON 格式正确且包含至少 20 个关键词。你需要基于【同一患者的5段模拟医患对话历史】做“跨对话对比分析”，提炼出可被真实临床医生直接执行、并能稳定改善沟通过程的【沟通策略】。

## 患者画像
{user_profile}

## 诊断结果
{diagnosis_data}

## 以往对话记录
{dialogue_histories}

## 输出格式（必须严格遵守）

请严格按照以下 JSON 格式输出（不要输出 markdown、解释或多余文本）：
{{
    "关键词1": 权重1,
    "关键词2": 权重2,
    ...
}}
"""


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="生成患者沟通策略词云")
    parser.add_argument("--input_dir", type=str, help="Input data directory path.")
    parser.add_argument("--output_dir", type=str, help="输出图片路径")
    parser.add_argument("--font_path", type=str, default="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", help="中文字体路径")
    parser.add_argument("--framework", action="store_true", help="是否使用框架增强的提示词")

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if args.framework:
        output_dir = output_dir / "framework"
    else:
        output_dir = output_dir / "baseline"
    output_dir.mkdir(parents=True, exist_ok=True)

    # dialogue_histories = ""
    # for idx, file in enumerate(input_dir.glob("**/*.json")):
    #     data = json.load(file.open())
    #     dialogue_histories += f"**对话 {idx + 1}**\n" + render_dialogue_history(data["conversation_history"]) + "\n\n"

    for file in input_dir.glob("**/*.json"):
        print(f"Processing file: {file}")
        data = json.load(file.open())
        format_args = SafeDict(
            user_profile=render_user_profile(data["patient_data"], role="Doctor", with_symptoms=True),
            diagnosis_data=render_diagnosis_data(data["examination_data"], with_exams=True),
            dialogue_histories=render_dialogue_history(data["conversation_history"], role=None),
        )

        if args.framework:
            prompt_template = FRAMEWORK_PROMPT
        else:
            prompt_template = BASELINE_PROMPT
        
        # print(f"Generated prompt:\n{prompt_template.format_map(format_args)}")
        result = get_llm_output(prompt_template.format_map(format_args))

        generate_wordcloud_from_dict(
            word_weights=result,
            out_path=output_dir / f"{file.stem}.png",
            font_path=args.font_path,
        )

    #     break  # 仅处理一个文件，测试用
    # result = {
    #     "先共情再告知诊断": 100,
    #     "接纳患者情绪": 96,
    #     "主动询问最担心的问题": 92,
    #     "情绪安抚与稳定焦虑": 90,
    #     "使用简单生活化语言": 88,
    #     "避免复杂医学术语": 84,
    #     "先说核心结论": 82,
    #     "分步骤解释病情": 80,
    #     "解释晚期但仍可治疗": 78,
    #     "强调治疗目标是控制与延长生命": 76,
    #     "提供希望但避免过度承诺": 74,
    #     "解释治疗流程与节奏": 72,
    #     "说明化疗常见副作用": 70,
    #     "提前说明副作用可控制": 68,
    #     "具体说明疼痛管理": 66,
    #     "解释费用与医保报销": 64,
    #     "讨论经济负担与援助": 62,
    #     "鼓励患者表达情绪": 60,
    #     "允许患者反复提问": 58,
    #     "对寿命问题谨慎回答": 56,
    #     "强调个体差异": 54,
    #     "引导关注当前治疗步骤": 52,
    #     "明确下一步治疗安排": 50,
    #     "分阶段提供信息": 48,
    #     "频繁确认患者理解": 46,
    #     "邀请家属参与沟通": 44,
    #     "提供持续陪伴感": 42,
    #     "鼓励患者表达家庭担忧": 40,
    #     "提供心理支持资源": 38,
    #     "保持语气温和稳定": 36
    # }
    # generate_wordcloud_from_dict(
    #     word_weights=result,
    #     out_path=output_dir / f"example.png",
    #     font_path=args.font_path,
    # )
