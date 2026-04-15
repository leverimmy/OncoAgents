#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Figure 6 panels (a-g), a combined Figure 6, and a long-format Excel
table of subgroup medians for Results 4.2.

Inputs
------
- final_test_cases.zip
- Pasted code (2).py

Outputs
-------
- population_level_medians_long.xlsx
- fig6a_pre_existing_effects.(pdf/png)
- fig6b_pre_stage_medians.(pdf/png)
- fig6c_pre_selected_contrasts.(pdf/png)
- fig6d_post_existing_effects.(pdf/png)
- fig6e_pre_extended_medians.(pdf/png)
- fig6f_post_extended_medians.(pdf/png)
- fig6g_post_personality_medians.(pdf/png)
- fig6_population_patterns_combined.(pdf/png)
- results_exp42_population_nc_v7.tex
- figure_population_patterns_abcdefg.tex
- figure_population_patterns_abcdefg_legend.txt
"""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.gridspec import GridSpec
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from scipy import stats


OUTCOME_ORDER = [
    "End-of-conversation APS",
    "End-of-conversation CCS",
    "End-of-conversation EWS",
    "Minimum EWS",
]
OUTCOME_SHORT = ["APS", "CCS", "EWS", "Min EWS"]

FACTOR_EN = {
    "gender": "Gender",
    "age": "Age",
    "cancer_type": "Cancer type",
    "stage_1234": "Stage",
    "education_level": "Education",
    "financial_status": "Financial",
    "personality": "Personality",
    "communication_style": "Style",
    "systemic_therapy_involved": "Systemic therapy",
    "surgery_involved": "Surgery",
    "chemotherapy_involved": "Chemotherapy",
    "symptom_burden": "Symptom burden",
    "metastatic_recurrent_context": "Metastatic/\nrecurrent",
    "lymph_node_involvement": "Lymph-node",
    "heavy_alcohol_history": "Heavy alcohol",
    "smoking_history": "Smoking",
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--zip_path", default="/mnt/data/final_test_cases.zip")
    p.add_argument("--code_path", default="/mnt/data/Pasted code (2).py")
    p.add_argument("--out_dir", default="/mnt/data/fig6_population_outputs")
    p.add_argument("--formats", nargs="+", default=["pdf"], choices=["pdf", "png"])
    return p.parse_args()


def load_module(code_path: Path):
    spec = importlib.util.spec_from_file_location("pop", str(code_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pop"] = mod
    spec.loader.exec_module(mod)
    return mod


def epsilon_squared_kruskal(H, n, k):
    return max(0.0, (H - k + 1) / (n - k)) if n > k else np.nan


def rank_biserial_from_u(U, n1, n2):
    return 2 * U / (n1 * n2) - 1


def analyze_factor(pop, df, spec, outcome):
    subset = df[[spec.key, outcome]].dropna()
    if subset.empty:
        return {"p": np.nan, "effect": np.nan, "method": "NA", "n": 0}
    if spec.kind == "continuous":
        rho, p = stats.spearmanr(subset[spec.key], subset[outcome], alternative="two-sided")
        return {
            "p": float(p),
            "effect": abs(float(rho)),
            "signed_effect": float(rho),
            "method": "Spearman",
            "n": len(subset),
        }
    levels = pop.ordered_levels(subset[spec.key], spec)
    groups = [subset.loc[subset[spec.key] == lvl, outcome] for lvl in levels]
    if spec.kind == "binary" or len(levels) == 2:
        U, p = stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided")
        rrb = rank_biserial_from_u(U, len(groups[0]), len(groups[1]))
        return {
            "p": float(p),
            "effect": abs(float(rrb)),
            "signed_effect": float(rrb),
            "method": "Mann-Whitney U",
            "n": len(subset),
        }
    H, p = stats.kruskal(*groups)
    eps = epsilon_squared_kruskal(H, len(subset), len(levels))
    return {
        "p": float(p),
        "effect": float(eps),
        "method": "Kruskal-Wallis",
        "n": len(subset),
    }


def add_transformed_outcomes(df):
    df = df.copy()
    df["End-of-conversation APS"] = df["final_pas"]
    df["End-of-conversation CCS"] = df["final_ccs"]
    df["End-of-conversation EWS"] = 100 - df["final_ess"]
    df["Minimum EWS"] = 100 - df["max_ess"]
    return df


def short_level(spec_key, level, edu_limited=None, edu_expert=None):
    if spec_key == "education_level":
        if level == edu_limited:
            return "Limited"
        if level == edu_expert:
            return "Expert"
        return str(level)
    if spec_key == "personality":
        mapping = {
            "不信任：对医疗系统或医生持怀疑态度": "Distrustful",
            "不耐烦：易怒、易激动、缺乏耐心": "Impatient",
            "中性：情绪稳定，易于沟通": "Neutral",
            "啰嗦：喜欢详细讨论，难以集中主题": "Verbose",
            "过度乐观：忽视风险，过分相信治疗效果": "Over-optimistic",
            "过度焦虑：总是感到担忧和紧张，难以放松": "Anxious",
        }
        return mapping.get(level, str(level))
    if spec_key == "communication_style":
        mapping = {
            "信息收集型：喜欢获取大量背景信息和细节": "Info-seeking",
            "冷静理性型：交流中一直保持冷静和理性，不受情绪影响": "Composed",
            "情绪表达型：倾向于表达自己的情感和感受": "Emotionally expressive",
            "沉默顺从型：被动回应，很少表达自己的想法": "Passive",
            "问题驱动型：喜欢提出问题，针对具体问题寻求解答": "Question-driven",
        }
        return mapping.get(level, str(level))
    if level is True:
        return "Yes"
    if level is False:
        return "No"
    return str(level)


def median_by_level(pop, df, spec, edu_limited=None, edu_expert=None):
    rows = []
    if spec.kind == "continuous":
        return rows
    levels = pop.ordered_levels(df[spec.key].dropna(), spec)
    for lvl in levels:
        sub = df[df[spec.key] == lvl]
        rows.append({
            "Factor": FACTOR_EN[spec.key],
            "Level": short_level(spec.key, lvl, edu_limited, edu_expert),
            "n": len(sub),
            **{out: float(np.median(sub[out])) if len(sub) else np.nan for out in OUTCOME_ORDER},
        })
    return rows


def build_long_excel(pop, before_df, after_df, out_path):
    edu_spec = next(s for s in pop.EXISTING_FACTORS if s.key == "education_level")
    edu_limited, edu_expert = edu_spec.level_order[0], edu_spec.level_order[-1]

    rows = []
    for dataset_name, df in [("pre-RL", before_df), ("post-RL", after_df)]:
        for spec in pop.EXISTING_FACTORS + pop.EXTENDED_FACTORS:
            for row in median_by_level(pop, df, spec, edu_limited, edu_expert):
                row["Dataset"] = dataset_name
                rows.append(row)
    long_df = pd.DataFrame(rows)[["Dataset", "Factor", "Level", "n"] + OUTCOME_ORDER]

    wb = Workbook()
    ws = wb.active
    ws.title = "all_medians"
    headers = list(long_df.columns)
    for j, h in enumerate(headers, 1):
        c = ws.cell(1, j, h)
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="D9EAF7")
        c.alignment = Alignment(horizontal="center")
    for i, row in enumerate(long_df.itertuples(index=False), 2):
        for j, val in enumerate(row, 1):
            ws.cell(i, j, val)
    ws.freeze_panes = "A2"
    for idx, col in enumerate(headers, 1):
        width = max(len(str(col)), int(long_df[col].astype(str).map(len).quantile(0.95))) + 2
        ws.column_dimensions[get_column_letter(idx)].width = min(max(width, 10), 40)

    wb.save(out_path)


def effect_matrix(pop, df, specs):
    m = np.zeros((len(OUTCOME_ORDER), len(specs)))
    p = np.zeros_like(m)
    for j, spec in enumerate(specs):
        for i, out in enumerate(OUTCOME_ORDER):
            res = analyze_factor(pop, df, spec, out)
            m[i, j] = res["effect"]
            p[i, j] = res["p"]
    return m, p


def save_panel(fig, basepath: Path, formats):
    for fmt in formats:
        fig.savefig(str(basepath) + f".{fmt}", bbox_inches="tight", dpi=300)


def panel_letter(ax, letter):
    ax.text(-0.12, 1.05, letter, transform=ax.transAxes, fontsize=14, fontweight="bold",
            va="top", ha="left")


def heatmap_with_text(ax, data, row_labels, col_labels, vmin=None, vmax=None, cmap="Blues",
                      fmt="{:.3f}", star_mask=None):
    im = ax.imshow(data, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=30, ha="right")
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            s = fmt.format(val)
            if star_mask is not None and star_mask[i, j]:
                s += " *"
            ax.text(j, i, s, ha="center", va="center", fontsize=7, color="black")
    ax.set_xlim(-0.5, data.shape[1] - 0.5)
    ax.set_ylim(data.shape[0] - 0.5, -0.5)
    return im


def add_bar_labels(ax, bars, fmt="{:.0f}", rotation=0):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 0.8, fmt.format(h),
                ha="center", va="bottom", fontsize=7, rotation=rotation)


class FigureBuilder:
    def __init__(self, pop, before_df, after_df, out_dir: Path, formats):
        self.pop = pop
        self.before_df = before_df
        self.after_df = after_df
        self.out_dir = out_dir
        self.formats = formats

        self.existing_specs = pop.EXISTING_FACTORS
        self.extended_specs = pop.EXTENDED_FACTORS

        self.pre_exist_m, self.pre_exist_p = effect_matrix(pop, before_df, self.existing_specs)
        self.post_exist_m, self.post_exist_p = effect_matrix(pop, after_df, self.existing_specs)

        self.stage_levels = [1, 2, 3, 4]
        self.stage_labels = ["I", "II", "III", "IV"]
        self.stage_pre = {
            out: [float(np.median(before_df.loc[before_df["stage_1234"] == s, out])) for s in self.stage_levels]
            for out in OUTCOME_ORDER
        }

        edu_spec = next(s for s in pop.EXISTING_FACTORS if s.key == "education_level")
        self.edu_limited = edu_spec.level_order[0]
        self.edu_expert = edu_spec.level_order[-1]
        self.pers_anx = "过度焦虑：总是感到担忧和紧张，难以放松"
        self.pers_neu = "中性：情绪稳定，易于沟通"
        self.style_em = "情绪表达型：倾向于表达自己的情感和感受"
        self.style_comp = "冷静理性型：交流中一直保持冷静和理性，不受情绪影响"

        self.sel_labels = ["Limited", "Expert", "Anxious", "Neutral", "Emotionally\nexpressive", "Composed"]
        self.sel_values = {
            "APS": [
                float(np.median(before_df.loc[before_df["education_level"] == self.edu_limited, "End-of-conversation APS"])),
                float(np.median(before_df.loc[before_df["education_level"] == self.edu_expert, "End-of-conversation APS"])),
                float(np.median(before_df.loc[before_df["personality"] == self.pers_anx, "End-of-conversation APS"])),
                float(np.median(before_df.loc[before_df["personality"] == self.pers_neu, "End-of-conversation APS"])),
                float(np.median(before_df.loc[before_df["communication_style"] == self.style_em, "End-of-conversation APS"])),
                float(np.median(before_df.loc[before_df["communication_style"] == self.style_comp, "End-of-conversation APS"])),
            ],
            "CCS/EWS": [
                float(np.median(before_df.loc[before_df["education_level"] == self.edu_limited, "End-of-conversation CCS"])),
                float(np.median(before_df.loc[before_df["education_level"] == self.edu_expert, "End-of-conversation CCS"])),
                float(np.median(before_df.loc[before_df["personality"] == self.pers_anx, "End-of-conversation EWS"])),
                float(np.median(before_df.loc[before_df["personality"] == self.pers_neu, "End-of-conversation EWS"])),
                float(np.median(before_df.loc[before_df["communication_style"] == self.style_em, "End-of-conversation EWS"])),
                float(np.median(before_df.loc[before_df["communication_style"] == self.style_comp, "End-of-conversation EWS"])),
            ],
        }

        self.extended_rows = []
        for spec in self.extended_specs:
            for lvl in pop.ordered_levels(before_df[spec.key].dropna(), spec):
                self.extended_rows.append((spec.key, lvl))
        self.extended_row_labels = [f"{FACTOR_EN[k]}: {short_level(k, lvl)}" for k, lvl in self.extended_rows]
        self.ext_pre_mat = self._extended_matrix(before_df)
        self.ext_post_mat = self._extended_matrix(after_df)

        pers_order = next(s for s in pop.EXISTING_FACTORS if s.key == "personality").level_order
        self.g_labels = [short_level("personality", lvl) for lvl in pers_order]
        self.g_mat = np.zeros((len(pers_order), len(OUTCOME_ORDER)))
        for r, lvl in enumerate(pers_order):
            sub = after_df[after_df["personality"] == lvl]
            for c, out in enumerate(OUTCOME_ORDER):
                self.g_mat[r, c] = float(np.median(sub[out]))

        plt.rcParams.update({
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.titlesize": 12,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        })

    def _extended_matrix(self, df):
        mat = np.zeros((len(self.extended_rows), len(OUTCOME_ORDER)))
        for r, (k, lvl) in enumerate(self.extended_rows):
            sub = df[df[k] == lvl]
            for c, out in enumerate(OUTCOME_ORDER):
                mat[r, c] = float(np.median(sub[out])) if len(sub) else np.nan
        return mat

    def generate_fig6a(self):
        fig, ax = plt.subplots(figsize=(8.6, 3.8))
        im = heatmap_with_text(
            ax, self.pre_exist_m, OUTCOME_SHORT, [FACTOR_EN[s.key] for s in self.existing_specs],
            vmin=0, vmax=max(self.pre_exist_m.max(), self.post_exist_m.max()),
            cmap="YlGnBu", fmt="{:.3f}", star_mask=self.pre_exist_p < 0.05
        )
        panel_letter(ax, "a")
        ax.set_title("Pre-RL effect sizes across existing fields")
        cbar = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.18, fraction=0.06)
        cbar.set_label("Effect size")
        fig.tight_layout()
        save_panel(fig, self.out_dir / "fig6a_pre_existing_effects", self.formats)
        return fig

    def generate_fig6b(self):
        fig, ax = plt.subplots(figsize=(8.2, 4.4))
        x = np.arange(len(self.stage_labels))
        width = 0.18
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
        for idx, out in enumerate(OUTCOME_ORDER):
            bars = ax.bar(x + (idx - 1.5) * width, self.stage_pre[out], width,
                          label=OUTCOME_SHORT[idx], color=colors[idx])
            add_bar_labels(ax, bars, fmt="{:.0f}" if out != "End-of-conversation CCS" else "{:.1f}")
        panel_letter(ax, "b")
        ax.set_title("Pre-RL stage I--IV medians")
        ax.set_xticks(x)
        ax.set_xticklabels(self.stage_labels)
        ax.set_xlabel("Stage")
        ax.set_ylabel("Median score")
        ax.set_ylim(0, max(max(v) for v in self.stage_pre.values()) + 15)
        ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.18))
        ax.grid(axis="y", alpha=0.2)
        fig.tight_layout()
        save_panel(fig, self.out_dir / "fig6b_pre_stage_medians", self.formats)
        return fig

    def generate_fig6c(self):
        fig, ax = plt.subplots(figsize=(9.4, 4.2))
        x = np.arange(len(self.sel_labels))
        width = 0.34
        bars1 = ax.bar(x - width / 2, self.sel_values["APS"], width, label="APS", color="#1f77b4")
        bars2 = ax.bar(x + width / 2, self.sel_values["CCS/EWS"], width, label="CCS or EWS", color="#ff7f0e")
        add_bar_labels(ax, bars1, fmt="{:.0f}")
        add_bar_labels(ax, bars2, fmt="{:.1f}" if any(v % 1 for v in self.sel_values["CCS/EWS"]) else "{:.0f}")
        for xpos in [1.5, 3.5]:
            ax.axvline(xpos, color="gray", linestyle="--", linewidth=1)
        ax.text(0.5, 1.02, "Education", transform=ax.get_xaxis_transform(), ha="center", fontsize=9, fontweight="bold")
        ax.text(2.5, 1.02, "Personality", transform=ax.get_xaxis_transform(), ha="center", fontsize=9, fontweight="bold")
        ax.text(4.5, 1.02, "Communication style", transform=ax.get_xaxis_transform(), ha="center", fontsize=9, fontweight="bold")
        panel_letter(ax, "c")
        ax.set_title("Selected pre-RL subgroup contrasts")
        ax.set_xticks(x)
        ax.set_xticklabels(self.sel_labels)
        ax.set_ylabel("Median score")
        ax.set_ylim(0, max(max(self.sel_values["APS"]), max(self.sel_values["CCS/EWS"])) + 18)
        ax.legend(loc="upper right")
        ax.grid(axis="y", alpha=0.2)
        fig.tight_layout()
        save_panel(fig, self.out_dir / "fig6c_pre_selected_contrasts", self.formats)
        return fig

    def generate_fig6d(self):
        fig, ax = plt.subplots(figsize=(8.6, 3.8))
        im = heatmap_with_text(
            ax, self.post_exist_m, OUTCOME_SHORT, [FACTOR_EN[s.key] for s in self.existing_specs],
            vmin=0, vmax=max(self.pre_exist_m.max(), self.post_exist_m.max()),
            cmap="YlGnBu", fmt="{:.3f}", star_mask=self.post_exist_p < 0.05
        )
        panel_letter(ax, "d")
        ax.set_title("Post-RL effect sizes across existing fields")
        cbar = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.18, fraction=0.06)
        cbar.set_label("Effect size")
        fig.tight_layout()
        save_panel(fig, self.out_dir / "fig6d_post_existing_effects", self.formats)
        return fig

    def generate_fig6e(self):
        fig, ax = plt.subplots(figsize=(7.8, 7.8))
        im = heatmap_with_text(
            ax, self.ext_pre_mat, self.extended_row_labels, OUTCOME_SHORT,
            vmin=0, vmax=np.nanmax([self.ext_pre_mat.max(), self.ext_post_mat.max()]),
            cmap="YlOrRd", fmt="{:.0f}"
        )
        panel_letter(ax, "e")
        ax.set_title("Pre-RL extended-field medians")
        cbar = fig.colorbar(im, ax=ax, orientation="vertical", fraction=0.04, pad=0.02)
        cbar.set_label("Median")
        fig.tight_layout()
        save_panel(fig, self.out_dir / "fig6e_pre_extended_medians", self.formats)
        return fig

    def generate_fig6f(self):
        fig, ax = plt.subplots(figsize=(7.8, 7.8))
        im = heatmap_with_text(
            ax, self.ext_post_mat, self.extended_row_labels, OUTCOME_SHORT,
            vmin=0, vmax=np.nanmax([self.ext_pre_mat.max(), self.ext_post_mat.max()]),
            cmap="YlOrRd", fmt="{:.0f}"
        )
        panel_letter(ax, "f")
        ax.set_title("Post-RL extended-field medians")
        cbar = fig.colorbar(im, ax=ax, orientation="vertical", fraction=0.04, pad=0.02)
        cbar.set_label("Median")
        fig.tight_layout()
        save_panel(fig, self.out_dir / "fig6f_post_extended_medians", self.formats)
        return fig

    def generate_fig6g(self):
        fig, ax = plt.subplots(figsize=(12.0, 4.6))
        x = np.arange(len(self.g_labels))
        width = 0.18
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
        for idx, out in enumerate(OUTCOME_ORDER):
            bars = ax.bar(x + (idx - 1.5) * width, self.g_mat[:, idx], width,
                          label=OUTCOME_SHORT[idx], color=colors[idx])
            add_bar_labels(ax, bars, fmt="{:.0f}")
        panel_letter(ax, "g")
        ax.set_title("Residual post-RL personality heterogeneity")
        ax.set_xticks(x)
        ax.set_xticklabels(self.g_labels)
        ax.set_ylabel("Median score")
        ax.set_ylim(0, np.nanmax(self.g_mat) + 20)
        ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.18))
        ax.grid(axis="y", alpha=0.2)
        fig.tight_layout()
        save_panel(fig, self.out_dir / "fig6g_post_personality_medians", self.formats)
        return fig

    def generate_combined(self):
        fig = plt.figure(figsize=(16, 20))
        gs = GridSpec(4, 2, figure=fig, height_ratios=[1.05, 1.0, 1.4, 1.2], hspace=0.5, wspace=0.35)
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

        ax = fig.add_subplot(gs[0, 0])
        im = heatmap_with_text(ax, self.pre_exist_m, OUTCOME_SHORT, [FACTOR_EN[s.key] for s in self.existing_specs],
                               vmin=0, vmax=max(self.pre_exist_m.max(), self.post_exist_m.max()),
                               cmap="YlGnBu", fmt="{:.3f}", star_mask=self.pre_exist_p < 0.05)
        panel_letter(ax, "a")
        ax.set_title("Pre-RL effect sizes across existing fields")

        ax = fig.add_subplot(gs[0, 1])
        x = np.arange(len(self.stage_labels))
        width = 0.18
        for idx, out in enumerate(OUTCOME_ORDER):
            bars = ax.bar(x + (idx - 1.5) * width, self.stage_pre[out], width,
                          label=OUTCOME_SHORT[idx], color=colors[idx])
            add_bar_labels(ax, bars, fmt="{:.0f}" if out != "End-of-conversation CCS" else "{:.1f}")
        ax.set_xticks(x)
        ax.set_xticklabels(self.stage_labels)
        ax.set_ylabel("Median score")
        ax.set_ylim(0, max(max(v) for v in self.stage_pre.values()) + 15)
        ax.grid(axis="y", alpha=0.2)
        ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.18))
        ax.set_title("Pre-RL stage I--IV medians")
        panel_letter(ax, "b")

        ax = fig.add_subplot(gs[1, 0])
        x = np.arange(len(self.sel_labels))
        width = 0.34
        bars1 = ax.bar(x - width / 2, self.sel_values["APS"], width, label="APS", color="#1f77b4")
        bars2 = ax.bar(x + width / 2, self.sel_values["CCS/EWS"], width, label="CCS or EWS", color="#ff7f0e")
        add_bar_labels(ax, bars1, fmt="{:.0f}")
        add_bar_labels(ax, bars2, fmt="{:.1f}" if any(v % 1 for v in self.sel_values["CCS/EWS"]) else "{:.0f}")
        for xpos in [1.5, 3.5]:
            ax.axvline(xpos, color="gray", linestyle="--", linewidth=1)
        ax.text(0.5, 1.02, "Education", transform=ax.get_xaxis_transform(), ha="center", fontsize=9, fontweight="bold")
        ax.text(2.5, 1.02, "Personality", transform=ax.get_xaxis_transform(), ha="center", fontsize=9, fontweight="bold")
        ax.text(4.5, 1.02, "Communication style", transform=ax.get_xaxis_transform(), ha="center", fontsize=9, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(self.sel_labels)
        ax.set_ylabel("Median score")
        ax.set_ylim(0, max(max(self.sel_values["APS"]), max(self.sel_values["CCS/EWS"])) + 18)
        ax.grid(axis="y", alpha=0.2)
        ax.legend(loc="upper right")
        ax.set_title("Selected pre-RL subgroup contrasts")
        panel_letter(ax, "c")

        ax = fig.add_subplot(gs[1, 1])
        im2 = heatmap_with_text(ax, self.post_exist_m, OUTCOME_SHORT, [FACTOR_EN[s.key] for s in self.existing_specs],
                                vmin=0, vmax=max(self.pre_exist_m.max(), self.post_exist_m.max()),
                                cmap="YlGnBu", fmt="{:.3f}", star_mask=self.post_exist_p < 0.05)
        panel_letter(ax, "d")
        ax.set_title("Post-RL effect sizes across existing fields")

        ax = fig.add_subplot(gs[2, 0])
        im3 = heatmap_with_text(ax, self.ext_pre_mat, self.extended_row_labels, OUTCOME_SHORT,
                                vmin=0, vmax=np.nanmax([self.ext_pre_mat.max(), self.ext_post_mat.max()]),
                                cmap="YlOrRd", fmt="{:.0f}")
        panel_letter(ax, "e")
        ax.set_title("Pre-RL extended-field medians")

        ax = fig.add_subplot(gs[2, 1])
        im4 = heatmap_with_text(ax, self.ext_post_mat, self.extended_row_labels, OUTCOME_SHORT,
                                vmin=0, vmax=np.nanmax([self.ext_pre_mat.max(), self.ext_post_mat.max()]),
                                cmap="YlOrRd", fmt="{:.0f}")
        panel_letter(ax, "f")
        ax.set_title("Post-RL extended-field medians")

        ax = fig.add_subplot(gs[3, :])
        x = np.arange(len(self.g_labels))
        width = 0.18
        for idx, out in enumerate(OUTCOME_ORDER):
            bars = ax.bar(x + (idx - 1.5) * width, self.g_mat[:, idx], width,
                          label=OUTCOME_SHORT[idx], color=colors[idx])
            add_bar_labels(ax, bars, fmt="{:.0f}")
        ax.set_xticks(x)
        ax.set_xticklabels(self.g_labels)
        ax.set_ylabel("Median score")
        ax.set_ylim(0, np.nanmax(self.g_mat) + 20)
        ax.grid(axis="y", alpha=0.2)
        ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12))
        ax.set_title("Residual post-RL personality heterogeneity")
        panel_letter(ax, "g")

        cax1 = fig.add_axes([0.12, 0.505, 0.32, 0.012])
        cb1 = fig.colorbar(im, cax=cax1, orientation="horizontal")
        cb1.set_label("Effect size", fontsize=8)
        cb1.ax.tick_params(labelsize=7)

        cax2 = fig.add_axes([0.56, 0.275, 0.32, 0.012])
        cb2 = fig.colorbar(im3, cax=cax2, orientation="horizontal")
        cb2.set_label("Median", fontsize=8)
        cb2.ax.tick_params(labelsize=7)

        fig.suptitle("Population-scale subgroup patterns before and after reinforcement learning",
                     y=0.995, fontsize=14, fontweight="bold")
        save_panel(fig, self.out_dir / "fig6_population_patterns_combined", self.formats)
        return fig


def write_results_tex(out_dir: Path):
    results_text = r"""\subsection{Population-scale simulation reveals subgroup patterns}\label{sec_results_population_patterns}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.95\textwidth]{figs/fig6_population_patterns_combined.pdf}
    \caption{}
    \label{fig_6}
\end{figure}

Using simulated consultations between Affective-Cognitive Patient Agents and either the Empathic-Strategic Doctor Agent or the Empathic-Strategic Doctor Agent (RL-Evolved), we analyzed subgroup patterns across 2,500 pre-RL and 2,500 post-RL simulations (Figure~\ref{fig_6}a--g). \\

Before reinforcement learning, existing fields already showed clinically plausible gradients (Figure~\ref{fig_6}a--c). Across stages I--IV, median End-of-conversation APS were 82, 74, 60 and 50, and median End-of-conversation CCS were 80, 72, 60 and 54.5 (Kruskal--Wallis $P = 1.03 \times 10^{-48}$ and $6.82 \times 10^{-46}$; $\varepsilon^2 = 0.089$ and $0.084$, respectively). Median End-of-conversation EWS and Minimum EWS followed the same ordering across stages, with values of 30, 25, 12 and 10, and 15, 15, 12 and 10, respectively ($P = 3.76 \times 10^{-27}$ and $5.41 \times 10^{-19}$; Figure~\ref{fig_6}b). Limited versus Expert education groups showed the same gradient, with median End-of-conversation APS and End-of-conversation CCS of 50 and 52.5 versus 78 and 78, and median End-of-conversation EWS and Minimum EWS of 10 and 10 versus 28 and 15 ($P = 1.34 \times 10^{-30}$, $8.28 \times 10^{-48}$, $1.21 \times 10^{-23}$ and $2.31 \times 10^{-13}$, respectively). Among persona variables, personality traits were particularly prominent before RL: the Anxious and Neutral groups showed median End-of-conversation APS and End-of-conversation EWS of 55 and 10 versus 72 and 25, respectively, and communication style showed a parallel pattern, with the Emotionally Expressive group lagging behind the Composed group on End-of-conversation APS and End-of-conversation EWS (50 and 10 versus 72 and 25; Figure~\ref{fig_6}c). These pre-RL gradients indicate that the simulator captures clinically plausible subgroup patterns. \\

Comparing simulations generated by the pre-RL Doctor Agent and the RL-Evolved Doctor Agent showed that reinforcement learning selectively compressed broad clinical and treatment-linked gradients (Figure~\ref{fig_6}d--f). After RL, stage-associated variation became small: median End-of-conversation APS were 85, 85, 84 and 83, and median End-of-conversation CCS were 85, 85, 85 and 83 across stages I--IV ($P = 3.34 \times 10^{-4}$ and $2.87 \times 10^{-4}$; $\varepsilon^2 = 0.006$ and $0.006$, respectively). Median End-of-conversation EWS were 30, 30, 30 and 30, and median Minimum EWS were 17, 17, 16 and 17 ($P = 7.82 \times 10^{-2}$ and $0.442$; $\varepsilon^2 = 0.002$ and 0, respectively). Accordingly, the stage effect on End-of-conversation APS contracted from $\varepsilon^2 = 0.089$ before RL to $\varepsilon^2 = 0.006$ after RL, and the corresponding End-of-conversation CCS effect contracted from $\varepsilon^2 = 0.084$ to $\varepsilon^2 = 0.006$ (Figure~\ref{fig_6}d). \\

A similar compression was observed in extended fields (Figure~\ref{fig_6}e,f). For systemic therapy involvement, median End-of-conversation APS and End-of-conversation CCS were 70 and 70 without systemic therapy versus 55 and 55 with systemic therapy before RL; after RL, the corresponding medians were 85 and 85 versus 84 and 84. The associated APS and CCS rank-biserial effect sizes shrank from 0.201 and 0.198 before RL to 0.042 and 0.028 after RL (post-RL $P = 0.072$ and $0.240$, respectively). Across the eight extended fields, significant factor-outcome associations decreased from 20 of 32 tests before RL to 9 of 32 after RL. \\

Residual heterogeneity nevertheless remained, and post-RL subgroup variation was dominated by persona rather than disease burden. Personality traits remained the strongest post-RL factor, with median End-of-conversation APS and End-of-conversation CCS ranging from 81.5 to 89 and from 82 to 88, respectively, and median End-of-conversation EWS and Minimum EWS ranging from 28 to 33 and from 15 to 19, respectively ($P = 1.84 \times 10^{-103}$, $1.91 \times 10^{-50}$, $2.50 \times 10^{-29}$ and $1.26 \times 10^{-39}$ for End-of-conversation APS, End-of-conversation CCS, End-of-conversation EWS and Minimum EWS, respectively; End-of-conversation APS $\varepsilon^2 = 0.194$; Figure~\ref{fig_6}g). Education background and communication style also remained detectable after RL, but within markedly narrower ranges than before RL. \\

Taken together, these analyses indicate that reinforcement learning compressed broad communication disparities linked to disease severity and treatment complexity while leaving a more persona-sensitive residual landscape of communication difficulty.
"""
    (out_dir / "results_exp42_population_nc_v7.tex").write_text(results_text, encoding="utf-8")

    figure_tex = r"""\begin{figure}[H]
    \centering
    \includegraphics[width=0.95\textwidth]{figs/fig6_population_patterns_combined.pdf}
    \caption{Population-scale subgroup patterns before and after reinforcement learning. (a) Pre-RL effect sizes across existing fields. (b) Pre-RL stage I--IV medians for End-of-conversation APS, End-of-conversation CCS, End-of-conversation EWS and Minimum EWS. (c) Selected pre-RL contrasts for education background, personality traits and communication style. (d) Post-RL effect sizes across existing fields. (e) Pre-RL extended-field medians. (f) Post-RL extended-field medians. (g) Residual post-RL personality heterogeneity. Asterisks in heatmaps denote raw exploratory $P < 0.05$.}
    \label{fig_6}
\end{figure}
"""
    (out_dir / "figure_population_patterns_abcdefg.tex").write_text(figure_tex, encoding="utf-8")

    legend = """Figure 6 | Population-scale subgroup patterns before and after reinforcement learning.
Panel a shows effect sizes for existing fields before RL; panel d shows the corresponding post-RL effect sizes.
Panel b shows pre-RL stage I–IV medians for End-of-conversation APS, End-of-conversation CCS, End-of-conversation EWS and Minimum EWS.
Panel c shows selected pre-RL subgroup contrasts: education (Limited versus Expert) for APS/CCS, personality traits (Anxious versus Neutral) for APS/End-of-conversation EWS, and communication style (Emotionally Expressive versus Composed) for APS/End-of-conversation EWS.
Panels e and f show extended-field medians before and after RL, respectively, across all four patient-side outcomes.
Panel g shows residual personality heterogeneity after RL.
"""
    (out_dir / "figure_population_patterns_abcdefg_legend.txt").write_text(legend, encoding="utf-8")


def main():
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extract_dir = out_dir / "_extracted_cases"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(args.zip_path) as zf:
        zf.extractall(extract_dir)

    pop = load_module(Path(args.code_path))
    before_df, _ = pop.load_records(extract_dir / "test_qwen3-8b", "before")
    after_df, _ = pop.load_records(extract_dir / "test_qwen3-8b-dpo", "after")
    before_df = add_transformed_outcomes(before_df)
    after_df = add_transformed_outcomes(after_df)

    build_long_excel(pop, before_df, after_df, out_dir / "population_level_medians_long.xlsx")

    builder = FigureBuilder(pop, before_df, after_df, out_dir, args.formats)
    plt.close("all")
    builder.generate_fig6a(); plt.close("all")
    builder.generate_fig6b(); plt.close("all")
    builder.generate_fig6c(); plt.close("all")
    builder.generate_fig6d(); plt.close("all")
    builder.generate_fig6e(); plt.close("all")
    builder.generate_fig6f(); plt.close("all")
    builder.generate_fig6g(); plt.close("all")
    builder.generate_combined(); plt.close("all")

    write_results_tex(out_dir)
    print(f"Outputs written to {out_dir}")


if __name__ == "__main__":
    main()
