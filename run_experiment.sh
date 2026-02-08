# Baseline, Qwen3-8B
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/pretest \
    --patient_model o3 \
    --strategy_model Qwen/Qwen3-8B \
    --reply_model Qwen/Qwen3-8B \
    --mdt_model Qwen/Qwen3-8B \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_patient \
    --do_eval_doctor \
    --output_dir ./results/pretest_qwen \
    --max_workers 8

# Baseline, o3
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/pretest \
    --patient_model o3 \
    --strategy_model o3 \
    --reply_model o3 \
    --mdt_model o3 \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --is_baseline \
    --is_emotional_patient \
    --do_eval_patient \
    --do_eval_doctor \
    --output_dir ./results/pretest_o3 \
    --max_workers 8

# Framework, Qwen3-8B
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/pretest \
    --patient_model o3 \
    --strategy_model Qwen/Qwen3-8B \
    --reply_model Qwen/Qwen3-8B \
    --mdt_model Qwen/Qwen3-8B \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --expert_knowledge \
    --is_emotional_patient \
    --do_eval_patient \
    --do_eval_doctor \
    --output_dir ./results/pretest_qwen \
    --max_workers 8

# Framework, o3
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/pretest \
    --patient_model o3 \
    --strategy_model o3 \
    --reply_model gpt-5-mini \
    --mdt_model Qwen/Qwen3-8B \
    --judge_model o3 \
    --url http://localhost:8000/v1 \
    --max_turns 15 \
    --expert_knowledge \
    --is_emotional_patient \
    --do_eval_patient \
    --do_eval_doctor \
    --output_dir ./results/pretest_o3 \
    --max_workers 8
