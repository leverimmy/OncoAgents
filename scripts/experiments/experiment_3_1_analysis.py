#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
analyze_exp3_rank_alignment.py

新增功能：
- 输出每个 txt 文件、每个维度下：
  - 人类排序字母串（如 ABECD）
  - 智能体排序字母串（如 AEBDC）

输出文件：
1) <out_prefix>.task_level.csv
2) <out_prefix>.summary.json
3) <out_prefix>.agent_rankings_by_txt.csv
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass, asdict
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import kendalltau


# =========================
# 维度名标准化
# =========================
DIM_ALIASES = {
    "诊疗过程信息可理解性": "诊疗过程信息可理解性",
    "信息可理解性": "诊疗过程信息可理解性",
    "维度 1": "诊疗过程信息可理解性",

    "诊疗过程问答合理性": "诊疗过程问答合理性",
    "问答合理性": "诊疗过程问答合理性",
    "维度 2": "诊疗过程问答合理性",

    "诊疗过程人文关怀度": "诊疗过程人文关怀度",
    "人文关怀度": "诊疗过程人文关怀度",
    "维度 3": "诊疗过程人文关怀度",
}

DIM_ORDER = [
    "诊疗过程信息可理解性",
    "诊疗过程问答合理性",
    "诊疗过程人文关怀度",
]

# =========================
# 维度打分规则
# =========================
DEFAULT_SCORE_SPECS: Dict[str, List[str]] = {
    "诊疗过程问答合理性": [
        "scores.judge_doctor_scores.safety_evaluation.inappropriate_assurance_overconfidence_score",
        "scores.judge_doctor_scores.safety_evaluation.risk_concealment_score",
    ],
    "诊疗过程信息可理解性": [
        "scores.judge_doctor_scores.safety_evaluation.evidence_support_consistency_score",
        "scores.judge_doctor_scores.humanity_evaluation.information_comprehensibility_score",
    ],
    "诊疗过程人文关怀度": [
        "scores.judge_doctor_scores.humanity_evaluation.response_quality_score",
        "scores.judge_doctor_scores.humanity_evaluation.respect_nonjudgment_score",
        "scores.judge_doctor_scores.humanity_evaluation.autonomy_support_score",
    ],
}

# =========================
# txt 解析
# =========================
HEADER_RE = re.compile(
    r"^\s*维度\s*(\d+)\s*[（(]\s*([^）)]+?)\s*[）)]\s*[:：]?\s*$"
)
ITEM_RE = re.compile(
    r"^\s*([1-5])\s*[\.\、]?\s*([A-E])\s*:\s*(.+?)\s*$"
)


@dataclass
class TaskResult:
    task_id: str
    case_stem: str
    txt_path: str
    dimension: str
    human_order: List[str]
    agent_order: List[str]
    human_letters: str
    agent_letters: str
    tau: float
    pairwise_concordance: float
    n_pairs: int
    n_agree: int


def canonicalize_dimension_name(name: str) -> str:
    name = name.strip()
    if name in DIM_ALIASES:
        return DIM_ALIASES[name]
    if "信息可理解" in name:
        return "诊疗过程信息可理解性"
    if "问答合理" in name:
        return "诊疗过程问答合理性"
    if "人文关怀" in name:
        return "诊疗过程人文关怀度"
    raise ValueError(f"无法识别的维度名: {name}")


def parse_ranking_txt(txt_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    返回：
    {
      dim: {
        "human_order": [model_rel1, ...],
        "ranked_letters": ["A","E","B","D","C"],   # 依照人类排序后的字母序列
        "model_to_letter": {model_rel: "A"/...},
      }
    }
    """
    text = txt_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    dim_to_items: Dict[str, List[Tuple[int, str, str]]] = {}
    current_dim = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        m_header = HEADER_RE.match(line)
        if m_header:
            dim_name = canonicalize_dimension_name(m_header.group(2))
            current_dim = dim_name
            dim_to_items[current_dim] = []
            continue

        m_item = ITEM_RE.match(line)
        if m_item and current_dim is not None:
            rank = int(m_item.group(1))
            letter = m_item.group(2)
            model_rel = m_item.group(3).strip()
            dim_to_items[current_dim].append((rank, letter, model_rel))

    result: Dict[str, Dict[str, Any]] = {}
    for dim in DIM_ORDER:
        if dim not in dim_to_items:
            raise ValueError(f"{txt_path} 缺少维度：{dim}")
        items = sorted(dim_to_items[dim], key=lambda x: x[0])
        if len(items) != 5:
            raise ValueError(f"{txt_path} 的维度 {dim} 不是 5 个模型，而是 {len(items)} 个")

        human_order = [model_rel for _, _, model_rel in items]
        ranked_letters = [letter for _, letter, _ in items]
        model_to_letter = {model_rel: letter for _, letter, model_rel in items}

        result[dim] = {
            "human_order": human_order,
            "ranked_letters": ranked_letters,
            "model_to_letter": model_to_letter,
        }

    return result


# =========================
# JSON 读取
# =========================
def get_nested_value(obj: Any, dotted_path: str) -> Any:
    cur = obj
    for part in dotted_path.split("."):
        if isinstance(cur, dict):
            if part not in cur:
                raise KeyError(f"找不到字段: {part} (path={dotted_path})")
            cur = cur[part]
        elif isinstance(cur, list):
            idx = int(part)
            cur = cur[idx]
        else:
            raise KeyError(f"中间节点不是 dict/list，无法继续取 path={dotted_path}")
    return cur


def load_agent_dimension_score(json_path: Path, score_spec: List[str]) -> float:
    obj = json.loads(json_path.read_text(encoding="utf-8"))
    vals: List[float] = []
    for dotted_path in score_spec:
        val = get_nested_value(obj, dotted_path)
        if not isinstance(val, (int, float)):
            raise TypeError(f"{json_path} 的 {dotted_path} 不是数值，而是 {type(val)}")
        vals.append(float(val))
    if not vals:
        raise ValueError(f"{json_path} 的 score_spec 为空")
    return float(sum(vals) / len(vals))


# =========================
# 排序辅助
# =========================
def order_to_rank_dict(order: List[str]) -> Dict[str, int]:
    return {model: idx + 1 for idx, model in enumerate(order)}


def order_to_letters(order: List[str], model_to_letter: Dict[str, str]) -> str:
    return "".join(model_to_letter[m] for m in order)


def compute_pairwise_concordance(order1: List[str], order2: List[str]) -> Tuple[float, int, int]:
    r1 = order_to_rank_dict(order1)
    r2 = order_to_rank_dict(order2)

    models = list(order1)
    total = 0
    agree = 0

    for a, b in combinations(models, 2):
        total += 1
        rel1 = r1[a] < r1[b]
        rel2 = r2[a] < r2[b]
        if rel1 == rel2:
            agree += 1

    return agree / total, agree, total


def compute_kendall_tau(order1: List[str], order2: List[str]) -> float:
    models = list(order1)
    r1 = order_to_rank_dict(order1)
    r2 = order_to_rank_dict(order2)

    x = [r1[m] for m in models]
    y = [r2[m] for m in models]

    res = kendalltau(x, y, variant="b")
    return float(res.statistic)


def build_agent_order(
    case_stem: str,
    human_order: List[str],
    agent_root: Path,
    score_spec: List[str],
) -> Tuple[List[str], Dict[str, float]]:
    scores: Dict[str, float] = {}
    for model_rel in human_order:
        json_path = agent_root / model_rel / f"{case_stem}.json"
        if not json_path.exists():
            raise FileNotFoundError(f"找不到智能体结果文件: {json_path}")
        score = load_agent_dimension_score(json_path, score_spec)
        scores[model_rel] = score

    # 不会出现 tie；仍保留稳定排序兜底
    agent_order = sorted(human_order, key=lambda m: (-scores[m], m))
    return agent_order, scores


# =========================
# 收集 task 级结果
# =========================
def collect_task_results(
    input_dir: Path,
    agent_root: Path,
    score_specs: Dict[str, List[str]],
) -> List[TaskResult]:
    txt_files = sorted(input_dir.glob("*/dimension_rankings/*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"在 {input_dir} 下没有找到 */dimension_rankings/*.txt")

    results: List[TaskResult] = []

    for txt_path in txt_files:
        task_id = txt_path.parent.parent.name
        case_stem = txt_path.stem

        dim_info = parse_ranking_txt(txt_path)

        for dim in DIM_ORDER:
            human_order = dim_info[dim]["human_order"]
            model_to_letter = dim_info[dim]["model_to_letter"]
            human_letters = "".join(dim_info[dim]["ranked_letters"])

            if dim not in score_specs:
                raise KeyError(f"score_specs 缺少维度: {dim}")

            agent_order, _ = build_agent_order(
                case_stem=case_stem,
                human_order=human_order,
                agent_root=agent_root,
                score_spec=score_specs[dim],
            )

            agent_letters = order_to_letters(agent_order, model_to_letter)

            tau = compute_kendall_tau(human_order, agent_order)
            concordance, agree, total = compute_pairwise_concordance(human_order, agent_order)

            results.append(
                TaskResult(
                    task_id=task_id,
                    case_stem=case_stem,
                    txt_path=str(txt_path),
                    dimension=dim,
                    human_order=human_order,
                    agent_order=agent_order,
                    human_letters=human_letters,
                    agent_letters=agent_letters,
                    tau=tau,
                    pairwise_concordance=concordance,
                    n_pairs=total,
                    n_agree=agree,
                )
            )

    return results


# =========================
# Bootstrap
# =========================
def bootstrap_mean_ci(
    values: np.ndarray,
    n_resamples: int = 5000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return (math.nan, math.nan, math.nan)

    point = float(values.mean())
    boots = np.empty(n_resamples, dtype=float)

    for i in range(n_resamples):
        sample = rng.choice(values, size=n, replace=True)
        boots[i] = sample.mean()

    alpha = 1.0 - confidence_level
    lo = float(np.quantile(boots, alpha / 2))
    hi = float(np.quantile(boots, 1 - alpha / 2))
    return point, lo, hi


def summarize_results(
    results: List[TaskResult],
    n_bootstrap: int,
    seed: int,
) -> Dict[str, Any]:
    df = pd.DataFrame([asdict(r) for r in results])

    summary: Dict[str, Any] = {
        "n_tasks": int(len(df)),
        "overall": {},
        "by_dimension": {},
    }

    tau_point, tau_lo, tau_hi = bootstrap_mean_ci(
        df["tau"].to_numpy(),
        n_resamples=n_bootstrap,
        seed=seed,
    )
    pc_point, pc_lo, pc_hi = bootstrap_mean_ci(
        df["pairwise_concordance"].to_numpy(),
        n_resamples=n_bootstrap,
        seed=seed + 1,
    )

    summary["overall"] = {
        "macro_average_tau": tau_point,
        "tau_95ci_low": tau_lo,
        "tau_95ci_high": tau_hi,
        "macro_average_pairwise_concordance": pc_point,
        "pairwise_concordance_95ci_low": pc_lo,
        "pairwise_concordance_95ci_high": pc_hi,
    }

    for i, dim in enumerate(DIM_ORDER):
        sub = df[df["dimension"] == dim]
        tau_point, tau_lo, tau_hi = bootstrap_mean_ci(
            sub["tau"].to_numpy(),
            n_resamples=n_bootstrap,
            seed=seed + 10 + i,
        )
        pc_point, pc_lo, pc_hi = bootstrap_mean_ci(
            sub["pairwise_concordance"].to_numpy(),
            n_resamples=n_bootstrap,
            seed=seed + 20 + i,
        )
        summary["by_dimension"][dim] = {
            "n_tasks": int(len(sub)),
            "macro_average_tau": tau_point,
            "tau_95ci_low": tau_lo,
            "tau_95ci_high": tau_hi,
            "macro_average_pairwise_concordance": pc_point,
            "pairwise_concordance_95ci_low": pc_lo,
            "pairwise_concordance_95ci_high": pc_hi,
        }

    return summary


def build_agent_rankings_by_txt(results: List[TaskResult]) -> pd.DataFrame:
    """
    输出每个 txt 文件在三个维度下的人类/智能体字母排序
    """
    df = pd.DataFrame([asdict(r) for r in results])

    base_cols = ["task_id", "case_stem", "txt_path"]

    out = (
        df[base_cols + ["dimension", "human_letters", "agent_letters"]]
        .drop_duplicates()
        .copy()
    )

    human_pivot = out.pivot_table(
        index=base_cols,
        columns="dimension",
        values="human_letters",
        aggfunc="first",
    )
    human_pivot.columns = [f"{c}_human" for c in human_pivot.columns]

    agent_pivot = out.pivot_table(
        index=base_cols,
        columns="dimension",
        values="agent_letters",
        aggfunc="first",
    )
    agent_pivot.columns = [f"{c}_agent" for c in agent_pivot.columns]

    merged = pd.concat([human_pivot, agent_pivot], axis=1).reset_index()

    ordered_cols = base_cols[:]
    for dim in DIM_ORDER:
        ordered_cols.append(f"{dim}_human")
        ordered_cols.append(f"{dim}_agent")

    existing_cols = [c for c in ordered_cols if c in merged.columns]
    return merged[existing_cols].sort_values(["task_id", "case_stem"]).reset_index(drop=True)


def print_summary(summary: Dict[str, Any]) -> None:
    print("=" * 80)
    print("OVERALL")
    print(f"n_tasks = {summary['n_tasks']}")
    ov = summary["overall"]
    print(
        f"Kendall's tau = {ov['macro_average_tau']:.4f} "
        f"[{ov['tau_95ci_low']:.4f}, {ov['tau_95ci_high']:.4f}]"
    )
    print(
        f"Pairwise concordance = {ov['macro_average_pairwise_concordance']:.4f} "
        f"[{ov['pairwise_concordance_95ci_low']:.4f}, "
        f"{ov['pairwise_concordance_95ci_high']:.4f}]"
    )

    print("\n" + "=" * 80)
    print("BY DIMENSION")
    for dim, vals in summary["by_dimension"].items():
        print(f"\n[{dim}]  n_tasks = {vals['n_tasks']}")
        print(
            f"  Kendall's tau = {vals['macro_average_tau']:.4f} "
            f"[{vals['tau_95ci_low']:.4f}, {vals['tau_95ci_high']:.4f}]"
        )
        print(
            f"  Pairwise concordance = {vals['macro_average_pairwise_concordance']:.4f} "
            f"[{vals['pairwise_concordance_95ci_low']:.4f}, "
            f"{vals['pairwise_concordance_95ci_high']:.4f}]"
        )
    print("=" * 80)


def load_score_specs(score_specs_arg: str | None) -> Dict[str, List[str]]:
    if score_specs_arg is None:
        return DEFAULT_SCORE_SPECS.copy()

    maybe_path = Path(score_specs_arg)
    if maybe_path.exists():
        return json.loads(maybe_path.read_text(encoding="utf-8"))

    return json.loads(score_specs_arg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=Path, required=True, help="exp3 根目录")
    parser.add_argument("--agent_root", type=Path, required=True, help="智能体 json 根目录")
    parser.add_argument(
        "--score_specs",
        type=str,
        default=None,
        help=(
            "维度->多个 JSON dotted path 的映射，最终取均值。"
            "可传 JSON 字符串，也可传一个 JSON 文件路径。"
        ),
    )
    parser.add_argument("--n_bootstrap", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out_prefix", type=str, default="exp3_rank_alignment")
    args = parser.parse_args()

    score_specs = load_score_specs(args.score_specs)
    score_specs = {
        canonicalize_dimension_name(k): v
        for k, v in score_specs.items()
    }

    results = collect_task_results(
        input_dir=args.input_dir,
        agent_root=args.agent_root,
        score_specs=score_specs,
    )

    summary = summarize_results(
        results=results,
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
    )

    # task-level csv
    df_task = pd.DataFrame([asdict(r) for r in results])
    csv_task = Path(f"{args.out_prefix}.task_level.csv")
    df_task.to_csv(csv_task, index=False, encoding="utf-8-sig")

    # summary json
    json_path = Path(f"{args.out_prefix}.summary.json")
    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 每个 txt 文件的三个维度字母排序
    df_letters = build_agent_rankings_by_txt(results)
    csv_letters = Path(f"{args.out_prefix}.agent_rankings_by_txt.csv")
    df_letters.to_csv(csv_letters, index=False, encoding="utf-8-sig")

    print_summary(summary)
    print(f"\n[Saved] task-level CSV: {csv_task}")
    print(f"[Saved] summary JSON:  {json_path}")
    print(f"[Saved] letter-rank CSV: {csv_letters}")


if __name__ == "__main__":
    main()