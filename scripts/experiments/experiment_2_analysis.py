import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from tqdm import tqdm

DIR = Path("../../apps/results")

METRICS = ["overall", "emotion", "cognition", "persona", "interaction"]
REFINE = {
    "overall": "Overall Performance",
    "emotion": "Emotional Expressiveness",
    "cognition": "Cognitive Ability",
    "persona": "Persona Consistency",
    "interaction": "Interactive Fluency",
}
OFFSETS = {
    "main": -1,
    "error_bar": 0.3,
    "box_plot": -0.3,
    "half_violin": -0.5,
}
GROUPS = ["o3\n(Baseline)", "Affective-Cognitive\nPatient Agent"]

TARGET_DIR = Path("./figs/")

TARGET_DIR.mkdir(exist_ok=True, parents=True)

LABEL_FS = 15   # x/y label
TITLE_FS = 20   # title
PVALUE_FS = 12  # p值/bracket文字
XTICK_FS = 15   # x轴分组名（如果你说的 x label 是指下面两组名字）
YTICK_FS = 15   # y轴刻度数字（如果你想一起变大）

plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['pdf.fonttype'] = 42

rows = []
for file in DIR.glob("**/*.json"):
    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    scores = data["scores"]["judge_patient_scores"]

    parts = str(file).split("-")
    cond = parts[-1].split(".")[0]  # "0" or "1"
    pair_id = "-".join(parts[:-1])  # same id across 0/1

    group = GROUPS[int(cond)]

    for m in METRICS:
        rows.append({
            "pair_id": pair_id,
            "group": group,
            "metric": m,
            "value": scores[m]
        })
        # print(rows[-1])

df = pd.DataFrame(rows)

# =========================
# Helpers
# =========================
def _half_violin(ax, data, x, width=0.28, side="left", color="#f2c300", alpha=0.55, bw_method=None):
    """
    Draw a half violin at position x.
    side: "left" or "right"
    """
    data = np.asarray(data, dtype=float)
    vp = ax.violinplot(
        [data],
        positions=[x],
        widths=width * 2,
        showmeans=False,
        showmedians=False,
        showextrema=False,
        bw_method=bw_method,
    )
    body = vp["bodies"][0]
    body.set_facecolor(color)
    body.set_edgecolor("none")
    body.set_alpha(alpha)

    # Clip to half by modifying vertices
    verts = body.get_paths()[0].vertices
    if side == "left":
        verts[:, 0] = np.minimum(verts[:, 0], x)
    else:  # right
        verts[:, 0] = np.maximum(verts[:, 0], x)

    return vp

def _add_bracket(ax, x1, x2, y, text, h=0.12, lw=1.5, fontsize=10):
    """
    Draw a bracket between x1 and x2 at height y, with label text.
    """
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=lw, color="black", clip_on=False)
    ax.text((x1 + x2) / 2, y + h + 0.05, text, ha="center", va="bottom", fontsize=fontsize)

def _mean_ci_sem(data, ci=0.95):
    """
    Return mean and a symmetric error bar length.
    Here we use dd as error (like many biology plots). You can switch to bootstrap CI easily.
    """
    data = np.asarray(data, dtype=float)
    mean = float(np.mean(data))
    sem = float(np.std(data, ddof=1) / np.sqrt(len(data))) if len(data) > 1 else 0.0
    return mean, sem

def plot_metric_paired_violin_box(
    df,
    metric: str,
    out_path: str,
    groups=GROUPS,
    colors=("#92c5de", "#f4a582"),
    seed=0,
    w=5.2,
):
    """
    df columns: pair_id, group, metric, value (1..5)
    """
    rng = np.random.default_rng(seed)

    # --- pivot to paired format and drop incomplete pairs
    sub = df[df["metric"] == metric].copy()
    pivot = sub.pivot(index="pair_id", columns="group", values="value")
    # keep only the two groups
    pivot = pivot.loc[:, list(groups)]
    pivot = pivot.dropna()
    n_pairs = pivot.shape[0]
    if n_pairs == 0:
        raise ValueError(f"No complete pairs found for metric={metric}")

    y_left = pivot[groups[0]].to_numpy(dtype=float)
    y_right = pivot[groups[1]].to_numpy(dtype=float)

    # --- Wilcoxon paired test
    # (scipy wilcoxon要求 paired，自动忽略0差异的处理取决于版本；这里保持默认)
    stat, p = wilcoxon(y_left, y_right)

    def p_to_star(p):
        if p < 0.0001:
            return "****"
        elif p < 0.001:
            return "***"
        elif p < 0.01:
            return "**"
        elif p < 0.05:
            return "*"
        else:
            return "ns"
    stars = p_to_star(p)
    p_text = f"{stars}(P={p:.3g})" #, N={n_pairs}"
    print(f"N={n_pairs} pairs, Wilcoxon stat={stat:.2f}, p={p:.3g} => {p_text}")

    # --- figure
    fig, ax = plt.subplots(figsize=(w, 4.2), dpi=200)

    xL, xR = 1.0, 2.25

    # Half violins (left = left-half, right = right-half)
    _half_violin(ax, y_left,  xL + OFFSETS["half_violin"], side="left",  color=colors[0], alpha=1)
    _half_violin(ax, y_right, xR - OFFSETS["half_violin"], side="right", color=colors[1], alpha=1)

    # Boxplots (one per group)
    bp = ax.boxplot(
        [y_left, y_right],
        positions=[xL + OFFSETS["box_plot"], xR - OFFSETS["box_plot"]],
        widths=0.18,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color="black", linewidth=1.5),
        boxprops=dict(linewidth=1.2, color="black"),
        whiskerprops=dict(linewidth=1.2, color="black"),
        capprops=dict(linewidth=1.2, color="black"),
    )
    bp["boxes"][0].set_facecolor(colors[0])
    bp["boxes"][0].set_alpha(1)
    bp["boxes"][1].set_facecolor(colors[1])
    bp["boxes"][1].set_alpha(1)

    # Jittered scatter + paired grey lines
    # keep dots near each x position (like reference)
    jitter = 0.25
    x_left_pts  = xL + rng.uniform(-jitter, jitter, size=n_pairs)
    x_right_pts = xR + rng.uniform(-jitter, jitter, size=n_pairs)

    def get_jitter_x(base, idx, jitter, xs):
        num_of_y = sum([1 for i, y in enumerate(xs) if y == xs[idx]])
        real_jitter = jitter * (num_of_y / n_pairs)  # scale jitter based on number of overlapping points
        return base + rng.uniform(-real_jitter, real_jitter)

    x_left_pts = [get_jitter_x(xL, i, jitter, y_left) for i in range(n_pairs)]
    x_right_pts = [get_jitter_x(xR, i, jitter, y_right) for i in range(n_pairs)]

    jitter_y = 0.25
    y_left_pts = [y + rng.uniform(-jitter_y, jitter_y) for y in y_left]
    y_right_pts = [y + rng.uniform(-jitter_y, jitter_y) for y in y_right]

    for i in range(n_pairs):
        ax.plot([x_left_pts[i], x_right_pts[i]], [y_left_pts[i], y_right_pts[i]],
                color="0.8", linewidth=1.0, zorder=1)

    ax.scatter(x_left_pts,  y_left_pts,  s=22, color=colors[0], edgecolor="none", alpha=1, zorder=2)
    ax.scatter(x_right_pts, y_right_pts, s=22, color=colors[1], edgecolor="none", alpha=1, zorder=2)

    # Mean + error bar (SEM) as colored vertical bar + big dot
    mL, eL = _mean_ci_sem(y_left)
    mR, eR = _mean_ci_sem(y_right)
    ax.errorbar([xL + OFFSETS["error_bar"]], [mL], yerr=[eL], fmt="o", markersize=5,
                color=colors[0], ecolor=colors[0], elinewidth=2, capsize=6, zorder=3)
    ax.errorbar([xR - OFFSETS["error_bar"]], [mR], yerr=[eR], fmt="o", markersize=5,
                color=colors[1], ecolor=colors[1], elinewidth=2, capsize=6, zorder=3)

    ax.plot([xL + OFFSETS["error_bar"], xR - OFFSETS["error_bar"]], [mL, mR],
            marker="o", markersize=3, color="black", linewidth=1.5, zorder=4)

    delta = mR - mL
    ci_text = f"From {mL:.2f} to {mR:.2f}, Δ={delta:.2f}\n95% CI=[{mR - mL - 1.96*eR:.2f}, {delta + 1.96*eR:.2f}]"
    # ax.text((xL + OFFSETS["error_bar"] + xR - OFFSETS["error_bar"]) / 2, (mL + mR) / 2, ci_text,
    #         ha="center", va="bottom", fontsize=9, color="black", zorder=5)
    print(f"{metric}: {p_text}, {ci_text}")
    

    # Axis formatting
    ax.set_xlim(xL + OFFSETS["main"], xR - OFFSETS["main"])
    ax.set_xticks([xL, xR])
    ax.set_xticklabels([groups[0], groups[1]])
    ax.set_ylabel("Rating", fontsize=LABEL_FS)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylim(0.6, 6.0)
    ax.tick_params(axis="x", labelsize=XTICK_FS)
    ax.tick_params(axis="y", labelsize=YTICK_FS)

    # Bracket + p-value on top
    y_top = 5.5
    _add_bracket(ax, xL, xR, y=y_top, text=p_text, h=0.12, lw=1.5, fontsize=PVALUE_FS)

    # Title
    ax.set_title("")
    y = 1.03
    # ax.text(
    #     0.5,
    #     y,
    #     "Rating Statistics for ",
    #     transform=ax.transAxes,
    #     ha="right",
    #     fontsize=14,
    #     color="black"
    # ) 
    ax.text(
        0.5,
        y,
        REFINE[metric],
        transform=ax.transAxes,
        ha="center",
        fontsize=TITLE_FS,
        color="black",
        # fontdict={"weight": "bold", "style": "italic"}
    )

    # Clean look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    # ax.spines["left"].set_visible(False)
    # ax.spines["bottom"].set_visible(False)

    # ax.text(
    #     -0.05,
    #     -0.15,
    #     "*Rating values are jittered for better visualization, real data only has integer values from 1 to 5.",
    #     transform=ax.transAxes,
    #     ha="left",
    #     va="top",
    #     fontsize=9,
    #     color="0.4"
    # )

    fig.tight_layout()
    fig.savefig(out_path, format="pdf", bbox_inches="tight")

    plt.close(fig)


# =========================
# Batch plot all metrics
# =========================
for i, metric in tqdm(enumerate(METRICS), desc="Plotting metrics"):
    fig_prefix = f"fig3{chr(ord('a') + i + 1)}"
    out_path = str(TARGET_DIR / f"{fig_prefix}_{metric}_statistics.pdf")
    if i == 0:
        plot_metric_paired_violin_box(df, metric=metric, out_path=out_path, seed=42)
    else:
        plot_metric_paired_violin_box(df, metric=metric, out_path=out_path, seed=42, w=6.5)
    print("Saved:", out_path)
