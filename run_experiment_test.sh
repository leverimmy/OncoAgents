# Baseline, Qwen3-8B
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model Qwen/Qwen3-8B \
    --reply_model Qwen/Qwen3-8B \
    --mdt_model Qwen/Qwen3-8B \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_qwen3-8b \
    --max_workers 8

# Baseline, GPT-5-Chat
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model gpt-5-chat \
    --reply_model gpt-5-chat \
    --mdt_model gpt-5-chat \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_gpt-5-chat \
    --max_workers 8

# Baseline, DeepSeek-V3.2
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model deepseek-ai/DeepSeek-V3.2 \
    --reply_model deepseek-ai/DeepSeek-V3.2 \
    --mdt_model deepseek-ai/DeepSeek-V3.2 \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_deepseek-v3.2 \
    --max_workers 4

# Baseline, DeepSeek-R1
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model deepseek-ai/DeepSeek-R1 \
    --reply_model deepseek-ai/DeepSeek-R1 \
    --mdt_model deepseek-ai/DeepSeek-R1 \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_deepseek-r1 \
    --max_workers 4

# Baseline, GLM-4.7
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model Pro/zai-org/GLM-4.7 \
    --reply_model Pro/zai-org/GLM-4.7 \
    --mdt_model Pro/zai-org/GLM-4.7 \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_glm-4.7 \
    --max_workers 4

# Baseline, GPT-5-2025-08-07
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model gpt-5-2025-08-07 \
    --reply_model gpt-5-2025-08-07 \
    --mdt_model gpt-5-2025-08-07 \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_gpt-5-2025-08-07 \
    --max_workers 8

# Baseline, o3-2025-04-16
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model o3-2025-04-16 \
    --reply_model o3-2025-04-16 \
    --mdt_model o3-2025-04-16 \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_o3-2025-04-16 \
    --max_workers 8

# New!!!
# Baseline, o3-2025-04-16
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full \
    --patient_model o3 \
    --strategy_model o3-2025-04-16 \
    --reply_model o3-2025-04-16 \
    --mdt_model o3-2025-04-16 \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --output_dir ./results/2026-03-22/test_o3-2025-04-16 \
    --max_workers 8

# Baseline, Baichuan-M3
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model Baichuan-M3 \
    --reply_model Baichuan-M3 \
    --mdt_model Baichuan-M3 \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_baichuan-m3 \
    --max_workers 8

# Baseline, Qwen3-8B-No-Thinking
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model Qwen/Qwen3-8B-No-Thinking \
    --reply_model Qwen/Qwen3-8B-No-Thinking \
    --mdt_model Qwen/Qwen3-8B-No-Thinking \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_qwen3-8b-no-thinking \
    --max_workers 8

# Baseline, Qwen3-8B-No-Thinking
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model qwen3-8b \
    --reply_model qwen3-8b \
    --mdt_model qwen3-8b \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_qwen3-8b-thinking \
    --max_workers 8


### Warm Agent - With FRAMEWORK ###

# Framework, Qwen3-8B
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model Qwen/Qwen3-8B \
    --reply_model gpt-5-chat \
    --mdt_model Qwen/Qwen3-8B \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --expert_knowledge \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_qwen3-8b \
    --max_workers 8

# Framework, o3
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model o3 \
    --reply_model gpt-5-chat \
    --mdt_model qwen3-8b \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --expert_knowledge \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_o3 \
    --max_workers 8

# Framework, Qwen3-8B-SFT
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model Qwen/Qwen3-8B-SFT \
    --reply_model gpt-5-chat \
    --mdt_model qwen3-8b \
    --judge_model o3 \
    --url http://localhost:8001/v1 \
    --max_turns 15 \
    --expert_knowledge \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_qwen3-8b-sft \
    --max_workers 8

# Framework, Qwen3-8B-DPO
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model Qwen/Qwen3-8B-DPO \
    --reply_model gpt-5-chat \
    --mdt_model qwen3-8b \
    --judge_model o3 \
    --url http://localhost:8002/v1 \
    --max_turns 15 \
    --expert_knowledge \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_qwen3-8b-dpo \
    --max_workers 8

## New!!!
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

# Henrychur/MMedS-Llama-3-8B
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/test \
    --patient_model o3 \
    --strategy_model Henrychur/MMedS-Llama-3-8B \
    --reply_model Henrychur/MMedS-Llama-3-8B \
    --mdt_model Henrychur/MMedS-Llama-3-8B \
    --judge_model o3 \
    --url http://localhost:8001/v1 \
    --max_turns 15 \
    --expert_knowledge \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_doctor \
    --output_dir ./results/2026-02-26-2/test_henrychur-mmeds-llama-3-8b \
    --max_workers 8
