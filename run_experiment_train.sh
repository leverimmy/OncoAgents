# Framework, o3
LOGGING_FILE_DIR=./logs python3 -m src.main \
    --input_dir ./data/full/train \
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
    --output_dir ./results/2026-02-26-2/train_o3 \
    --max_workers 8

cd scripts/sft_data_generation
uv run python3 main.py \
    --input_dir ../../results/2026-02-26-2/train_o3/warm \
    --output_file ../sft_train/data/sft_train_o3.jsonl

cd ../sft_train
sh train_sft_qwen3-8b_full_thinking.sh

cd ../dpo_data_generation
uv run python3 main.py \
    --input_dir ../../results/2026-02-26-2/train_o3/warm \
    --output_file ../dpo_train/data/dpo_train_o3.jsonl \
    --max_workers 8

cd ../dpo_train
sh train_dpo_qwen3-8b_full_thinking.sh
