# Clinical Note Generation

First, modify the `note_generation_prompt.py` file to set all the necessary constants for the experiment.

Then, run the following command to obtain the note generation results:

```bash
uv run python3 main.py
```

Finally, run the following command to obtain a HTML file displaying the generated notes:

```bash
uv run python3 generate_html.py \
    --input_dir path/to/results \
    --output_file path/to/html/file
```
