CUDA_VISIBLE_DEVICES=0,1,2,3 \
vllm serve /ssd/xze/hf/models/Qwen/Qwen3-8B \
  --host 0.0.0.0 --port 8000 \
  --dtype auto \
  --served-model-name Qwen/Qwen3-8B \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.90

CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
vllm serve Qwen/Qwen3-8B \
  --host 0.0.0.0 --port 8000 \
  --dtype auto \
  --served-model-name Qwen/Qwen3-8B \
  --tensor-parallel-size 8 \
  --gpu-memory-utilization 0.90

CUDA_VISIBLE_DEVICES=0,1,2,3 \
vllm serve /ssd/xze/sft/Qwen3-8B/sft-full/20260306 \
  --host 0.0.0.0 --port 8001 \
  --dtype auto \
  --served-model-name Qwen/Qwen3-8B-SFT \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.90

CUDA_VISIBLE_DEVICES=4,5,6,7 \
vllm serve /ssd/xze/dpo/Qwen3-8B/dpo-full/20260306/checkpoint-40 \
  --host 0.0.0.0 --port 8002 \
  --dtype auto \
  --served-model-name Qwen/Qwen3-8B-DPO \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.90

CUDA_VISIBLE_DEVICES=4,5 \
vllm serve /ssd/xze/hf/models/Henrychur/MMedS-Llama-3-8B \
  --host 0.0.0.0 --port 8001 \
  --dtype auto \
  --served-model-name Henrychur/MMedS-Llama-3-8B \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.90
