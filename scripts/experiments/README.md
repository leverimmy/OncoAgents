# Results Analysis and Plotting

>   Suppose the current folder is `path/to/OncoAgents/scripts/experiments`.

```bash
uv run python3 experiment_2_analysis.py

zip -r "figs-$(date +%Y-%m-%d_%H-%M-%S).zip" ./figs/*.pdf
```

```bash
uv run python3 experiment_2_plot.py \
    --input_file /root/xze/OncoAgents/results/2026-02-26-2/test_deepseek-v3.2/cot/char127_diag2_胃癌.json
```

```bash
uv run python3 experiment_3_2_analysis.py \
    --input_dir ../../results/2026-02-26-2
```

```bash
uv run python3 experiment_3_1_analysis.py \
    --input_dir /root/xze/OncoAgents/apps/results/exp3 \
    --agent_root /root/xze/OncoAgents/scripts/experiments/data \
    --n_bootstrap 5000 \
    --seed 42 \
    --out_prefix exp3_rank_alignment
```

```bash
uv run python3 experiment_4_plot.py \
    --input_dir ../../results/2026-02-26-1/pretest_o3/warm\
    --output_dir ./figs/exp4

uv run python3 experiment_4_plot.py \
    --input_dir ../../results/2026-02-26-2/note_o3/warm\
    --output_dir ./figs/exp4 \
    --framework
```

```bash
uv run python3 experiment_4_2_analysis.py \
  --before_dir /root/xze/OncoAgents/results/2026-03-22/test_qwen3-8b/warm \
  --after_dir /root/xze/OncoAgents/results/2026-03-22/test_qwen3-8b-dpo/warm \
  --output_dir ./
```

```bash
uv run python3 experiment_4_generate_html.py \
  --input_dir /root/xze/OncoAgents/apps/results/exp4/邓思瑶/25/results/warm \
  --output ./output_1.html
```
