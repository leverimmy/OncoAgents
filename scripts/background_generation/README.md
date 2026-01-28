# Patient Background Generation

>   Suppose the current folder is `path/to/OncoAgents`.

Generate patients' background data:

```bash
uv run scripts/background_generation/main.py \
    --output_dir data/background
```

Visualize the distribution of generated patient backgrounds:

```bash
uv run scripts/background_generation/statistics.py \
    --input_dir data/background \
    --output_dir data/figs
```
