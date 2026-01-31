CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
vllm serve /ssd/xze/Qwen3-8B \
  --host 0.0.0.0 --port 8000 \
  --dtype auto \
  --served-model-name Qwen3-8B \
  --tensor-parallel-size 8 \
  --gpu-memory-utilization 0.90
