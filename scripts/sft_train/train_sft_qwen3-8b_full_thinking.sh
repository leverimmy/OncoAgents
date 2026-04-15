export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
export WANDB_API_KEY=""
export WANDB_ENTITY=""
export WANDB_PROJECT=""

llamafactory-cli train cfg_sft_qwen3-8b_full_thinking.yaml
