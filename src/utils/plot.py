import json
import traceback

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def plot(case: int):
    # 清空 plt
    plt.clf()
    ccs_scores = []
    ess_scores = []
    pas_scores = []
    stages = []
    with open(f"./results/final_conversation/dia{case}_patient{case}.json") as f:
        data = json.load(f)
        for turn in data["conversation_history"]:
            if turn["speaker"] == "Patient":
                ccs_scores.append(turn["message"].get("ccs_score", 0))
                ess_scores.append(turn["message"].get("ess_score", 0))
                pas_scores.append(turn["message"].get("pas_score", 0))
                stages.append(turn["message"].get("stage_transfer", "认知与邀请阶段"))

    # 设置字体
    plt.rcParams["font.sans-serif"] = ["SimHei"]  # 用来正常显示中文标签

    plt.plot(ccs_scores, label="认知清晰度", color="orange")
    plt.plot(ess_scores, label="情绪压力度", color="green")
    plt.plot(pas_scores, label="患者依从度", color="blue")
    print(pas_scores)
    # 限定 x 范围
    plt.xlim(-0.5, len(stages) - 0.5)
    # x 每 2 点一个刻度
    plt.xticks(range(len(stages)))
    plt.xlabel("轮次")
    plt.ylabel("分数")
    plt.title("对话轮次中的分数趋势")
    ax = plt.gca()  # 获取当前坐标轴
    line_legend = plt.legend(loc="lower right")
    ax.add_artist(
        line_legend
    )  # 关键步骤：将第一个图例固定在图上，防止被下一个legend()覆盖
    # plt.show()

    try:
        stage_mapping = {
            "认知与邀请阶段": 0,
            "知识传递阶段": 1,
            "共情支持阶段": 2,
            "策略与总结阶段": 3,
        }
        stage_colors = ["blue", "orange", "red", "green"]
        for i in range(len(stages)):
            plt.axvspan(i - 0.5, i + 0.5, color=stage_colors[stage_mapping[stages[i]]], alpha=0.1)
        stage_labels = ["认知与邀请阶段", "知识传递阶段", "共情支持阶段", "策略与总结阶段"]

        stage_patches = [
            Patch(
                facecolor=stage_colors[i],
                edgecolor="none",
                alpha=0.1,
                label=stage_labels[i],
            )
            for i in range(len(stage_colors))
        ]

        plt.legend(handles=stage_patches, loc="upper left")
    except Exception:
        traceback.print_exc()

    # plt.show()
    plt.savefig(f"./results/figs/conversation_scores_trend_colored_{case}.png")


if __name__ == "__main__":
    plot(case=1)
    plot(case=2)
    plot(case=3)
    plot(case=4)
    plot(case=5)
    plot(case=6)
