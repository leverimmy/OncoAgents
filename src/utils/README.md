# Results Analysis and Plotting

>   Suppose the current folder is `path/to/OncoAgents`.

Run the following command to analyze and plot the results from the final conversations:

```bash
uv run python3 -m src.utils.plot \
    --input_dir_1 ./results/pretest_o3/expert_knowledge \
    --input_dir_2 ./results/pretest_qwen/expert_knowledge \
    --output_dir ./results/comparison/pretest_o3_qwen_expert_knowledge
```
