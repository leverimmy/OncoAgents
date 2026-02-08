CUDA_VISIBLE_DEVICES=0,1,2,3 \
vllm serve /ssd/xze/hf/models/Qwen/Qwen3-8B \
  --host 0.0.0.0 --port 8000 \
  --dtype auto \
  --served-model-name Qwen/Qwen3-8B \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.90
