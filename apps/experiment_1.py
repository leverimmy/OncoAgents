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
DATA_DIR = "./data/pretest"

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

def generate_doctor_step(conversation: Conversation):
    """Runs one step of doctor generation."""
    try:
        if conversation.is_baseline:
             doctor_reply = conversation._run_baseline_reply_model()
             doctor_ret = {
                 "stage": "baseline",
                 "analysis": "baseline",
                 "strategy": "baseline",
                 "response": doctor_reply,
                 "explanation": [],
             }
        else:
            stage, analysis, strategy, keywords = conversation._run_strategy_model()
            doctor_reply, explanation = conversation._run_reply_model(
                stage, analysis, strategy, keywords
            )
            doctor_ret = {
                "stage": stage,
                "analysis": analysis,
                "strategy": strategy,
                "keywords": keywords,
                "response": doctor_reply,
                "explanation": explanation,
            }

        term = {
            "speaker": "Doctor",
            "message": doctor_ret,
        }
        return term
    except Exception as e:
        st.error(f"Error in doctor step: {e}")
        raise e

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
    # uploaded_file = st.file_uploader("上传对话 JSON", type=["json"])
    # if uploaded_file:
    #     try:
    #         st.session_state.conversation_data = json.load(uploaded_file)
    #         st.success("已加载 JSON.")
    #     except Exception as e:
    #         st.error(f"无效的 JSON: {e}")

    # Settings
    st.markdown("---")
    st.subheader("模型设置")

    if "conversation_data" in st.session_state and st.session_state.conversation_data.get("models"):
        models = st.session_state.conversation_data["models"]
        patient_model_name = st.text_input("患者模型名称", value=models["patient"], disabled=True)
        strategy_model_name = st.text_input("策略模型名称", value=models["strategy"], disabled=True)
        reply_model_name = st.text_input("回复模型名称", value=models["reply"], disabled=True)
        mdt_model_name = st.text_input("MDT 模型名称", value=models["mdt"], disabled=True)
        judge_model_name = st.text_input("Judge 模型名称", value=models["judge"], disabled=True)
        url = st.text_input("URL (如果需要)", value=models.get("url", "http://localhost:8000/v1/"), disabled=True)
    else:
        patient_model_name = st.text_input("患者模型名称", value="o3")
        strategy_model_name = st.text_input("策略模型名称", value="Qwen/Qwen3-8B")
        reply_model_name = st.text_input("回复模型名称", value="Qwen/Qwen3-8B")
        mdt_model_name = st.text_input("MDT 模型名称", value="Qwen/Qwen3-8B")
        judge_model_name = st.text_input("Judge 模型名称", value="o3")
        url = st.text_input("URL (如果需要)", value="http://localhost:8000/v1/")

    st.markdown("---")
    st.subheader("参数设置")

    if "conversation_data" in st.session_state and st.session_state.conversation_data.get("parameters"):
        params = st.session_state.conversation_data["parameters"]
        max_turns = st.number_input("最长对话轮数", value=params.get("max_turns", 15), min_value=1, disabled=True)
        human_in_the_loop = st.checkbox("人类作为医生进行对话", value=params.get("human_in_the_loop", False), disabled=True, help="人类对话，用文本输入框的形式和患者智能体进行交流")
        has_expert_knowledge = st.checkbox("具备专家知识？", value=params.get("has_expert_knowledge", True), disabled=True)
        debug_mode = st.checkbox("单步调试", value=False, disabled=True)
        is_emotional_patient = st.checkbox("使用具有情感的患者智能体", value=params.get("is_emotional_patient", True), disabled=True)
        is_baseline = st.checkbox("Baseline 模式", value=params.get("is_baseline", False), disabled=True)
        do_eval_patient = st.checkbox("进行患者评估", value=params.get("do_eval_patient", False), disabled=True)
        do_eval_doctor = st.checkbox("进行医生评估", value=params.get("do_eval_doctor", False), disabled=True)
    else:
        is_emotional_patient = st.checkbox("是否使用具有情感的患者智能体", value=True)
        human_in_the_loop = st.checkbox("是否人类作为医生进行对话", value=True, help="人类对话，用文本输入框的形式和患者智能体进行交流")
        is_baseline = st.checkbox("是否为 Baseline 模式", value=False)
        has_expert_knowledge = st.checkbox("是否具备专家知识？", value=True)
        debug_mode = st.checkbox("单步调试", value=False)
        max_turns = st.number_input("最长对话轮数", value=15, min_value=1)
        # do_eval_patient = st.checkbox("是否进行患者评估", value=False)
        # do_eval_doctor = st.checkbox("是否进行医生评估", value=False)
        do_eval_patient = False
        do_eval_doctor = False
    
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
                    "file_name": data.get("file_name", "uploaded_conversation"),
                    "patient_data": patient_data,
                    "examination_data": examination_data,
                }
            st.session_state.conversation = Conversation(
                file_name=data.get("file_name", "uploaded_conversation"),
                patient_data=data.get("patient_data", {}),
                examination_data=data.get("examination_data", {}),
                patient_model_name=patient_model_name,
                strategy_model_name=strategy_model_name,
                reply_model_name=reply_model_name,
                mdt_model_name=mdt_model_name,
                judge_model_name=judge_model_name,
                url=url,
                max_turns=max_turns,
                human_in_the_loop=human_in_the_loop,
                has_expert_knowledge=has_expert_knowledge,
                is_emotional_patient=is_emotional_patient,
                is_baseline=is_baseline,
                do_eval_patient=do_eval_patient,
                do_eval_doctor=do_eval_doctor,
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
        for i, turn in enumerate(history):
            speaker = turn["speaker"]
            
            if speaker == "Doctor":
                # Doctor Message (Right)
                d_c1, d_c2 = st.columns([1, 4])
                with d_c2:
                    with st.chat_message("assistant", avatar="👨‍⚕️"):
                        msg = turn.get("message", {})
                        response_text = msg.get("response", "")
                        
                        st.markdown(f"<div style='font-size:20px;'>{response_text}</div>", unsafe_allow_html=True)
                        
                        # Expandable details
                        with st.expander("内部状态 (策略 & 解释)", expanded=False):
                            st.write("- **阶段:**", msg.get("stage", "N/A"))
                            st.write("- **分析:**", msg.get("analysis", "N/A"))
                            st.write("- **策略:**", msg.get("strategy", "N/A"))
                            st.write("- **关键词:**", msg.get("keywords", []))
                            
                            if msg.get("explanation"):
                                st.markdown("##### 解释结果:")
                                explanation = msg.get("explanation")
                                if isinstance(explanation, list):
                                    for item in explanation:
                                        q = item.get("query", "")
                                        e = item.get("explanation", "")
                                        st.markdown(f"- **Query**: {q}")
                                        st.markdown(f"> {e}")
                                else:
                                    st.write(explanation)

                        # # Logic for "Edit & Replay"
                        # if st.button("编辑并重播", key=f"edit_btn_{i}"):
                        #     st.session_state.editing_index = i
                        #     st.rerun()

            elif speaker == "Patient":
                # Patient Message (Left)
                p_c1, p_c2 = st.columns([4, 1])
                with p_c1:
                    with st.chat_message("user", avatar="👤"):
                        msg = turn.get("message", {})
                        response_text = msg.get("response", "")
                        st.markdown(f"<div style='font-size:20px;'>{response_text}</div>", unsafe_allow_html=True)
                        
                        # Internal State (Patient)
                        with st.expander("内部状态 (CoT & 评估)", expanded=False):
                            st.markdown("## 情感 CoT")
                            st.write(f"- **分析**: {msg.get('emotion_analysis', 'N/A')}")
                            st.write(f"- **状态**: {msg.get('emotion_state', 'N/A')}")
                            st.write(f"- **信任分析**: {msg.get('trust_analysis', 'N/A')}")
                            st.write(f"- **信任状态**: {msg.get('trust_state', 'N/A')}")

                            st.markdown("## 理性 CoT")
                            st.write(f"- **输入分析**: {msg.get('input_analysis', 'N/A')}")
                            st.write(f"- **知识**: {msg.get('knowledge', 'N/A')}")
                            st.write(f"- **信息差距**: {msg.get('information_gap', 'N/A')}")

                        # Scores
                        with st.expander("## 评分", expanded=False):
                            st.write(f"- **CCS**: {msg.get('ccs_score', 'N/A')}")
                            st.write(f"- **ESS**: {msg.get('ess_score', 'N/A')}")
                            st.write(f"- **PAS 分析**: {msg.get('pas_analysis', 'N/A')}")
                            st.write(f"- **PAS**: {msg.get('pas_score', 'N/A')}")
                            st.write(f"- **决策**: {msg.get('decision', 'N/A')}")

        # --- Editing Area (if active) --- #
        if "editing_index" in st.session_state:
            idx = st.session_state.editing_index
            if 0 <= idx < len(history):
                turn_to_edit = history[idx]
                current_text = turn_to_edit["message"].get("response", "")
                
                st.info("正在编辑医生消息。这将移除后续的所有回复并重新生成患者的回复。")
                new_text = st.text_area("医生消息", value=current_text)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("确认并重播"):
                        conversation.conversation_history[idx]["message"]["response"] = new_text
                        conversation.conversation_history = conversation.conversation_history[:idx+1]
                        st.session_state.run_patient_next = True
                        del st.session_state.editing_index
                        st.rerun()
                with col_b:
                    if st.button("取消"):
                        del st.session_state.editing_index
                        st.rerun()
            else:
                del st.session_state.editing_index

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
            if last_message.get("decision") == "reject" or last_message.get("pas_score", 0) < 10 or last_message.get("ess_score", 0) >= 90:
                st.warning("患者拒绝了医生的建议。")
                conversation.negotiation_result = "reject"
                conversation.negotiation_completed = True
            if last_message.get("decision") == "accept" or last_message.get("pas_score", 0) >= 90:
                st.success("患者接受了医生的建议。")
                conversation.negotiation_result = "accept"
                conversation.negotiation_completed = True

        if max_turns_reached or conversation.negotiation_completed:
            st.warning("交互结束。")
            if st.button("对当前医生进行评价"):
                result = None
                with st.spinner("正在评估医生..."):
                    result = conversation._run_judge_doctor_model()
                st.markdown("### 医生评估结果")
                st.json(result)
            if st.button("保存当前对话"):
                save_dir = st.text_input("输入保存文件名", value=f"{conversation.file_name}_edited")
                try:
                    result = conversation.save_conversation(save_dir)
                    st.markdown(result)
                    st.success(f"已保存到 {save_dir}")
                except Exception as e:
                    st.error(f"保存失败: {e}")

        elif next_speaker == "Doctor":
            st.subheader("下一轮: 医生")
            
            if human_in_the_loop:
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
            else:
                if debug_mode:
                    if st.button("生成 AI 医生回复"):
                        with st.spinner("医生正在思考..."):
                            try:
                                turn = generate_doctor_step(conversation)
                                conversation.conversation_history.append(turn)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error generating doctor response: {e}")
                else:
                    # Automatic generation (No button) if not debug
                    with st.spinner("医生正在思考 (自动)..."):
                        try:
                            turn = generate_doctor_step(conversation)
                            conversation.conversation_history.append(turn)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error generating doctor response: {e}")
                            
        elif next_speaker == "Patient":
            st.subheader("下一轮: 患者")
            if debug_mode:
                if st.button("生成患者回复"):
                    st.session_state.run_patient_next = True
                    st.rerun()
            else:
                 # Should have been handled by auto-run block above,
                 # but if we just arrived here from Doctor turn repaint:
                 st.session_state.run_patient_next = True
                 st.rerun()
