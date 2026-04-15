import json
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

# Add current directory to path so we can import src
sys.path.append(os.path.abspath("../"))

from src.conversation import Conversation
from src.utils import (
    render_diagnosis_data,
    render_personal_info,
    render_user_profile,
)

# Page Config
st.set_page_config(layout="wide", page_title="OncoAgents 对话")

# --- Constants & Helpers --- #
DATA_DIR = "../data/full/experiment"

DOCTORS = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]

random.seed(42)

MAPS = {
    d: sorted([
        f"{f.split(".json")[0]}-{idx}" for f in os.listdir(os.path.join(DATA_DIR, d)) if f.endswith(".json") for idx in range(2)
    ],) for d in DOCTORS
}

for key in MAPS:
    random.shuffle(MAPS[key])

for key in MAPS:
    MAPS[key] = sorted(MAPS[key])
    for idx, _ in enumerate(MAPS[key]):
        if idx % 2 == 0:
            if random.random() < 0.5:
                t = MAPS[key][idx]
                MAPS[key][idx] = MAPS[key][idx + 1]
                MAPS[key][idx + 1] = t

# logger.info(MAPS)

def generate_patient_step(conversation: Conversation):
    """Runs one step of patient generation."""
    try:
        patient_ret = conversation.patient_agent.respond(
            dialogue_history=conversation._get_dialogue_history()
        )

        term = {
            "speaker": "Patient",
            "message": patient_ret,
        }

        # Update scores like in run_conversation
        conversation.patient_scores.append(
            {
                "ccs_score": patient_ret.get("ccs_score", 0),
                "ess_score": patient_ret.get("ess_score", 0),
                "pas_score": patient_ret.get("pas_score", 0),
            }
        )

        return term
    except Exception as e:
        st.error(f"Error in patient step: {e}")
        raise e

@dataclass(frozen=True)
class Metric:
    key: str
    title: str
    anchors: dict  # {1: "...", 3: "...", 5: "..."}

METRICS = [
    Metric(
        key="overall",
        title="总体拟真性",
        anchors={
            1: "一眼看穿为AI，反应不合常理，难以当真实患者。",
            3: "几句话之后感觉是AI，可以部分场景模拟真实患者。",
            5: "整体高度像真实患者，可用于临床沟通训练。",
        },
    ),
    Metric(
        key="emotion",
        title="情绪反应合理性",
        anchors={
            1: "情绪与坏消息不匹配（过冷/过戏剧化）或无触发点地跳变。",
            3: "情绪方向大体对，但强度/节奏不够自然，偶有跳变。",
            5: "情绪与关键节点强相关，变化连贯且符合画像。",
        },
    ),
    Metric(
        key="cognition",
        title="认知过程合理性",
        anchors={
            1: "理解不真实（突然全懂/突然失忆），几乎无真实困惑与澄清过程。",
            3: "有理解/困惑，但深浅不稳，偶有不自然的理解跳跃或遗漏。",
            5: "困惑—追问/复述确认—澄清—修正 连贯，符合教育水平差异。",
        },
    ),
    Metric(
        key="persona",
        title="画像一致性",
        anchors={
            1: "教育/经济/性格/沟通风格不体现或频繁自相矛盾。",
            3: "画像可见但不稳定，关键处偶尔跑偏。",
            5: "画像稳定贯穿语言风格与关注点（费用敏感、耐心、提问方式等）。",
        },
    ),
    Metric(
        key="interaction",
        title="互动自然度",
        anchors={
            1: "像问答系统：机械应答/长篇独白/不接话，缺少真实互动。",
            3: "能互动但节奏偏规则化，偶有重复、突兀转话题或“没听见”。",
            5: "互动节奏自然：追问、确认、沉默等自然出现，围绕核心逐步推进。",
        },
    ),
]

# --- Main App Logic --- #

st.title("OncoAgents 交互界面")

# Sidebar
with st.sidebar:
    # Settings
    st.header("配置")

    selected_doctor = st.selectbox("选择医生身份", options=MAPS.keys())
    selected_patient = st.number_input("选择患者编号", min_value=1, max_value=8, value=1)
    target_file = MAPS[selected_doctor][selected_patient - 1]
    file_name, digit = target_file.rsplit("-", 1)

    input_file = Path(DATA_DIR) / selected_doctor / f"{file_name}.json"
    st.session_state.conversation_data = json.load(open(input_file, encoding="utf-8"))
    st.success(f"已加载对话文件: {input_file.name}")

    st.markdown("---")
    st.subheader("参数设置")

    is_emotional_patient = True if digit in ["1"] else False
    _ = st.checkbox("是否为具有情绪感知的患者智能体", value=is_emotional_patient, disabled=True)
    max_turns = st.number_input("最长对话轮数", value=8, min_value=1)

    if st.button("初始化 / 重置会话"):
        if "conversation_data" in st.session_state:
            data = st.session_state.conversation_data
            if "patient_data" not in data or "examination_data" not in data:
                patient_data = {
                    "personal_info": data["personal_info"],
                    "symptom": data["symptom"],
                    "reiterated_symptom": data["reiterated_symptom"],
                }
                examination_data = {
                    "symptom": data["symptom"],
                    "auxiliary_examination": data["auxiliary_examination"],
                    "diagnosis": data["diagnosis"],
                    "treatment": data["treatment"],
                }
                data = {
                    "file_name": f"{input_file.stem}-{digit}.json",
                    "patient_data": patient_data,
                    "examination_data": examination_data,
                }
            st.session_state.conversation = Conversation(
                file_name=data.get("file_name", "uploaded_conversation"),
                patient_data=data.get("patient_data", {}),
                examination_data=data.get("examination_data", {}),
                patient_model_name="o3",
                strategy_model_name="",
                reply_model_name="",
                mdt_model_name="",
                judge_model_name="",
                url=None,
                max_turns=max_turns,
                human_in_the_loop=True,
                has_expert_knowledge=False,
                is_emotional_patient=is_emotional_patient,
                is_baseline=False,
                do_eval_patient=False,
                do_eval_doctor=False,
            )
            st.session_state.initialized = True
            st.success("会话已初始化.")
            st.rerun()

# --- Conversation View --- #

if "initialized" in st.session_state and st.session_state.initialized:
    conversation = st.session_state.conversation

    # st.subheader(f"对话 (文件: {conversation.file_name})")

    # Layout: Chat (Left) + Data (Right)
    col_chat, col_data = st.columns([2, 1])

    # Right Column: Data
    with col_data:
        st.markdown("### 数据面板")
        # with st.container(height=250):
        with st.expander("患者数据 (Patient Data)", expanded=True):
            st.write(render_user_profile(conversation.patient_data, "Patient"))
        # with st.container(height=650):
        with st.expander("患者信息 (Personal Information)", expanded=True):
            st.write(render_personal_info(conversation.patient_data))
        with st.expander("诊断数据 (Diagnosis Data)", expanded=True):
            st.write(
                render_diagnosis_data(
                    conversation.examination_data, with_exams=True
                )
            )

    # Left Column: Chat & Controls
    with col_chat:
        st.subheader("场景背景")
        st.markdown("""
假设你是一位肿瘤医生。某位患者已入院并完成必要检查。现在你需要与患者进行一次关键沟通：**告知癌症诊断结果，并解释推荐的治疗方案与下一步安排**。为保证沟通过程可重复、可评估，我们参考 SPIKES 坏消息告知框架（Baile 等提出的经典六步法）并进行简化。

SPIKES 是“告知重大坏消息”的一种策略。我们将 SPIKES 中的六个阶段化简为以下四个，你可以将对话组织为以下四个阶段（顺序建议，但可根据患者反应灵活调整）：
                
1.  P/I：Perception/Invitation，询问患者对当前情况的认知，这使医生能够确定患者对坏消息的了解程度、期望和接受准备情况。
2.  K：Knowledge，在患者愿意听的前提下，**按其需求与理解水平**传递关键信息。
3.  E：Emotions，当患者出现震惊、恐惧、愤怒、否认、哭泣等反应时，**优先处理情绪**，减少孤立感与无助感。
4.  S：Strategy，把信息收束成可执行计划，让患者知道“接下来做什么、何时做、为什么要做”。
                
你可以以“您好！请问您对您的病情有所了解吗？需要我现在告诉您诊断结果和治疗方案吗？”作为开头。
                    """.strip())

        st.subheader("你的任务")
        st.markdown("""
1.  告知患者他们的癌症诊断结果和治疗方案。
2.  你需要根据患者的个人背景画像，调整你的沟通方式（例如受教育水平、性格、经济条件等）。
3.  如果患者的情绪比较激动，你需要进行安抚。
4.  你最多只能和患者进行 8 轮对话（每轮指医生和患者各说一次）。
在对话完成之后，你需要给患者智能体的表现进行打分。
                    """.strip())
        history = conversation.conversation_history

        # Display History
        for i, turn in enumerate(history):
            speaker = turn["speaker"]

            if speaker == "Doctor":
                # Doctor Message (Right)
                d_c1, d_c2 = st.columns([1, 4])
                with d_c2:
                    with st.chat_message("assistant", avatar="👨‍⚕️"):
                        msg = turn.get("message", {})
                        response_text = msg.get("response", "")
                        st.markdown(
                            f"<div style='font-size:20px;'>{response_text}</div>",
                            unsafe_allow_html=True,
                        )

            elif speaker == "Patient":
                # Patient Message (Left)
                p_c1, p_c2 = st.columns([4, 1])
                with p_c1:
                    with st.chat_message("user", avatar="👤"):
                        msg = turn.get("message", {})
                        response_text = msg.get("response", "")
                        st.markdown(
                            f"<div style='font-size:20px;'>第{i // 2 + 1}轮：{response_text}</div>",
                            unsafe_allow_html=True,
                        )

        st.divider()

        # --- Action Area --- #

        # Determine who is next
        next_speaker = "Doctor"
        if history:
            last_turn = history[-1]
            if last_turn["speaker"] == "Doctor":
                next_speaker = "Patient"
        # Check max turns
        current_turns = len(history) // 2
        # Note: conversation_history stores individual turns, so len = 2 * rounds approx
        # "max_turns" usually refers to rounds (pairs).

        # In conversation.py logic: turn_count = len(self.conversation_history) // 2
        # while turn_count < self.max_turns:

        max_turns_reached = (len(history) // 2) >= max_turns
        if max_turns_reached:
            conversation.negotiation_result = "max_turns_reached"
            conversation.negotiation_completed = False

        # Auto-run Patient if triggered
        if st.session_state.get("run_patient_next") and not max_turns_reached:
            with st.spinner("患者正在回复..."):
                try:
                    turn = generate_patient_step(conversation)
                    conversation.conversation_history.append(turn)
                except Exception as e:
                    st.error(f"Error generating patient response: {e}")

            st.session_state.run_patient_next = False
            st.rerun()

        # Controls
        if history and history[-1]["speaker"] == "Patient":
            last_message = history[-1]["message"]
            if (
                last_message.get("pas_score", 0) < 10
                or last_message.get("ess_score", 0) >= 90
            ):
                st.error("患者拒绝了医生的建议。")
                conversation.negotiation_result = "reject"
                conversation.negotiation_completed = True
            if last_message.get("pas_score", 0) >= 90:
                st.success("患者接受了医生的建议。")
                conversation.negotiation_result = "accept"
                conversation.negotiation_completed = True

        if max_turns_reached or conversation.negotiation_completed:
            st.warning("交互结束。")
            save_dir = Path("results") / selected_doctor

            st.subheader("评分标准")
            for m in METRICS:
                st.markdown(f"#### {m.title}")
                st.markdown(f"**1 分：** {m.anchors[1]}")
                st.markdown(f"**3 分：** {m.anchors[3]}")
                st.markdown(f"**5 分：** {m.anchors[5]}")
                st.caption("2 分表示介于 1–3；4 分表示介于 3–5。")
                if "scores" not in st.session_state:
                    st.session_state.scores = {m.key: 3 for m in METRICS}  # 默认 3 分
                
                st.session_state.scores[m.key] = st.radio(
                    label=m.title,
                    options=[1, 2, 3, 4, 5],
                    index=4 if is_emotional_patient else 0,
                    horizontal=True
                )
            
            st.subheader("反馈")
            feedback_1 = st.text_input("主观题：你觉得这个患者智能体最拟真的地方在哪里？")
            feedback_2 = st.text_input("主观题：你觉得这个患者智能体最不拟真的地方在哪里？")

            conversation.judge_patient_scores = {
                m.key: st.session_state.scores[m.key] for m in METRICS
            }
            conversation.judge_patient_scores["feedback_1"] = feedback_1
            conversation.judge_patient_scores["feedback_2"] = feedback_2

            st.divider()

            if st.button("保存当前打分"):
                try:
                    result = conversation.save_conversation(save_dir)
                    st.success(f"已保存到 {save_dir}")
                except Exception as e:
                    st.error(f"保存失败: {e}")

        elif next_speaker == "Doctor":
            st.subheader("下一轮: 医生")

            user_input = st.text_area("输入医生的回复:", key="new_doc_input")
            if st.button("发送 (人类)"):
                if user_input.strip():
                    turn = {
                        "speaker": "Doctor",
                        "message": {
                            "stage": "human_input",
                            "analysis": "human_input",
                            "strategy": "human_input",
                            "response": user_input,
                            "explanation": [],
                        },
                    }
                    conversation.conversation_history.append(turn)
                    st.session_state.run_patient_next = True
                    st.rerun()
        elif next_speaker == "Patient":
            st.subheader("下一轮: 患者")
            st.session_state.run_patient_next = True
            st.rerun()
