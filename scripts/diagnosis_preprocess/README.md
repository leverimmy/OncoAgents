# Patient Diagnosis Preprocessing

>   Suppose the current folder is `path/to/OncoAgents/scripts/diagnosis_preprocess`.

Run the following command to preprocess raw patient diagnosis data:

```bash
uv run python3 main.py \
    --input_dir ../../data/raw/乳腺癌_1326 \
    --output_dir ../../data/raw/乳腺癌_preprocessed \
    --workers 16
```

Or run the following commands to preprocess raw patient diagnosis data in `.xlsx` format:

```bash
uv run python3 main_xlsx.py \
    --input_file ../../data/raw/xlsx/胃癌病历_脱敏.xlsx \
    --output_dir ../../data/raw/胃癌_preprocessed \
    --workers 16
uv run python3 main_xlsx.py \
    --input_file ../../data/raw/xlsx/前列腺癌病历_脱敏.xlsx \
    --output_dir ../../data/raw/前列腺癌_preprocessed \
    --workers 16
uv run python3 main_xlsx.py \
    --input_file ../../data/raw/xlsx/结直肠癌病历_脱敏.xlsx \
    --output_dir ../../data/raw/结直肠癌_preprocessed \
    --workers 16
```

Run the following command to de-identify and move the dataset:

```bash
uv run python3 de-identify.py \
    --source_dir ../../data/raw/乳腺癌_preprocessed/success \
    --dest_dir ../../data/diagnosis/乳腺癌
```
