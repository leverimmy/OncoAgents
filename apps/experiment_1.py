import json
import os
import sys
from pathlib import Path

import streamlit as st

# Add current directory to path so we can import src
sys.path.append(os.path.abspath("../"))

from src.conversation import Conversation
from src.utils import render_diagnosis_data, render_personal_info, render_user_profile

# Page Config
st.set_page_config(layout="wide", page_title="OncoAgents 对话")

# --- Constants & Helpers --- #
DATA_DIR = "../data/pretest"

MAP = [
    "char95_diag313.json",
    "char120_diag73.json",
    "char161_diag98.json",
    "char215_diag320.json",
    "char244_diag318.json",
    "char256_diag581.json",
    "char259_diag416.json",
    "char428_diag587.json",
]

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
        conversation.patient_scores.append({
            "ccs_score": patient_ret.get("ccs_score", 0),
            "ess_score": patient_ret.get("ess_score", 0),
            "pas_score": patient_ret.get("pas_score", 0),
        })
        
        return term
    except Exception as e:
        st.error(f"Error in patient step: {e}")
        raise e

# --- Main App Logic --- #

st.title("OncoAgents 交互界面")

# Sidebar
with st.sidebar:
    st.header("配置")

    selected = st.number_input("选择对话 (1-8)", min_value=1, max_value=8, value=1)
    input_file = Path(DATA_DIR) / MAP[selected - 1]
    st.session_state.conversation_data = json.load(open(input_file, encoding="utf-8"))
    st.success(f"已加载对话文件: {input_file.name}")

    # Settings
    st.markdown("---")
    st.subheader("模型设置")

    patient_model_name = st.text_input("患者模型名称", value="o3", disabled=True)

    st.markdown("---")
    st.subheader("参数设置")

    # is_emotional_patient = st.checkbox("是否使用具有情感的患者智能体", value=True)
    # TODO: 怎么分配这个？
    is_emotional_patient = True
    max_turns = st.number_input("最长对话轮数", value=15, min_value=1)
    
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
                    "file_name": input_file.name,
                    "patient_data": patient_data,
                    "examination_data": examination_data,
                }
            st.session_state.conversation = Conversation(
                file_name=data.get("file_name", "uploaded_conversation"),
                patient_data=data.get("patient_data", {}),
                examination_data=data.get("examination_data", {}),
                patient_model_name=patient_model_name,
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
    
    st.subheader(f"对话 (文件: {conversation.file_name})")

    # Layout: Chat (Left) + Data (Right)
    col_chat, col_data = st.columns([2, 1])

    # Right Column: Data
    with col_data:
        st.markdown("### 数据面板")
        with st.container(height=250):
            with st.expander("患者数据 (Patient Data)", expanded=True):
                st.write(render_user_profile(conversation.patient_data, "Patient"))
        with st.container(height=650):
            with st.expander("患者信息 (Personal Information)", expanded=True):
                st.write(render_personal_info(conversation.patient_data))
            with st.expander("诊断数据 (Diagnosis Data)", expanded=True):
                st.write(render_diagnosis_data(conversation.examination_data, with_exams=True))

    # Left Column: Chat & Controls
    with col_chat:
        history = conversation.conversation_history
        
        # Display History
        for turn in history:
            speaker = turn["speaker"]
            
            if speaker == "Doctor":
                # Doctor Message (Right)
                d_c1, d_c2 = st.columns([1, 4])
                with d_c2:
                    with st.chat_message("assistant", avatar="👨‍⚕️"):
                        msg = turn.get("message", {})
                        response_text = msg.get("response", "")
                        st.markdown(f"<div style='font-size:20px;'>{response_text}</div>", unsafe_allow_html=True)

            elif speaker == "Patient":
                # Patient Message (Left)
                p_c1, p_c2 = st.columns([4, 1])
                with p_c1:
                    with st.chat_message("user", avatar="👤"):
                        msg = turn.get("message", {})
                        response_text = msg.get("response", "")
                        st.markdown(f"<div style='font-size:20px;'>{response_text}</div>", unsafe_allow_html=True)

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
            if last_message.get("pas_score", 0) < 10 or last_message.get("ess_score", 0) >= 90:
                st.error("患者拒绝了医生的建议。")
                conversation.negotiation_result = "reject"
                conversation.negotiation_completed = True
            if last_message.get("pas_score", 0) >= 90:
                st.success("患者接受了医生的建议。")
                conversation.negotiation_result = "accept"
                conversation.negotiation_completed = True

        if max_turns_reached or conversation.negotiation_completed:
            st.warning("交互结束。")
            save_dir = st.text_input("输入你的唯一 ID", value="xyz")
            save_dir = Path("results") / save_dir
            if st.button("保存当前对话"):
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
                            "explanation": []
                        }
                    }
                    conversation.conversation_history.append(turn)
                    st.session_state.run_patient_next = True 
                    st.rerun()
        elif next_speaker == "Patient":
            st.subheader("下一轮: 患者")
            st.session_state.run_patient_next = True
            st.rerun()
