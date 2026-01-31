uv run python3 -m src.preprocess.main \
    --input_dir ./data/raw/肺癌 \
    --output_dir ./data/raw/肺癌_preprocessed \
    --workers 16
uv run python3 -m src.preprocess.main \
    --input_dir ./data/raw/结直肠癌 \
    --output_dir ./data/raw/结直肠癌_preprocessed \
    --workers 16
uv run python3 -m src.preprocess.main \
    --input_dir ./data/raw/前列腺癌 \
    --output_dir ./data/raw/前列腺癌_preprocessed \
    --workers 16
uv run python3 -m src.preprocess.main \
    --input_dir ./data/raw/乳腺癌 \
    --output_dir ./data/raw/乳腺癌_preprocessed \
    --workers 16
uv run python3 -m src.preprocess.main \
    --input_dir ./data/raw/胃癌 \
    --output_dir ./data/raw/胃癌_preprocessed \
    --workers 16
uv run python3 -m src.preprocess.main \
    --input_dir ./data/raw/lung_非小细胞 \
    --output_dir ./data/raw/lung_非小细胞_preprocessed \
    --workers 16
