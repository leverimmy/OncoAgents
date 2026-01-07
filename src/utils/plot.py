import json

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

data_all = [
    [
        {"ccs_score": 30, "tas_score": 0, "trs_score": 15, "ers_score": 70},
        {"ccs_score": 20, "tas_score": 20, "trs_score": 25, "ers_score": 45},
        {"ccs_score": 60, "tas_score": 30, "trs_score": 40, "ers_score": 20},
        {"ccs_score": 15, "tas_score": 25, "trs_score": 35, "ers_score": 10},
        {"ccs_score": 60, "tas_score": 35, "trs_score": 30, "ers_score": 5},
        {"ccs_score": 35, "tas_score": 50, "trs_score": 45, "ers_score": 25},
        {"ccs_score": 55, "tas_score": 65, "trs_score": 55, "ers_score": 30},
        {"ccs_score": 70, "tas_score": 25, "trs_score": 50, "ers_score": 25},
    ],
    [
        {"ccs_score": 30, "tas_score": 0, "trs_score": 40, "ers_score": 65},
        {"ccs_score": 45, "tas_score": 30, "trs_score": 65, "ers_score": 30},
        {"ccs_score": 55, "tas_score": 75, "trs_score": 70, "ers_score": 35},
        {"ccs_score": 85, "tas_score": 70, "trs_score": 75, "ers_score": 30},
        {"ccs_score": 55, "tas_score": 65, "trs_score": 65, "ers_score": 20},
        {"ccs_score": 75, "tas_score": 70, "trs_score": 80, "ers_score": 30},
        {"ccs_score": 75, "tas_score": 60, "trs_score": 85, "ers_score": 35},
        {"ccs_score": 55, "tas_score": 55, "trs_score": 80, "ers_score": 40},
        {"ccs_score": 85, "tas_score": 65, "trs_score": 50, "ers_score": 15},
        {"ccs_score": 85, "tas_score": 75, "trs_score": 75, "ers_score": 35},
        {"ccs_score": 85, "tas_score": 90, "trs_score": 85, "ers_score": 40},
        {"ccs_score": 85, "tas_score": 95, "trs_score": 90, "ers_score": 45},
    ],
    [
        {"ccs_score": 20, "tas_score": 0, "trs_score": 20, "ers_score": 30},
        {"ccs_score": 85, "tas_score": 30, "trs_score": 40, "ers_score": 10},
        {"ccs_score": 65, "tas_score": 25, "trs_score": 35, "ers_score": 15},
        {"ccs_score": 50, "tas_score": 10, "trs_score": 30, "ers_score": 5},
        {"ccs_score": 40, "tas_score": 15, "trs_score": 35, "ers_score": 3},
        {"ccs_score": 45, "tas_score": 20, "trs_score": 45, "ers_score": 25},
        {"ccs_score": 20, "tas_score": 40, "trs_score": 50, "ers_score": 25},
        {"ccs_score": 40, "tas_score": 20, "trs_score": 50, "ers_score": 25},
        {"ccs_score": 30, "tas_score": 10, "trs_score": 45, "ers_score": 20},
        {"ccs_score": 45, "tas_score": 15, "trs_score": 50, "ers_score": 15},
        {"ccs_score": 60, "tas_score": 25, "trs_score": 55, "ers_score": 20},
        {"ccs_score": 60, "tas_score": 15, "trs_score": 50, "ers_score": 15},
        {"ccs_score": 60, "tas_score": 10, "trs_score": 45, "ers_score": 10},
        {"ccs_score": 60, "tas_score": 40, "trs_score": 60, "ers_score": 15},
        {"ccs_score": 60, "tas_score": 55, "trs_score": 65, "ers_score": 18},
        {"ccs_score": 60, "tas_score": 70, "trs_score": 75, "ers_score": 22},
    ],
    [
        {"ccs_score": 50, "tas_score": 0, "trs_score": 45, "ers_score": 70},
        {"ccs_score": 55, "tas_score": 30, "trs_score": 60, "ers_score": 35},
        {"ccs_score": 40, "tas_score": 25, "trs_score": 65, "ers_score": 35},
        {"ccs_score": 50, "tas_score": 30, "trs_score": 70, "ers_score": 25},
        {"ccs_score": 60, "tas_score": 35, "trs_score": 75, "ers_score": 20},
        {"ccs_score": 45, "tas_score": 30, "trs_score": 70, "ers_score": 15},
        {"ccs_score": 45, "tas_score": 40, "trs_score": 65, "ers_score": 25},
        {"ccs_score": 50, "tas_score": 45, "trs_score": 60, "ers_score": 30},
        {"ccs_score": 70, "tas_score": 35, "trs_score": 50, "ers_score": 20},
        {"ccs_score": 65, "tas_score": 25, "trs_score": 45, "ers_score": 15},
        {"ccs_score": 30, "tas_score": 15, "trs_score": 40, "ers_score": 25},
        {"ccs_score": 35, "tas_score": 5, "trs_score": 25, "ers_score": 20},
        {"ccs_score": 35, "tas_score": 30, "trs_score": 40, "ers_score": 10},
        {"ccs_score": 35, "tas_score": 35, "trs_score": 40, "ers_score": 10},
        {"ccs_score": 35, "tas_score": 45, "trs_score": 50, "ers_score": 30},
        {"ccs_score": 35, "tas_score": 60, "trs_score": 60, "ers_score": 45},
        {"ccs_score": 35, "tas_score": 75, "trs_score": 70, "ers_score": 50},
    ],
    [
        {"ccs_score": 0, "tas_score": 40, "trs_score": 50, "ers_score": 60},
        {"ccs_score": 20, "tas_score": 45, "trs_score": 50, "ers_score": 40},
        {"ccs_score": 35, "tas_score": 55, "trs_score": 55, "ers_score": 42},
        {"ccs_score": 40, "tas_score": 62, "trs_score": 60, "ers_score": 38},
        {"ccs_score": 55, "tas_score": 65, "trs_score": 67, "ers_score": 40},
        {"ccs_score": 60, "tas_score": 70, "trs_score": 70, "ers_score": 45},
        {"ccs_score": 65, "tas_score": 72, "trs_score": 75, "ers_score": 42},
        {"ccs_score": 65, "tas_score": 75, "trs_score": 78, "ers_score": 45},
        {"ccs_score": 65, "tas_score": 68, "trs_score": 75, "ers_score": 47},
        {"ccs_score": 65, "tas_score": 72, "trs_score": 70, "ers_score": 45},
        {"ccs_score": 65, "tas_score": 68, "trs_score": 60, "ers_score": 40},
        {"ccs_score": 65, "tas_score": 72, "trs_score": 65, "ers_score": 48},
        {"ccs_score": 65, "tas_score": 75, "trs_score": 68, "ers_score": 52},
        {"ccs_score": 65, "tas_score": 70, "trs_score": 70, "ers_score": 50},
        {"ccs_score": 65, "tas_score": 72, "trs_score": 72, "ers_score": 52},
        {"ccs_score": 70, "tas_score": 75, "trs_score": 74, "ers_score": 54},
        {"ccs_score": 70, "tas_score": 78, "trs_score": 78, "ers_score": 60},
        {"ccs_score": 70, "tas_score": 79, "trs_score": 81, "ers_score": 65},
        {"ccs_score": 70, "tas_score": 75, "trs_score": 83, "ers_score": 70},
        {"ccs_score": 70, "tas_score": 78, "trs_score": 85, "ers_score": 72},
    ],
    [],
    [
        {"ccs_score": 30, "tas_score": 0, "trs_score": 30, "ers_score": 65},
        {"ccs_score": 0, "tas_score": 0, "trs_score": 25, "ers_score": 40},
        {"ccs_score": 45, "tas_score": 5, "trs_score": 35, "ers_score": 20},
        {"ccs_score": 20, "tas_score": 50, "trs_score": 25, "ers_score": 10},
        {"ccs_score": 25, "tas_score": 40, "trs_score": 20, "ers_score": 15},
        {"ccs_score": 25, "tas_score": 20, "trs_score": 15, "ers_score": 10},
        {"ccs_score": 25, "tas_score": 10, "trs_score": 10, "ers_score": 5},
        {"ccs_score": 25, "tas_score": 55, "trs_score": 50, "ers_score": 40},
        {"ccs_score": 25, "tas_score": 50, "trs_score": 60, "ers_score": 45},
        {"ccs_score": 25, "tas_score": 60, "trs_score": 70, "ers_score": 55},
        {"ccs_score": 25, "tas_score": 50, "trs_score": 75, "ers_score": 65},
        {"ccs_score": 25, "tas_score": 75, "trs_score": 80, "ers_score": 70},
    ],
]


def plot(case: int):
    # 清空 plt
    plt.clf()
    data = data_all[case - 3]

    # 画出 data 的变化趋势
    ccs_scores = [item["ccs_score"] for item in data]
    tas_scores = [item["tas_score"] for item in data]
    trs_scores = [item["trs_score"] for item in data]
    ers_scores = [item["ers_score"] for item in data]

    # 设置字体
    plt.rcParams["font.sans-serif"] = ["SimHei"]  # 用来正常显示中文标签

    plt.plot(ccs_scores, label="认知清晰度", color="orange")
    plt.plot(trs_scores, label="信任度", color="green")
    plt.plot(ers_scores, label="情绪稳定度", color="red")
    plt.plot(tas_scores, label="治疗接受度", color="blue")
    # 限定 x 范围
    plt.xlim(0 - 0.5, len(data) - 1 + 0.5)
    plt.xlabel("轮次")
    plt.ylabel("分数")
    plt.title("对话轮次中的分数趋势")
    ax = plt.gca()  # 获取当前坐标轴
    line_legend = plt.legend(loc="lower right")
    ax.add_artist(
        line_legend
    )  # 关键步骤：将第一个图例固定在图上，防止被下一个legend()覆盖
    # plt.show()

    doc_stage = []
    pat_stage = []

    def mapping(zh_cn: str) -> int:
        if zh_cn == "认知与邀请阶段":
            return 0
        elif zh_cn == "知识传递阶段":
            return 1
        elif zh_cn == "共情支持阶段":
            return 2
        elif zh_cn == "策略与总结阶段":
            return 3

    with open(f"final_conversation/dia{case}_patient{case}.json") as f:
        conversation = json.load(f)
        for turn in conversation["conversation_history"]:
            if turn["speaker"] == "Patient":
                pat_stage.append(
                    turn["message"]["stage"] if turn["message"]["ers_score"] > 30 else 2
                )
            else:
                doc_stage.append(mapping(turn["stage"]))
    pat_stage[0] = 0
    print(doc_stage, pat_stage)
    stage_colors = ["blue", "orange", "red", "green"]
    for i in range(len(pat_stage)):
        plt.axvspan(i - 0.5, i + 0.5, color=stage_colors[pat_stage[i]], alpha=0.1)
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

    # plt.show()
    plt.savefig(f"conversation_scores_trend_colored_{case}.png")


if __name__ == "__main__":
    plot(case=3)
    plot(case=4)
    plot(case=5)
    plot(case=6)
    plot(case=7)
    plot(case=9)
