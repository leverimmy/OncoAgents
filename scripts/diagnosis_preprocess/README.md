# Patient Diagnosis Preprocessing

>   Suppose the current folder is `path/to/OncoAgents/scripts/diagnosis_preprocess`.

Run the following command to preprocess raw patient diagnosis data:

```bash
uv run python3 main.py \
    --input_dir ../../data/raw/肺癌_非小细胞_1357 \
    --output_dir ../../data/raw/肺癌_非小细胞_preprocessed \
    --workers 16
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
    --source_dir ../../data/raw/肺癌_非小细胞_preprocessed/success \
    --dest_dir ../../data/diagnosis_all/肺癌
uv run python3 de-identify.py \
    --source_dir ../../data/raw/乳腺癌_preprocessed/success \
    --dest_dir ../../data/diagnosis_all/乳腺癌
uv run python3 de-identify.py \
    --source_dir ../../data/raw/胃癌_preprocessed/success \
    --dest_dir ../../data/diagnosis_all/胃癌
uv run python3 de-identify.py \
    --source_dir ../../data/raw/前列腺癌_preprocessed/success \
    --dest_dir ../../data/diagnosis_all/前列腺癌
uv run python3 de-identify.py \
    --source_dir ../../data/raw/结直肠癌_preprocessed/success \
    --dest_dir ../../data/diagnosis_all/结直肠癌
```

Run the following command to duplicate dataset:

```bash
uv run python3 duplicate.py \
    --source_dir ../../data/diagnosis_all/前列腺癌3_base \
    --dest_dir ../../data/diagnosis_all/前列腺癌3 \
    --start_id 79 \
    --num_duplicates 120

uv run python3 duplicate.py \
    --source_dir ../../data/diagnosis_all/前列腺癌4_base \
    --dest_dir ../../data/diagnosis_all/前列腺癌4 \
    --start_id 199 \
    --num_duplicates 315
```
