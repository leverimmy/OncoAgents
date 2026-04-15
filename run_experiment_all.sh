# Framework, Qwen3-8B-DPO
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full \
    --patient_model o3 \
    --strategy_model Qwen/Qwen3-8B-DPO \
    --reply_model gpt-5-chat \
    --mdt_model qwen3-8b \
    --judge_model o3 \
    --url http://localhost:8002/v1 \
    --max_turns 15 \
    --expert_knowledge \
    --is_emotional_patient \
    --output_dir ./results/2026-03-22/test_qwen3-8b-dpo \
    --max_workers 12

# Framework, Qwen3-8B
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full \
    --patient_model o3 \
    --strategy_model Qwen/Qwen3-8B \
    --reply_model gpt-5-chat \
    --mdt_model Qwen/Qwen3-8B \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --expert_knowledge \
    --is_emotional_patient \
    --output_dir ./results/2026-03-22/test_qwen3-8b \
    --max_workers 8
