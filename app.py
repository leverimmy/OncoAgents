import streamlit as st
import json
import os
import sys
import asyncio
import copy

# Add current directory to path so we can import src
sys.path.append(os.path.abspath("."))

from src.conversation import Conversation
from src.utils import STAGE2NAME

# Page Config
st.set_page_config(layout="wide", page_title="OncoAgents Conversation")

# --- Constants & Helpers --- #
DATA_DIR = "data/"

def load_data(patient_id, diagnosis_id):
    """Loads and merges patient and diagnosis data."""
    try:
        full_data = {}
        bg_path = os.path.join(DATA_DIR, "background", f"{patient_id}.json")
        diag_path = os.path.join(DATA_DIR, "diagnosis", f"{diagnosis_id}.json")
        
        if not os.path.exists(bg_path):
             st.error(f"Background file not found: {bg_path}")
             return None, None, None, None
        if not os.path.exists(diag_path):
             st.error(f"Diagnosis file not found: {diag_path}")
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
        st.error(f"Error loading data: {e}")
        return None, None, None, None

async def generate_doctor_step(conversation):
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
             tom_reasoning = await conversation._run_tom_reasoning()
    else:
        tom_reasoning = {
            "patient_analysis": "human_input",
            "stage": "human_input",
        }
    
    # 2. Strategy
    stage = tom_reasoning.get("stage", "human_input")
    patient_analysis = tom_reasoning.get("patient_analysis", "human_input")

    analysis, strategy, is_explanation_needed = await conversation._run_strategy_model(
        stage=stage,
        analysis=patient_analysis,
    )

    # 3. Reply
    doctor_reply = await conversation._run_reply_model(
        analysis, strategy, is_explanation_needed
    )
    
    doctor_ret = {
        "analysis": analysis,
        "strategy": strategy,
        "response": doctor_reply,
    }
    
    term = {
        "speaker": "Doctor",
        "tom_reasoning": tom_reasoning,
        "message": doctor_ret,
    }
    return term

async def generate_patient_step(conversation):
    """Runs one step of patient generation."""
    patient_ret = await conversation.patient_agent.respond(
        dialogue_history=conversation._get_dialogue_history()
    )
    
    term = {
        "speaker": "Patient",
        "message": patient_ret,
    }
    return term

# --- Main App Logic --- #

st.title("OncoAgents Interactive Interface")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    mode = st.radio("Initialization Mode", ["From IDs", "From JSON File"])
    
    patient_id = 1
    diagnosis_id = 1
    loaded_history = []
    
    if mode == "From IDs":
        patient_id = st.number_input("Patient ID (Characteristic)", value=1, min_value=1)
        diagnosis_id = st.number_input("Diagnosis ID", value=1, min_value=1)
    else:
        uploaded_file = st.file_uploader("Upload Conversation JSON", type=["json"])
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                patient_id = data.get("patient_id", 1)
                diagnosis_id = data.get("diagnosis_id", 1)
                loaded_history = data.get("conversation_history", [])
                st.success(f"Loaded: Pat {patient_id}, Diag {diagnosis_id}, {len(loaded_history)} turns.")
            except Exception as e:
                st.error(f"Invalid JSON: {e}")

    # Settings
    st.markdown("---")
    st.subheader("Model Configuration")
    patient_model_name = st.text_input("Patient Model Name", value="gpt-4o")
    strategy_model_name = st.text_input("Strategy Model Name", value="gpt-4o")
    reply_model_name = st.text_input("Reply Model Name", value="gpt-4o")
    tom_model_name = st.text_input("ToM Model Name", value="gpt-4o")
    mdt_model_name = st.text_input("MDT Model Name", value="gpt-4o")

    st.markdown("---")
    st.subheader("Parameters")
    is_emotional_patient = st.checkbox("Is Emotional Patient?", value=True)
    has_expert_knowledge = st.checkbox("Has Expert Knowledge?", value=True)
    max_turns = st.number_input("Max Turns", value=20, min_value=1)
    
    human_in_the_loop = st.checkbox("Human in the Loop (Doctor)", value=False, help="Text box for Doctor input instead of AI.")
    
    if st.button("Initialize / Reset Session"):
        st.session_state.conversation_data = None 
        patient_data, diagnosis_data, examination_data, full_data = load_data(patient_id, diagnosis_id)
        
        if patient_data:
            with st.spinner("Initializing models..."):
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
                    max_turns=max_turns
                )
            
            st.session_state.conversation_obj = convo
            # If loaded from file, inject history
            if mode == "From JSON File" and loaded_history:
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
    
    st.subheader(f"Conversation (Pat: {convo.patient_id}, Diag: {convo.diagnosis_id})")
    # Show details of patient_data and diagnosis_data
    # Split into 2 columns
    with st.expander("View Patient & Diagnosis Data", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Patient Data")
            st.json(convo.patient_data)
        with col2:
            st.markdown("### Diagnosis Data")
            st.json(convo.diagnosis_data)
    history = convo.conversation_history
    
    # Display History
    for i, turn in enumerate(history):
        speaker = turn["speaker"]
        
        if speaker == "Doctor":
            # Doctor Message (Right)
            col1, col2 = st.columns([1, 4])
            with col2:
                with st.chat_message("assistant", avatar="👨‍⚕️"):
                    msg = turn.get("message", {})
                    response_text = msg.get("response", "")
                    
                    st.markdown(f"<div style='font-size:20px;'>{response_text}</div>", unsafe_allow_html=True)
                    
                    # Expandable details
                    with st.expander("Internal State (CoT & Strategy)", expanded=False):
                        if "tom_reasoning" in turn:
                            st.json(turn["tom_reasoning"])
                        st.write("- **Analysis:**", msg.get("analysis", "N/A"))
                        st.write("- **Strategy:**", msg.get("strategy", "N/A"))
                    
                    # Logic for "Edit & Replay"
                    # User wants to modify the last doctor turn.
                    # We check if this is the last turn OR second to last (if Patient responded).
                    is_last_doctor_turn = False
                    if i == len(history) - 1:
                        is_last_doctor_turn = True
                    elif i == len(history) - 2 and history[-1]["speaker"] == "Patient":
                        is_last_doctor_turn = True
                    
                    if is_last_doctor_turn:
                        if st.button("Edit & Replay", key=f"edit_btn_{i}"):
                            st.session_state.editing_index = i
                            st.rerun()

        elif speaker == "Patient":
            # Patient Message (Left)
            col1, col2 = st.columns([4, 1])
            with col1:
                with st.chat_message("user", avatar="👤"):
                    msg = turn.get("message", {})
                    response_text = msg.get("response", "")
                    st.markdown(f"<div style='font-size:20px;'>{response_text}</div>", unsafe_allow_html=True)
                    
                    # Internal State (Patient)
                    with st.expander("Internal State (CoT)", expanded=False):
                        st.markdown("## Emotional CoT")
                        st.write(f"- **Analysis**: {msg.get('emotional_analysis', 'N/A')}")
                        st.write(f"- **State**: {msg.get('emotion_state', 'N/A')}")
                        
                        st.markdown("## Rational CoT")
                        st.write(f"- **Input Analysis**: {msg.get('input_analysis', 'N/A')}")
                        st.write(f"- **Knowledge**: {msg.get('knowledge', 'N/A')}")
                        st.write(f"- **Info Gap**: {msg.get('information_gap', 'N/A')}")

                        st.markdown("## Stage")
                        st.write(f"- **Stage Analysis**: {msg.get('stage_analysis', 'N/A')}")
                        st.write(f"- **Current Stage**: {msg.get('stage_transfer', 'N/A')}")
                        st.write(f"- **PAS Analysis**: {msg.get('pas_analysis', 'N/A')}")

                    # Scores
                    with st.expander("## Scores", expanded=False):
                        st.write(f"- **CCS**: {msg.get('ccs_score', 'N/A')}")
                        st.write(f"- **ESS**: {msg.get('ess_score', 'N/A')}")
                        st.write(f"- **PAS**: {msg.get('pas_score', 'N/A')}")
                        st.write(f"- **Decision**: {msg.get('decision', 'N/A')}")

    # --- Editing Area (if active) --- #
    if "editing_index" in st.session_state:
        idx = st.session_state.editing_index
        # Sanity check
        if 0 <= idx < len(history):
            turn_to_edit = history[idx]
            current_text = turn_to_edit["message"].get("response", "")
            
            st.info("Editing Doctor Message. This will remove any subsequent responses and regenerate the Patient response.")
            new_text = st.text_area("Doctor Message", value=current_text)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Confirm & Replay"):
                    # Update text
                    convo.conversation_history[idx]["message"]["response"] = new_text
                    
                    # Slice history: keep up to this doctor turn (idx is included)
                    convo.conversation_history = convo.conversation_history[:idx+1]
                    
                    # Trigger patient response
                    st.session_state.run_patient_next = True
                    del st.session_state.editing_index
                    st.rerun()
            with col_b:
                if st.button("Cancel"):
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
    # A turn is considered complete when both Doctor and Patient have spoken.
    # So we count pairs.
    current_turns = len(history)
    max_turns_reached = current_turns >= 2 * max_turns
    
    # Auto-run patient if set (unless max turns reached, but if allow completing partial turn?)
    # If patient needs to speak (next_speaker="Patient"), we are in the middle of a turn.
    # So max_turns_reached (based on pairs) would be False if len is odd.
    # Example: Max=1.
    # 1. Doc speaks. History=1. Turns=0. Reached=False. Next=Patient. -> Allow Patient.
    # 2. Patient speaks. History=2. Turns=1. Reached=True. -> Stop.
    
    if st.session_state.get("run_patient_next") and not max_turns_reached:
        with st.spinner("Patient is responding..."):
            try:
                 # Check if loop is already running?
                 # Streamlit runs linearly. existing_loop logic shouldn't be issue unless inside another async function.
                 # Actually asyncio.run() cannot be called when an event loop is already running.
                 # Streamlit might have one?
                 # Safer to use:
                 loop = asyncio.new_event_loop()
                 asyncio.set_event_loop(loop)
                 turn = loop.run_until_complete(generate_patient_step(convo))
                 convo.conversation_history.append(turn)
            except Exception as e:
                # If "This event loop is already running" happens, we might need a different approach.
                # Just trying basic run first.
                try:
                    turn = asyncio.run(generate_patient_step(convo))
                    convo.conversation_history.append(turn)
                except Exception as e2:
                    st.error(f"Error generating patient response: {e}, {e2}")
            
        st.session_state.run_patient_next = False
        st.rerun()

    # Controls
    if max_turns_reached:
        st.warning(f"Max turns ({max_turns}) reached. Interaction finished.")
        
        st.subheader("Save Conversation")
        save_dir = st.text_input("Save Directory", value="results")
        
        if st.button("Save to File"):
            try:
                # Use the method from Conversation class
                convo.save_conversation(save_dir)
                
                # Construct expected path for display
                expected_filename = f"char_{convo.patient_id}diag_{convo.diagnosis_id}.json"
                full_path = os.path.join(save_dir, expected_filename)
                
                st.success(f"Successfully saved conversation to `{full_path}`")
            except Exception as e:
                st.error(f"Error saving file: {e}")

    elif next_speaker == "Doctor":
        st.subheader("Next Turn: Doctor")
        
        if human_in_the_loop:
            user_input = st.text_area("Enter Doctor's Response:", key="new_doc_input")
            if st.button("Send (Human)"):
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
            if st.button("Generate AI Doctor Response"):
                with st.spinner("Doctor is thinking..."):
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

    elif next_speaker == "Patient":
        st.subheader("Next Turn: Patient")
        if st.button("Generate Patient Response"):
            st.session_state.run_patient_next = True
            st.rerun()

else:
    st.info("Please initialize the conversation from the sidebar.")
