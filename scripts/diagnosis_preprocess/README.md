# Patient Diagnosis Preprocessing

>   Suppose the current folder is `path/to/OncoAgents/scripts/diagnosis_preprocess`.

Run the following command to preprocess raw patient diagnosis data:

```bash
uv run python3 main.py \
    --input_dir ../../data/raw/lung_非小细胞 \
    --output_dir ../../data/raw/肺癌_非小细胞_preprocessed \
    --workers 16
```

Run the following command to de-identify and move the dataset:

```bash
uv run python3 de-identify.py \
    --source_dir ../../data/raw/肺癌_非小细胞_preprocessed/success \
    --dest_dir ../../data/diagnosis
```
