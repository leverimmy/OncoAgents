# Patient Diagnosis Preprocessing

>   Suppose the current folder is `path/to/OncoAgents`.

Run the following command to preprocess raw patient diagnosis data:

```bash
uv run python3 -m src.preprocess.main \
    --input_dir ./data/raw/肺癌 \
    --output_dir ./data/raw/肺癌_preprocessed \
    --workers 16
```

Run the following command to generate display-friendly JSON files:

```bash
uv run python3 -m src.preprocess.display \
    --input_dir ./data/raw/肺癌_preprocessed \
    --output_dir ./data/raw/肺癌_display
```
