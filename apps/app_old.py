import asyncio
import copy
import json
import os
import sys

import streamlit as st

# Add current directory to path so we can import src
sys.path.append(os.path.abspath("."))

from src.conversation import Conversation
from src.json_schema.mdt_json_schema import MDT_JSON_SCHEMA
from src.utils import STAGE2NAME

# Page Config
st.set_page_config(layout="wide", page_title="OncoAgents 对话")

# --- Constants & Helpers --- #
DATA_DIR = "data/"

def load_data(patient_id, diagnosis_id):
    """Loads and merges patient and diagnosis data."""
    try:
        full_data = {}
        bg_path = os.path.join(DATA_DIR, "background", f"{patient_id}.json")
        diag_path = os.path.join(DATA_DIR, "diagnosis", f"{diagnosis_id}.json")
        
        if not os.path.exists(bg_path):
             st.error(f"未找到背景文件: {bg_path}")
             return None, None, None, None
        if not os.path.exists(diag_path):
             st.error(f"未找到诊断文件: {diag_path}")
             return None, None, None, None

        with open(bg_path, encoding="utf-8") as f:
            full_data = json.load(f)
        with open(diag_path, encoding="utf-8") as f:
            diagnosis_data = json.load(f)
            for k, v in diagnosis_data.items():
                if k in full_data and isinstance(full_data[k], dict):
                    full_data[k].update(v)
                else:
                    full_data[k] = v
        
        patient_data = {
            "personal_info": full_data["personal_info"],
            "symptom": full_data["symptom"],
        }
        examination_data = {
            "physical_examination": full_data.get("physical_examination", ""),
            "auxiliary_examination": full_data.get("auxiliary_examination", ""),
        }
        return patient_data, diagnosis_data, examination_data, full_data
    except Exception as e:
        st.error(f"加载数据出错: {e}")
        return None, None, None, None

def generate_doctor_step(conversation):
    """Runs one step of doctor generation."""
    # This mirrors logic in Conversation.run_conversation loop
    
    # 1. ToM
    if conversation.has_expert_knowledge:
        # If first turn logic needed?
        if len(conversation.conversation_history) == 0:
            tom_reasoning = {
                "patient_analysis": "null",
                "stage": STAGE2NAME[0],
            }
        else:
             tom_reasoning = conversation._run_tom_reasoning()
    else:
        tom_reasoning = {
            "patient_analysis": "human_input",
            "stage": "human_input",
        }
    
    # 2. Strategy
    stage = tom_reasoning.get("stage", "human_input")
    patient_analysis = tom_reasoning.get("patient_analysis", "human_input")

    analysis, strategy, is_explanation_needed = conversation._run_strategy_model(
        stage=stage,
        analysis=patient_analysis,
    )

    # 3. Reply
    doctor_reply, explanation = conversation._run_reply_model(
        analysis, strategy, is_explanation_needed
    )
    
    doctor_ret = {
        "analysis": analysis,
        "strategy": strategy,
        "response": doctor_reply,
        "explanation": explanation,
    }
    
    term = {
        "speaker": "Doctor",
        "tom_reasoning": tom_reasoning,
        "message": doctor_ret,
    }
    return term

def generate_patient_step(conversation):
    """Runs one step of patient generation."""
    patient_ret = conversation.patient_agent.respond(
        dialogue_history=conversation._get_dialogue_history()
    )
    
    term = {
        "speaker": "Patient",
        "message": patient_ret,
    }
    return term

# --- Main App Logic --- #

st.title("OncoAgents 交互界面")

# Sidebar
with st.sidebar:
    st.header("配置")
    mode = st.radio("初始化模式", ["通过 ID", "通过 JSON 文件"])
    
    patient_id = 1
    diagnosis_id = 1
    loaded_history = []
    
    if mode == "通过 ID":
        patient_id = st.number_input("患者 ID (特征)", value=1, min_value=1)
        diagnosis_id = st.number_input("诊断 ID", value=1, min_value=1)
    else:
        uploaded_file = st.file_uploader("上传对话 JSON", type=["json"])
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                patient_id = data.get("patient_id", 1)
                diagnosis_id = data.get("diagnosis_id", 1)
                loaded_history = data.get("conversation_history", [])
                st.success(f"已加载: 患者 {patient_id}, 诊断 {diagnosis_id}, {len(loaded_history)} 轮对话.")
            except Exception as e:
                st.error(f"无效的 JSON: {e}")

    # Settings
    st.markdown("---")
    st.subheader("模型设置")
    patient_model_name = st.text_input("患者模型名称", value="o3")
    strategy_model_name = st.text_input("策略模型名称", value="Qwen/Qwen3-8B")
    reply_model_name = st.text_input("回复模型名称", value="o3")
    tom_model_name = st.text_input("ToM 模型名称", value="o3")
    mdt_model_name = st.text_input("MDT 模型名称", value="o3")

    st.markdown("---")
    st.subheader("参数设置")
    is_emotional_patient = st.checkbox("是否使用具有情感的患者智能体", value=True)
    human_in_the_loop = st.checkbox("是否人类作为医生进行对话", value=False, help="人类对话，用文本输入框的形式和患者智能体进行交流")
    if not human_in_the_loop:
        has_expert_knowledge = st.checkbox("是否具备专家知识？", value=True)
        debug_mode = st.checkbox("单步调试", value=False)
    else:
        has_expert_knowledge = False
        debug_mode = True
    max_turns = st.number_input("最长对话轮数", value=20, min_value=1)
    do_eval_patient = st.checkbox("是否进行对话评估", value=True)
    
    if st.button("初始化 / 重置会话"):
        st.session_state.conversation_data = None 
        patient_data, diagnosis_data, examination_data, full_data = load_data(patient_id, diagnosis_id)
        
        if patient_data:
            with st.spinner("初始化模型中……"):
                convo = Conversation(
                    patient_id=patient_id,
                    patient_data=patient_data,
                    diagnosis_id=diagnosis_id,
                    diagnosis_data=diagnosis_data,
                    examination_data=examination_data,
                    patient_model_name=patient_model_name,
                    strategy_model_name=strategy_model_name,
                    reply_model_name=reply_model_name,
                    tom_model_name=tom_model_name,
                    mdt_model_name=mdt_model_name,
                    is_emotional_patient=is_emotional_patient, # Defaulting
                    human_in_the_loop=human_in_the_loop,
                    has_expert_knowledge=has_expert_knowledge, # Assuming expert knowledge for AI
                    max_turns=max_turns,
                    do_eval_patient=do_eval_patient
                )
                asyncio.run(convo.initialize())
            
            st.session_state.conversation_obj = convo
            # If loaded from file, inject history
            if mode == "通过 JSON 文件" and loaded_history:
                st.session_state.conversation_obj.conversation_history = copy.deepcopy(loaded_history)
            
            st.session_state.initialized = True
            st.rerun()

# --- Conversation View --- #

if "initialized" in st.session_state and st.session_state.initialized:
    convo = st.session_state.conversation_obj
    
    # Update parameters dynamically
    convo.human_in_the_loop = human_in_the_loop
    convo.has_expert_knowledge = has_expert_knowledge
    convo.max_turns = max_turns
    
    st.subheader(f"对话 (患者: {convo.patient_id}, 诊断: {convo.diagnosis_id})")

    # Layout: Chat (Left) + Data (Right)
    # The sidebar counts as the 1st column, Chat as 2nd, Data as 3rd.
    col_chat, col_data = st.columns([2, 1])

    # Right Column: Data
    with col_data:
        st.markdown("### 数据面板")
        with st.container(height=450):
            with st.expander("患者数据", expanded=True):
                st.write(convo.user_profile)
        with st.container(height=450):
            with st.expander("诊断数据", expanded=True):
                st.json(convo.diagnosis_data)

    # Left Column: Chat & Controls
    with col_chat:
        history = convo.conversation_history
        
        # Display History
        for i, turn in enumerate(history):
            speaker = turn["speaker"]
            
            if speaker == "Doctor":
                # Doctor Message (Right)
                # Nesting columns: chat_col -> [spacer, msg]
                d_c1, d_c2 = st.columns([1, 4])
                with d_c2:
                    with st.chat_message("assistant", avatar="👨‍⚕️"):
                        msg = turn.get("message", {})
                        response_text = msg.get("response", "")
                        
                        st.markdown(f"<div style='font-size:20px;'>{response_text}</div>", unsafe_allow_html=True)
                        
                        # Expandable details
                        with st.expander("内部状态 (CoT & 策略)", expanded=False):
                            if "tom_reasoning" in turn:
                                st.json(turn["tom_reasoning"])
                            st.write("- **分析:**", msg.get("analysis", "N/A"))
                            st.write("- **策略:**", msg.get("strategy", "N/A"))
                            if msg.get("explanation"):
                                display_str = "- **解释结果:**\n"
                                explanation = MDT_JSON_SCHEMA(msg.get("explanation"))
                                # st.write(explanation)
                                for item in explanation.items:
                                    display_str += f"    - **{item.item}**: {item.explanation}\n"
                                st.write(display_str)
                        
                        # Logic for "Edit & Replay"
                        if st.button("编辑并重播", key=f"edit_btn_{i}"):
                            st.session_state.editing_index = i
                            st.rerun()

            elif speaker == "Patient":
                # Patient Message (Left)
                # Nesting columns: chat_col -> [msg, spacer]
                p_c1, p_c2 = st.columns([4, 1])
                with p_c1:
                    with st.chat_message("user", avatar="👤"):
                        msg = turn.get("message", {})
                        response_text = msg.get("response", "")
                        st.markdown(f"<div style='font-size:20px;'>{response_text}</div>", unsafe_allow_html=True)
                        
                        # Internal State (Patient)
                        with st.expander("内部状态 (CoT)", expanded=False):
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
            # Sanity check
            if 0 <= idx < len(history):
                turn_to_edit = history[idx]
                current_text = turn_to_edit["message"].get("response", "")
                
                st.info("正在编辑医生消息。这将移除后续的所有回复并重新生成患者的回复。")
                new_text = st.text_area("医生消息", value=current_text)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("确认并重播"):
                        # Update text
                        convo.conversation_history[idx]["message"]["response"] = new_text
                        
                        # Slice history: keep up to this doctor turn (idx is included)
                        convo.conversation_history = convo.conversation_history[:idx+1]
                        
                        # Trigger patient response
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
        current_turns = len(history)
        max_turns_reached = current_turns >= 2 * max_turns
        
        if st.session_state.get("run_patient_next") and not max_turns_reached:
            with st.spinner("患者正在回复..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    turn = loop.run_until_complete(generate_patient_step(convo))
                    convo.conversation_history.append(turn)
                except Exception as e:
                    try:
                        turn = asyncio.run(generate_patient_step(convo))
                        convo.conversation_history.append(turn)
                    except Exception as e2:
                        st.error(f"Error generating patient response: {e}, {e2}")
                
            st.session_state.run_patient_next = False
            st.rerun()

        # Controls
        if max_turns_reached:
            st.warning(f"达到最大对话轮数 ({max_turns})。交互结束。")
            
            st.subheader("保存对话")
            save_dir = st.text_input("保存目录", value="results")
            
            if st.button("保存到文件"):
                try:
                    # Use the method from Conversation class
                    convo.save_conversation(save_dir)
                    
                    # Construct expected path for display
                    expected_filename = f"char_{convo.patient_id}diag_{convo.diagnosis_id}.json"
                    full_path = os.path.join(save_dir, expected_filename)
                    
                    st.success(f"成功保存对话到 `{full_path}`")
                except Exception as e:
                    st.error(f"保存文件出错: {e}")

        elif next_speaker == "Doctor":
            st.subheader("下一轮: 医生")
            
            if human_in_the_loop:
                user_input = st.text_area("输入医生的回复:", key="new_doc_input")
                if st.button("发送 (人类)"):
                    if user_input.strip():
                        turn = {
                            "speaker": "Doctor",
                            "tom_reasoning": {
                                "patient_analysis": "human_input",
                                "stage": "human_input", 
                            },
                            "message": {
                                "analysis": "human_input",
                                "strategy": "human_input", 
                                "response": user_input
                            }
                        }
                        convo.conversation_history.append(turn)
                        st.session_state.run_patient_next = True 
                        st.rerun()
            else:
                if debug_mode:
                    if st.button("生成 AI 医生回复"):
                        with st.spinner("医生正在思考..."):
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                turn = loop.run_until_complete(generate_doctor_step(convo))
                                convo.conversation_history.append(turn)
                                st.rerun()
                            except Exception as e:
                                # Fallback for loop issues
                                try:
                                    turn = asyncio.run(generate_doctor_step(convo))
                                    convo.conversation_history.append(turn)
                                    st.rerun()
                                except Exception as e2:
                                    st.error(f"Error generating doctor response: {e}, {e2}")
                else:
                    # Automatic generation (No button)
                    with st.spinner("医生正在思考 (自动)..."):
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            turn = loop.run_until_complete(generate_doctor_step(convo))
                            convo.conversation_history.append(turn)
                            st.rerun()
                        except Exception as e:
                            try:
                                turn = asyncio.run(generate_doctor_step(convo))
                                convo.conversation_history.append(turn)
                                st.rerun()
                            except Exception as e2:
                                st.error(f"Error generating doctor response: {e}, {e2}")                    
        elif next_speaker == "Patient":
            st.subheader("下一轮: 患者")
            if debug_mode:
                if st.button("生成患者回复"):
                    st.session_state.run_patient_next = True
                    st.rerun()
            else:
                # Automatic trigger for patient
                st.session_state.run_patient_next = True
                st.rerun()
