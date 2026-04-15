import argparse
import json
import matplotlib.pyplot as plt
from pathlib import Path

MAX_TURNS = 15



if __name__ == '__main__':
    parser = argparse.ArgumentParser("Plot the scores of a given case.")
    parser.add_argument("--input_file", type=str, required=True, help="Path to the input JSON file containing the scores.")

    args = parser.parse_args()
    input_file = Path(args.input_file)

    data = json.load(open(input_file, encoding="utf-8"))
    scores = data["scores"]["patient_scores"]

    ccs_scores = []
    ess_scores = []
    pas_scores = []
    for i in range(MAX_TURNS):
        if i < len(scores):
            score = scores[i]
        else:
            if data["negotiation_result"] == "accept":
                score = {
                    "ccs_score": 100.0,
                    "ess_score": 0.0,
                    "pas_score": 100.0,
                }
            elif data["negotiation_result"] == "reject":
                score = {
                    "ccs_score": 0.0,
                    "ess_score": 100.0,
                    "pas_score": 0.0,
                }
        ccs_scores.append(score['ccs_score'])
        ess_scores.append(score['ess_score'])
        pas_scores.append(score['pas_score'])
    print("CCS Scores:", ccs_scores)
    print("ESS Scores:", ess_scores)
    print("PAS Scores:", pas_scores)
    # Plot the scores
    turns = list(range(1, MAX_TURNS + 1))
    plt.figure(figsize=(10, 4))
    plt.plot(turns, ccs_scores, marker='o', label='CCS Score', color='blue')
    # triangle
    plt.plot(turns, ess_scores, marker='^', label='ESS Score', color='red')
    plt.plot(turns, pas_scores, marker='s', label='PAS Score', color='green')
    plt.xlabel('Turn')
    plt.ylabel('Score')
    plt.title('Patient Scores Over Turns')
    plt.xticks(turns)
    plt.ylim(0, 100)
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.savefig("./figs/scores_over_turns.svg", dpi=200, format="svg", bbox_inches="tight")

    # 在同一个图里，按照不同的 y 轴范围，画出 ccs_score(0-100)，ess_score 和 pas_score 自适应范围的线图。 --- IGNORE ---
    turns = list(range(1, MAX_TURNS + 1))
    fig, ax1 = plt.subplots(figsize=(10, 3))
    ax1.plot(turns, ccs_scores, marker='o', label='CCS Score', color='blue', linestyle='--')
    ax1.set_xlabel('Turn')
    ax1.set_ylabel('CCS Score', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_ylim(-5, 105)
    ax1.spines["top"].set_visible(False)

    ax2 = ax1.twinx()
    ax2.plot(turns, pas_scores, marker='s', label='PAS Score', color='green', linewidth=4)

    ax2.plot(turns, ess_scores, marker='^', label='ESS Score', color='red', linestyle='--')
    ax2.set_ylabel('ESS & PAS Scores', color='black')
    ax2.tick_params(axis='y', labelcolor='black')
    ax2.set_ylim(47, 87)

    ax2.spines["top"].set_visible(False)

    plt.title('Patient Scores Over Turns')
    plt.xticks(turns)
    fig.legend(loc='upper left', bbox_to_anchor=(0.8, 0.47))
    # plt.grid()
    plt.tight_layout()
    plt.savefig("./figs/scores_over_turns_dual_axis.svg", dpi=200, format="svg", bbox_inches="tight")

import numpy as np

turns = list(range(1, MAX_TURNS + 1))

fig, ax = plt.subplots(figsize=(8, 5), dpi=200)

# ===== 设置 offset =====
gap = 50   # 每条线之间的垂直距离
offset_ccs = 0 * gap
offset_ess = 1 * gap
offset_pas = 2 * gap

# ===== 画线（加 offset）=====
ax.plot(turns, np.array(ccs_scores) + offset_ccs,
        color="blue", linewidth=2, marker='o', markersize=4)
ax.plot(turns, np.array(ess_scores) + offset_ess,
        color="red", linewidth=2, marker='^', markersize=4)
ax.plot(turns, np.array(pas_scores) + offset_pas,
        color="green", linewidth=2, marker='s', markersize=4)

# ===== 可选：填充 =====
ax.fill_between(turns,
                0,
                np.array(ccs_scores) + offset_ccs,
                color="blue", alpha=0.2)

ax.fill_between(turns,
                0,
                np.array(ess_scores) + offset_ess,
                color="red", alpha=0.2)

ax.fill_between(turns,
                0,
                np.array(pas_scores) + offset_pas,
                color="green", alpha=0.2)

# ===== 右侧写名字 =====
ax.text(MAX_TURNS + 0.5, offset_ccs + 50, "CCS",
        fontsize=14, va="center")
ax.text(MAX_TURNS + 0.5, offset_ess + 50, "ESS",
        fontsize=14, va="center")
ax.text(MAX_TURNS + 0.5, offset_pas + 50, "PAS",
        fontsize=14, va="center")

# ===== 美化 =====
ax.set_xlim(1, MAX_TURNS)
ax.set_ylim(-10, offset_pas + 100)
ax.set_xticks(turns)

ax.set_xlabel("Turn")
ax.set_yticks([])             # 关键：隐藏 y 轴
ax.spines["left"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(True)
ax.spines["bottom"].set_visible(True)

plt.tight_layout()
plt.savefig("./figs/scores_ridge_style.svg", bbox_inches="tight")