# Dataset Generation

>   Suppose the current folder is `path/to/OncoAgents/scripts/dataset_construction`.

Run the following command to generate a sample dataset of patient characteristic IDs and diagnosis IDs:

```bash
uv run python3 main.py \
    --background_dir ../../data/background \
    --diagnosis_dir ../../data/diagnosis \
    --output_dir ../../data/test \
    --sample_size=30 \
    --seed=30
```

Visualize the distribution of generated patient backgrounds:

```bash
uv run python3 statistics.py \
    --input_dir ../../data/test \
    --output_dir ../../data/figs
```
