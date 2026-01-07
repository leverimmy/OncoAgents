LOGGING_FILE_DIR=./logs python3 -m src.main --id 1 \
    --patient_model o3 \
    --strategy_model Qwen/Qwen3-8B \
    --reply_model gpt-5-mini \
    --tom_model o3 \
    --max_turns 2 \
    --expert_knowledge \
    --is_emotional_patient \
    --human_in_the_loop \
    --output_dir ./results
