export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
export WANDB_API_KEY="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"
export WANDB_ENTITY="leverimmy-organization"
export WANDB_PROJECT="OncoAgents"

llamafactory-cli train cfg_dpo_qwen3-8b_full_thinking.yaml
