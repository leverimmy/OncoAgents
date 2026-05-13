# OncoAgents


## Setting Up the Environment

## Training the Model

We adopted a two-stage training strategy to train the DPO model. In the first stage, we fine-tuned the Qwen3-8B model on the training data using supervised learning. In the second stage, we further fine-tuned the model using the DPO algorithm.

### Stage 1: Supervised Fine-tuning

In the first stage, we fine-tuned the Qwen3-8B model on the training data using supervised learning.

At `./scripts/sft_data_generation`, generate the training data using the following command:

```bash
uv run python3 main.py \
    --input_dir path/to/all/input/data \
    --output_file ../sft_train/data/test_o3.jsonl
```

At `./scripts/sft_train`, run the following command to start the SFT process:

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
export WANDB_API_KEY=""
export WANDB_ENTITY=""
export WANDB_PROJECT=""

llamafactory-cli train ./cfg_sft_qwen3-8b_full_thinking.yaml
```

### Stage 2: DPO

In the second stage, we further trained the model using the DPO algorithm.

At `./scripts/dpo_data_generation`, generate the training data for DPO using the following command:

```bash
uv run python3 main.py \
    --input_dir path/to/all/input/data \
    --output_file ../dpo_train/data/dpo_train_o3.jsonl
```

At `./scripts/dpo_train`, run the following command to start the DPO process:

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
export WANDB_API_KEY=""
export WANDB_ENTITY=""
export WANDB_PROJECT=""

llamafactory-cli train ./cfg_dpo_qwen3-8b_full_thinking.yaml
```

## Running the Code

We use vLLM to serve the models. Run the following commands to start the servers for the models:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
vllm serve path/to/local/Qwen/Qwen3-8B \
  --host 0.0.0.0 --port 8000 \
  --dtype auto \
  --served-model-name Qwen/Qwen3-8B \
  --tensor-parallel-size 8 \
  --gpu-memory-utilization 0.90

CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
vllm serve path/to/local/Henrychur/MMedS-Llama-3-8B \
  --host 0.0.0.0 --port 8001 \
  --dtype auto \
  --served-model-name Henrychur/MMedS-Llama-3-8B \
  --tensor-parallel-size 8 \
  --gpu-memory-utilization 0.90

CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
vllm serve path/to/DPO/model \
  --host 0.0.0.0 --port 8002 \
  --dtype auto \
  --served-model-name Qwen/Qwen3-8B-DPO \
  --tensor-parallel-size 8 \
  --gpu-memory-utilization 0.90
```

At `./`, use the following command to simulate the doctor-patient interaction:

```bash
LOGGING_FILE_DIR=./logs uv run python3 -m src.main \
  --input_dir path/to/data \
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
  --output_dir path/to/results \
  --max_workers 8
```

Note that if the `--baseline` flag is set, then `--strategy_model`, `--reply_model` and `--judge_model` arguments will be ignored.

## Collecting Data



## Reproducing the Results


## System Environment

The code is developed and tested on a Linux system with the following specifications:

- OS: Ubuntu 22.04 LTS (Linux 5.15.0-91-generic)
- CPU: Intel Xeon Platinum 8336C
- GPU: NVIDIA A100 80GB (8 GPUs)
