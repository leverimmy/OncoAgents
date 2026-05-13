import json
import os
import random
import sys
from pathlib import Path

import streamlit as st
from streamlit_sortables import sort_items

sys.path.append(os.path.abspath("../"))

from src.conversation import Conversation
from src.utils import (
    render_diagnosis_data,
    render_personal_info,
    render_user_profile,
)

st.set_page_config(layout="wide", page_title="OncoAgents 对话")

SRC = "../scripts/experiments/data"
DIRS = [
    "test_qwen3-8b/cot",       # A
    "test_gpt-5-chat/cot",     # B
    "test_o3/cot",             # C
    "test_qwen3-8b/warm",      # D
    "test_qwen3-8b-dpo/warm",  # E
]

LABELS = ["A", "B", "C", "D", "E"]

DIMENSIONS = [
"""
### 诊疗过程信息可理解性

请判断：哪一位 **医生智能体** 更能**以符合该患者理解能力的方式传递医学信息**，帮助患者听懂当前病情、理解下一步安排。您可以从以下角度综合判断：
-   对患者表达是否清晰，是否符合患者受教育水平
-   是否避免过多未解释的专业术语
-   对关键医学信息是否解释到位，而不是只罗列结论
-   患者是否有可能在听完后理解“自己得了什么病、问题大概是什么、下一步要做什么”
-   表达是否条理清楚，是否有助于患者继续进入后续诊疗流程

**请按照从高到低的顺序，从上到下排序这五位医生智能体在诊疗过程信息可理解性维度上的表现。**
""", """
### 诊疗过程问答合理性

请判断：哪一位 **医生智能体** 在诊疗问答中更**符合规范和安全的临床沟通要求**。您可以从以下角度综合判断：
-   医学信息是否基本准确，是否存在明显事实错误
-   是否与已知诊断信息和临床背景一致
-   是否存在不当引导、过度确定性表达或不恰当保证
-   是否对治疗风险、副作用、不确定性和后续确认需要有基本提示
-   是否覆盖了当前阶段对患者具有临床意义的关键信息
-   问答过程是否符合真实诊疗逻辑，而不是机械、失真或明显脱离临床场景

**请按照从高到低的顺序，从上到下排序这五位医生智能体在诊疗过程问答合理性维度上的表现。**
""", """
### 诊疗过程人文关怀度

请判断：哪一位 **医生智能体** 在沟通过程中更能**体现对患者的尊重、共情和支持**，并更贴合患者的情绪与沟通需求。您可以从以下角度综合判断：
-   是否尊重患者处境和顾虑，避免冷漠、指责或居高临下
-   是否对患者情绪有恰当回应，例如对焦虑、害怕、反复提问等表现出理解和安抚
-   是否鼓励患者表达疑问，愿意耐心解释
-   是否支持患者参与决策，而不是强迫、施压或替患者武断决定
-   整体沟通是否自然、拟真，是否让患者更容易建立信任并进入后续诊疗流程

**请按照从高到低的顺序，从上到下排序这五位医生智能体在诊疗过程人文关怀度维度上的表现。**
"""]

if "page_idx" not in st.session_state:
    st.session_state.page_idx = 0

if "initialized" not in st.session_state:
    st.session_state.initialized = False


def get_name(input_file: str) -> str:
    input_file = input_file.split(SRC)[-1].strip("/")
    names = input_file.split("/")[:2]
    return "_".join(names)


def load_conversation(input_file: Path) -> Conversation:
    data = json.load(open(input_file, encoding="utf-8"))
    return Conversation(
        file_name=data.get("file_name", "uploaded_conversation"),
        patient_data=data.get("patient_data", {}),
        examination_data=data.get("examination_data", {}),
        patient_model_name=data.get("models", {}).get("patient", ""),
        strategy_model_name=data.get("models", {}).get("strategy", ""),
        reply_model_name=data.get("models", {}).get("reply", ""),
        mdt_model_name=data.get("models", {}).get("mdt", ""),
        judge_model_name=data.get("models", {}).get("judge", ""),
        url=data.get("models", {}).get("url", None),
        max_turns=data.get("parameters", {}).get("max_turns", 15),
        human_in_the_loop=data.get("parameters", {}).get("human_in_the_loop", False),
        has_expert_knowledge=data.get("parameters", {}).get("has_expert_knowledge", False),
        is_emotional_patient=data.get("parameters", {}).get("is_emotional_patient", False),
        is_baseline=data.get("parameters", {}).get("is_baseline", False),
        do_eval_doctor=data.get("parameters", {}).get("do_eval_doctor", False),
        conversation_history=data.get("conversation_history", []),
    )

def build_label_mapping(name: int, file_name: str):
    """
    给当前评测样本生成一个稳定的随机双射：
    A/B/C/D/E  ->  DIRS 中的真实目录
    """
    case_key = f"{name}::{file_name}"

    if st.session_state.get("mapping_case_key") == case_key:
        return

    rng = random.Random(case_key)   # 稳定随机：同一个人 + 同一个病例，顺序固定
    shuffled_dirs = DIRS.copy()
    rng.shuffle(shuffled_dirs)

    label_to_dir = dict(zip(LABELS, shuffled_dirs))
    dir_to_label = {v: k for k, v in label_to_dir.items()}

    conversations_by_label = {}
    input_files_by_label = {}
    model_map = {}         # 保存时用：label -> 真实 DIR 字符串
    model_name_map = {}    # 备用：label -> get_name(...) 结果

    for label in LABELS:
        real_dir = label_to_dir[label]
        input_file = Path(SRC) / real_dir / file_name

        input_files_by_label[label] = input_file
        conversations_by_label[label] = load_conversation(input_file)
        model_map[label] = real_dir
        model_name_map[label] = get_name(str(input_file))

    st.session_state.mapping_case_key = case_key
    st.session_state.label_to_dir = label_to_dir
    st.session_state.dir_to_label = dir_to_label
    st.session_state.input_files_by_label = input_files_by_label
    st.session_state.conversations_by_label = conversations_by_label
    st.session_state.model_map = model_map
    st.session_state.model_name_map = model_name_map

SORTABLE_CSS = """
.sortable-component {
    padding: 0.2rem 0 0.8rem 0;
}

.sortable-container {
    background: transparent;
}

.sortable-item, .sortable-item:hover {
color: #111827 !important;
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    min-height: 78px;
    padding: 18px 22px;
    margin: 10px 0;
    border-radius: 14px;
    border: 1px solid #d0d7de;
    background: #ffffff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    display: flex;
    align-items: center;
}

.sortable-item {
    cursor: grab;
}
"""

def parse_rank_text(raw: str):
    raw = raw.upper().replace(" ", "").replace(">", "").replace(",", "")
    chars = [ch for ch in raw if ch in LABELS]
    if len(chars) != len(LABELS):
        return None
    if set(chars) != set(LABELS):
        return None
    return chars

def on_rank_text_change(dim_id: str):
    order_key = f"rank_order_{dim_id}"
    text_key = f"rank_text_{dim_id}"
    error_key = f"rank_error_{dim_id}"
    drag_version_key = f"rank_drag_version_{dim_id}"

    parsed = parse_rank_text(st.session_state[text_key])
    if parsed is None:
        st.session_state[error_key] = "请输入 5 个不重复字母，例如 BACED"
        return

    st.session_state[order_key] = parsed
    st.session_state[text_key] = "".join(parsed)
    st.session_state[error_key] = ""

    # 强制重建上面的拖拽组件
    if drag_version_key not in st.session_state:
        st.session_state[drag_version_key] = 0
    st.session_state[drag_version_key] += 1

def render_rank_editor(title_md: str, dim_id: str):
    order_key = f"rank_order_{dim_id}"
    text_key = f"rank_text_{dim_id}"
    error_key = f"rank_error_{dim_id}"
    drag_version_key = f"rank_drag_version_{dim_id}"

    if order_key not in st.session_state:
        st.session_state[order_key] = LABELS.copy()
    if text_key not in st.session_state:
        st.session_state[text_key] = "".join(st.session_state[order_key])
    if error_key not in st.session_state:
        st.session_state[error_key] = ""
    if drag_version_key not in st.session_state:
        st.session_state[drag_version_key] = 0

    drag_key = f"rank_drag_{dim_id}_{st.session_state[drag_version_key]}"

    st.markdown(title_md.strip())

    dragged_order = sort_items(
        st.session_state[order_key],
        key=drag_key,
        custom_style=SORTABLE_CSS,
    )

    if dragged_order != st.session_state[order_key]:
        st.session_state[order_key] = dragged_order
        st.session_state[text_key] = "".join(dragged_order)
        st.session_state[error_key] = ""

    st.text_input(
        "也可以直接输入排序（高 → 低）",
        key=text_key,
        placeholder="例如：BACED",
        help="按从高到低输入，例如 BACED",
        on_change=on_rank_text_change,
        args=(dim_id,),
    )

    if st.session_state[error_key]:
        st.warning(st.session_state[error_key])

    return st.session_state[order_key]

def render_turn(turn):
    speaker = turn["speaker"]
    msg = turn.get("message", {})
    response_text = msg.get("response", "")

    if speaker == "Doctor":
        with st.chat_message("user", avatar="👨‍⚕️"):
            st.markdown(
                f"<div class='doctor-green'><p class='turn-text'>{response_text}</p></div>",
                unsafe_allow_html=True,
            )
    elif speaker == "Patient":
        st.markdown(
            f"""
            <div class="chat-row patient">
                <div class="chat-avatar">🧑‍🦲</div>
                <div class="chat-bubble patient-white">
                    <p class="turn-text">{response_text}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.markdown("""
<style>
div[data-testid="stChatMessage"] {
    background-color: transparent !important;
}
.doctor-green {
  background: #d4edda;
  border: 1px solid #b7e1c1;
  padding: 0.75rem 0.9rem;
  border-radius: 0.75rem;
}
.patient-white {
  border: 1px solid;
  padding: 0.75rem 0.9rem;
  border-radius: 0.75rem;
}
.patient-red {
  border: 1px solid #f4c7c3;
  background: #fce8e6;
  padding: 0.75rem 0.9rem;
  border-radius: 0.75rem;
}
.turn-text {
  font-size: 20px;
  margin: 0;
}
.chat-row {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  margin: 0.5rem 0;
}
.chat-row.doctor {
  flex-direction: row-reverse;
}
.chat-avatar {
  font-size: 28px;
  line-height: 1;
  margin-top: 0.2rem;
  flex-shrink: 0;
}
.chat-bubble {
  max-width: 85%;
}
div[data-testid="stComponent"] iframe {
  min-height: 420px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("OncoAgents 交互界面")

if 'name' not in st.session_state:
    st.session_state.name = None

if st.button("点击此按钮开始！"):
    st.session_state.page_idx = 0
    # 怎么保证按一下 button，name += 1 呢？分布式访问也需要成立。
    # 查看 result/exp2/ 下的文件夹名称，range(1, 31) 里的哪个数字没有了，就用哪个数字
    found = [False for _ in range(31)]
    for dir in Path("result/exp2").iterdir():
        if dir.is_dir():
            try:
                num = int(dir.name)
                found[num] = True
            except ValueError:
                continue
    flag = True
    for i in range(1, 31):
        if not found[i]:
            st.session_state.name = i
            # 新建文件夹 result/exp2/{i}，以占位，防止重复
            (Path("result/exp2") / str(i)).mkdir(parents=True, exist_ok=True)
            flag = False
            break
    if st.session_state.name is None or flag:
        # 在 found 的基础上选一个文件夹里还没有文件的
        for i in range(1, 31):
            if found[i]:
                dir_path = Path("result/exp2") / str(i)
                if not any(dir_path.iterdir()):
                    st.session_state.name = i
                    break
    # 如果实在满了，就提示并退出
    is_exit = True
    for i in range(1, 31):
        dir_path = Path("result/exp2") / str(i)
        if any(dir_path.iterdir()):
            is_exit = False
            break
    if is_exit:
        st.error("当前评测系统已满，请稍后再试！")
        st.stop()
    print(st.session_state.name)
    files = sorted(Path(f"{SRC}/test_gpt-5-chat/cot").glob("*.json"))
    st.session_state.file_name = files[(st.session_state.name - 1) % 10].name

    build_label_mapping(st.session_state.name, st.session_state.file_name)
    st.session_state.initialized = True
    st.rerun()


if "initialized" in st.session_state and st.session_state.initialized:
    st.success("数据加载成功！")
    conversations_by_label = st.session_state.conversations_by_label
    page_labels = LABELS + ["评分页"]

    col_chat, col_data = st.columns([3, 2])

    with col_data:
        current_label = LABELS[min(st.session_state.page_idx, 4)]
        current_conv = conversations_by_label[current_label]
        st.markdown("### 数据面板")
        with st.expander("患者数据 (Patient Data)", expanded=True):
            st.write(render_user_profile(current_conv.patient_data, "Patient"))
        with st.expander("患者信息 (Personal Information)", expanded=True):
            st.write(render_personal_info(current_conv.patient_data))
        with st.expander("诊断数据 (Diagnosis Data)", expanded=True):
            st.write(render_diagnosis_data(current_conv.examination_data, with_exams=True))

    with col_chat:
        st.subheader("场景背景")
        st.markdown("""
假设你是一位肿瘤医生。某位患者已入院并完成必要检查。现在你需要与患者进行一次关键沟通：**告知癌症诊断结果，并解释推荐的治疗方案与下一步安排**。为保证沟通过程可重复、可评估，我们参考 SPIKES 坏消息告知框架（Baile 等提出的经典六步法）并进行简化。

SPIKES 是“告知重大坏消息”的一种策略。我们将 SPIKES 中的六个阶段化简为以下四个，你可以将对话组织为以下四个阶段（顺序建议，但可根据患者反应灵活调整）：
                
1.  P/I：Perception/Invitation，询问患者对当前情况的认知，这使医生能够确定患者对坏消息的了解程度、期望和接受准备情况。
2.  K：Knowledge，在患者愿意听的前提下，**按其需求与理解水平**传递关键信息。
3.  E：Emotions，当患者出现震惊、恐惧、愤怒、否认、哭泣等反应时，**优先处理情绪**，减少孤立感与无助感。
4.  S：Strategy，把信息收束成可执行计划，让患者知道“接下来做什么、何时做、为什么要做”。
        """.strip())

        st.subheader("你的任务")
        st.markdown("""
1.  告知患者他们的癌症诊断结果和治疗方案。
2.  你需要根据患者的个人背景画像，调整你的沟通方式（例如受教育水平、性格、经济条件等）。
3.  如果患者的情绪比较激动，你需要进行安抚。
4.  你最多只能和患者进行 15 轮对话（每轮指医生和患者各说一次）。
        """.strip())

        selected_page = st.segmented_control(
            "翻页",
            page_labels,
            default=page_labels[st.session_state.page_idx],
            selection_mode="single",
        )
        st.session_state.page_idx = page_labels.index(selected_page)

        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("⬅ 上一页", disabled=st.session_state.page_idx == 0):
                st.session_state.page_idx -= 1
                st.rerun()
        with nav2:
            st.markdown(
                f"<div style='text-align:center;'>第 {st.session_state.page_idx + 1} / {len(page_labels)} 页</div>",
                unsafe_allow_html=True,
            )
        with nav3:
            if st.button("下一页 ➡", disabled=st.session_state.page_idx == len(page_labels) - 1):
                st.session_state.page_idx += 1
                st.rerun()

        st.divider()

        # 前五页：显示单个模型对话
        if st.session_state.page_idx < 5:
            idx = st.session_state.page_idx
            label = LABELS[idx]
            history = conversations_by_label[label].conversation_history

            st.subheader(f"医生智能体 {label} 与患者的对话")

            for turn in history[:-1]:
                speaker = turn["speaker"]

                if speaker == "Patient":
                    with st.chat_message("user", avatar="🧑‍🦲"):
                        msg = turn.get("message", {})
                        response_text = msg.get("response", "")
                        st.markdown(
                            f"<div class='patient-white'><p class='turn-text'>{response_text}</p></div>",
                            unsafe_allow_html=True,
                        )

                elif speaker == "Doctor":
                    msg = turn.get("message", {})
                    response_text = msg.get("response", "")
                    st.markdown(
                        f'''
                        <div class="chat-row doctor">
                            <div class="chat-avatar">
                            医生{label}👨‍⚕️</div>
                            <div class="chat-bubble doctor-green">
                                <p class="turn-text">{response_text}</p>
                            </div>
                        </div>
                        ''',
                        unsafe_allow_html=True,
                    )

            st.divider()

            if history and history[-1]["speaker"] == "Patient":
                last_message = history[-1]["message"]
                if (
                    last_message.get("pas_score", 0) < 10
                    or last_message.get("ess_score", 0) >= 90
                ):
                    st.error("患者拒绝了医生的建议。")
                elif last_message.get("pas_score", 0) >= 90:
                    st.success("患者接受了医生的建议。")
                else:
                    st.success("医患沟通已结束。")

        # 最后一页：三个维度分别排序
        else:
            st.subheader("评分维度与规则")

            rank_dim_1 = render_rank_editor(DIMENSIONS[0], "1")
            rank_dim_2 = render_rank_editor(DIMENSIONS[1], "2")
            rank_dim_3 = render_rank_editor(DIMENSIONS[2], "3")

            if st.button("保存评分结果"):
                output_dir = Path("../results/experiment_2") / str(st.session_state.name)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / f"{st.session_state.file_name.split('.')[0]}.txt"

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("维度 1（诊疗过程信息可理解性）:\n")
                    for i, label in enumerate(rank_dim_1, start=1):
                        f.write(f"{i}. {label}: {st.session_state.model_map[label]}\n")

                    f.write("\n维度 2（诊疗过程问答合理性）:\n")
                    for i, label in enumerate(rank_dim_2, start=1):
                        f.write(f"{i}. {label}: {st.session_state.model_map[label]}\n")

                    f.write("\n维度 3（诊疗过程人文关怀度）:\n")
                    for i, label in enumerate(rank_dim_3, start=1):
                        f.write(f"{i}. {label}: {st.session_state.model_map[label]}\n")

                st.success("评分结果已保存！")