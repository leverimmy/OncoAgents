import os
import json
import math
import pickle
import re
import heapq
import warnings
from collections import defaultdict
from typing import Dict, Any, List, Tuple

import os
from dotenv import load_dotenv

load_dotenv()

import numpy as np
import faiss
import torch
from sentence_transformers import SentenceTransformer

warnings.filterwarnings("ignore", message=r"pkg_resources is deprecated as an API.*")



KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "knowledge")
BM25_SUBDIR   = os.getenv("BM25_SUBDIR", "chunks")
DENSE_SUBDIR  = os.getenv("DENSE_SUBDIR", "dense")

BM25_DIR  = os.path.join(KNOWLEDGE_DIR, BM25_SUBDIR)
DENSE_DIR = os.path.join(KNOWLEDGE_DIR, DENSE_SUBDIR)

# ===== BM25 files =====
BM25_CONTENT_INDEX = os.path.join(BM25_DIR, "bm25_index.pkl")
BM25_CONTENT_DOCS  = os.path.join(BM25_DIR, "bm25_docs.pkl")
BM25_CONTENT_CONF  = os.path.join(BM25_DIR, "bm25_config.json")

BM25_SPMC_INDEX = os.path.join(BM25_DIR, "bm25_index_spmc.pkl")
BM25_SPMC_DOCS  = os.path.join(BM25_DIR, "bm25_docs_spmc.pkl")
BM25_SPMC_CONF  = os.path.join(BM25_DIR, "bm25_config_spmc.json")

# ===== Dense files =====
DENSE_META      = os.path.join(DENSE_DIR, "dense_meta.pkl")
DENSE_CHUNK_IDS = os.path.join(DENSE_DIR, "chunk_ids.npy")
DENSE_CONF      = os.path.join(DENSE_DIR, "dense_config.json")


FIELDS = ["subject", "chapter", "part", "main_row", "content"]
DENSE_IDX_FILES = {f: os.path.join(DENSE_DIR, f"faiss_{f}.index") for f in FIELDS}

# =========================
# 检索参数
# =========================
# BM25：content 与标题（spmc）融合权重
BM25_W_CONTENT = 1.0
BM25_W_TITLE = 2.0

# Dense：最终输出的 dense topk
DENSE_TOPK = 30

# BM25：最终输出的 bm25 topk
BM25_TOPK = 50

# 最终 topk
FINAL_TOPK = 3

# 最终过滤：content 至少包含多少汉字
MIN_HAN_IN_CONTENT = 5

# 融合：RRF
RRF_K = 60
W_BM25 = 1.0
W_DENSE = 1.2

# 可选：增加少量“原始分数归一化 bonus”
BONUS_BM25 = 0.20
BONUS_DENSE = 0.20


try:
    import jieba
    JIEBA_OK = True
except Exception:
    JIEBA_OK = False

TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+")
HAN_RE = re.compile(r"[\u4e00-\u9fff]")
WS_RE = re.compile(r"\s+")


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u00a0", " ")
    s = s.replace("\ufeff", "")
    s = s.replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def tokenize(text: str) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []
    pieces = TOKEN_RE.findall(text)
    tokens: List[str] = []
    for p in pieces:
        if any("\u4e00" <= ch <= "\u9fff" for ch in p):
            if JIEBA_OK:
                tokens.extend([t.strip() for t in jieba.lcut(p) if t.strip()])
            else:
                tokens.extend([ch for ch in p if "\u4e00" <= ch <= "\u9fff"])
        else:
            tokens.append(p.lower())
    tokens = [t for t in tokens if len(t) >= 1]
    return tokens


def count_chinese_chars(text: str) -> int:
    if not text:
        return 0
    return len(HAN_RE.findall(text))


def valid_content(text: str, min_han: int = MIN_HAN_IN_CONTENT) -> bool:
    return count_chinese_chars(text) >= min_han


def preview30(text: str) -> str:
    text = text or ""
    return WS_RE.sub(" ", text).strip()[:30]


def rrf(rank: int, k: int = RRF_K) -> float:
    return 1.0 / (k + rank)


# =========================
# BM25 部分
# =========================
def load_bm25_bundle(index_path: str, docs_path: str, conf_path: str) -> Dict[str, Any]:
    with open(index_path, "rb") as f:
        index = pickle.load(f)
    with open(docs_path, "rb") as f:
        docs = pickle.load(f)
    with open(conf_path, "r", encoding="utf-8") as f:
        conf = json.load(f)

    bundle = {
        "index": index,
        "docs": docs,
        "k1": float(conf.get("k1", 1.5)),
        "b": float(conf.get("b", 0.75)),
        "N": int(index["N"]),
        "avgdl": float(index["avgdl"]),
        "df": index["df"],              # dict term->df
        "postings": index["postings"],  # dict term->[(doc_idx, tf), ...]
        "doc_len": index["doc_len"],    # list doc_idx->len(tokens)
    }

    chunkid_to_docidx = {}
    for doc_idx, obj in enumerate(docs):
        cid = obj.get("chunk_id")
        if cid is not None:
            chunkid_to_docidx[int(cid)] = doc_idx
    bundle["chunkid_to_docidx"] = chunkid_to_docidx
    return bundle


def bm25_scores_for_bundle(bundle: Dict[str, Any], query: str) -> Dict[int, float]:
    N = bundle["N"]
    avgdl = bundle["avgdl"]
    df = bundle["df"]
    postings = bundle["postings"]
    doc_len = bundle["doc_len"]
    k1 = bundle["k1"]
    b = bundle["b"]
    docs = bundle["docs"]

    q_tokens = tokenize(query)
    if not q_tokens:
        return {}

    scores_docidx = defaultdict(float)

    for term in set(q_tokens):
        dfi = df.get(term, 0)
        if dfi <= 0:
            continue
        idf = math.log(1.0 + (N - dfi + 0.5) / (dfi + 0.5))

        plist = postings.get(term, [])
        for doc_idx, tf in plist:
            dl = doc_len[doc_idx]
            denom = tf + k1 * (1.0 - b + b * (dl / avgdl if avgdl > 0 else 0.0))
            score = idf * (tf * (k1 + 1.0)) / (denom if denom != 0 else 1.0)
            scores_docidx[doc_idx] += score

    chunkid_to_score = {}
    for doc_idx, sc in scores_docidx.items():
        cid = docs[doc_idx].get("chunk_id")
        if cid is None:
            continue
        chunkid_to_score[int(cid)] = float(sc)

    return chunkid_to_score


def bm25_search_weighted(query: str,
                         top_k: int,
                         content_bundle: Dict[str, Any],
                         spmc_bundle: Dict[str, Any],
                         w_content: float = BM25_W_CONTENT,
                         w_title: float = BM25_W_TITLE) -> List[Dict[str, Any]]:
    content_scores = bm25_scores_for_bundle(content_bundle, query)
    spmc_scores = bm25_scores_for_bundle(spmc_bundle, query)
    all_cids = set(content_scores.keys()) | set(spmc_scores.keys())
    if not all_cids:
        return []

    fused = []
    for cid in all_cids:
        sc_content = content_scores.get(cid, 0.0)
        sc_title = spmc_scores.get(cid, 0.0)
        fused_score = w_content * sc_content + w_title * sc_title
        fused.append((cid, fused_score, sc_content, sc_title))

    top = heapq.nlargest(top_k, fused, key=lambda x: x[1])

    results = []
    content_map = content_bundle["chunkid_to_docidx"]
    spmc_map = spmc_bundle["chunkid_to_docidx"]

    for cid, fused_score, sc_content, sc_title in top:
        if cid in content_map:
            obj = content_bundle["docs"][content_map[cid]]
        elif cid in spmc_map:
            obj = spmc_bundle["docs"][spmc_map[cid]]
        else:
            continue

        out = dict(obj)
        out["score_bm25"] = float(fused_score)
        out["score_bm25_content"] = float(sc_content)
        out["score_bm25_title"] = float(sc_title)
        results.append(out)

    return results


# =========================
# Dense 部分
# =========================
def l2_normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v) + 1e-12
    return v / n


def load_dense_all():
    with open(DENSE_META, "rb") as f:
        meta = pickle.load(f)
    chunk_ids = np.load(DENSE_CHUNK_IDS).astype(np.int32)

    with open(DENSE_CONF, "r", encoding="utf-8") as f:
        conf = json.load(f)

    model_name = conf["model_name"]
    weights = conf.get("weights_default", {})
    topk_per_field = int(conf.get("topk_per_field_default", 200))

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Dense ST device = {device}")
    if device == "cuda":
        print(f"[INFO] GPU = {torch.cuda.get_device_name(0)}")

    model = SentenceTransformer(model_name, device=device)
    indexes = {f: faiss.read_index(DENSE_IDX_FILES[f]) for f in FIELDS}
    chunkid_to_docidx = {int(c.get("chunk_id")): i for i, c in enumerate(meta)}

    return meta, chunk_ids, chunkid_to_docidx, model, indexes, weights, topk_per_field


def dense_search(query: str,
                 meta: List[Dict[str, Any]],
                 chunk_ids: np.ndarray,
                 chunkid_to_docidx: Dict[int, int],
                 model: SentenceTransformer,
                 indexes: Dict[str, faiss.Index],
                 weights: Dict[str, float],
                 topk_per_field: int = 200,
                 top_k_final: int = 30,
                 min_han_in_content: int = MIN_HAN_IN_CONTENT) -> List[Dict[str, Any]]:

    query = normalize_text(query)
    if not query:
        return []

    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=False).astype(np.float32)[0]
    q_emb = l2_normalize(q_emb).reshape(1, -1)

    score_sum: Dict[int, float] = {}
    per_field: Dict[int, Dict[str, float]] = {}

    for f, index in indexes.items():
        w = float(weights.get(f, 1.0))
        sims, idxs = index.search(q_emb, topk_per_field)
        sims = sims[0]
        idxs = idxs[0]

        for sim, doc_idx in zip(sims, idxs):
            if doc_idx < 0:
                continue
            cid = int(chunk_ids[doc_idx])
            contrib = w * float(sim)
            score_sum[cid] = score_sum.get(cid, 0.0) + contrib
            per_field.setdefault(cid, {})[f] = float(sim)

    if not score_sum:
        return []

    ranked = sorted(score_sum.items(), key=lambda x: x[1], reverse=True)
    ranked = ranked[: max(top_k_final * 20, top_k_final)]

    results = []
    for cid, sc in ranked:
        doc_idx = chunkid_to_docidx.get(cid)
        if doc_idx is None:
            continue
        obj = meta[doc_idx]
        content = obj.get("content", "") or ""
        if not valid_content(content, min_han=min_han_in_content):
            continue

        out = dict(obj)
        out["score_dense"] = float(sc)
        out["field_sims"] = per_field.get(cid, {})
        results.append(out)

        if len(results) >= top_k_final:
            break

    return results


# =========================
# Hybrid 融合 + 输出给 Agent
# =========================
def format_for_agent(item: Dict[str, Any], rank: int) -> str:
    """
    输出一段可以直接喂给 agent 的文本块：
    - 标题信息（subject/chapter/part/main_row）
    - chunk_id、len
    - content 全量
    """
    cid = item.get("chunk_id")
    ln = item.get("len")
    subject = item.get("subject")
    chapter = item.get("chapter")
    part = item.get("part")
    main_row = item.get("main_row")
    content = (item.get("content", "") or "").strip()

    score_h = item.get("score_hybrid", 0.0)
    sb = item.get("score_bm25", 0.0)
    sd = item.get("score_dense", 0.0)
    rb = item.get("rank_bm25")
    rd = item.get("rank_dense")

    header = (
        f"[{rank}] chunk_id={cid} len={ln}\n"
        f"HybridScore={score_h:.4f} | BM25={sb:.4f}(r{rb}) | Dense={sd:.4f}(r{rd})\n"
        f"subject: {subject}\n"
        f"chapter: {chapter}\n"
        f"part: {part}\n"
        f"main_row: {main_row}\n"
    )
    return header + "content:\n" + content + "\n"


def hybrid_search(query: str,
                  bm25_content_bundle: Dict[str, Any],
                  bm25_spmc_bundle: Dict[str, Any],
                  dense_state: Tuple,
                  bm25_topk: int = BM25_TOPK,
                  dense_topk: int = DENSE_TOPK,
                  final_topk: int = FINAL_TOPK) -> List[Dict[str, Any]]:
    meta, chunk_ids, chunkid_to_docidx, model, indexes, dweights, topk_per_field = dense_state

    # 1) BM25 top50
    bm25_res = bm25_search_weighted(
        query,
        top_k=bm25_topk,
        content_bundle=bm25_content_bundle,
        spmc_bundle=bm25_spmc_bundle,
        w_content=BM25_W_CONTENT,
        w_title=BM25_W_TITLE
    )

    # 2) Dense top30
    dense_res = dense_search(
        query,
        meta, chunk_ids, chunkid_to_docidx,
        model, indexes, dweights,
        topk_per_field=topk_per_field,
        top_k_final=dense_topk,
        min_han_in_content=MIN_HAN_IN_CONTENT
    )

    # 3) 建 rank / score 映射
    bm25_rank, bm25_score = {}, {}
    for i, r in enumerate(bm25_res, 1):
        cid = r.get("chunk_id")
        if cid is None:
            continue
        cid = int(cid)
        bm25_rank[cid] = i
        bm25_score[cid] = float(r.get("score_bm25", 0.0))

    dense_rank, dense_score = {}, {}
    for i, r in enumerate(dense_res, 1):
        cid = r.get("chunk_id")
        if cid is None:
            continue
        cid = int(cid)
        dense_rank[cid] = i
        dense_score[cid] = float(r.get("score_dense", 0.0))

    all_cids = set(bm25_rank.keys()) | set(dense_rank.keys())
    if not all_cids:
        return []

    bm25_max = max(bm25_score.values()) if bm25_score else 0.0
    dense_max = max(dense_score.values()) if dense_score else 0.0

    # 4) 融合打分（RRF + bonus）
    fused_list = []
    for cid in all_cids:
        rb = bm25_rank.get(cid)
        rd = dense_rank.get(cid)

        s = 0.0
        if rb is not None:
            s += W_BM25 * rrf(rb, RRF_K)
            if bm25_max > 0:
                s += BONUS_BM25 * (bm25_score.get(cid, 0.0) / bm25_max)

        if rd is not None:
            s += W_DENSE * rrf(rd, RRF_K)
            if dense_max > 0:
                s += BONUS_DENSE * (dense_score.get(cid, 0.0) / dense_max)

        fused_list.append((cid, s))

    fused_list.sort(key=lambda x: x[1], reverse=True)

    # 5) 从 dense_meta / bm25_docs 取回完整 obj，并过滤 content
    dense_obj_map = {int(obj.get("chunk_id")): obj for obj in meta}

    bm25_obj_map = {}
    for obj in bm25_content_bundle["docs"]:
        cid = obj.get("chunk_id")
        if cid is not None:
            bm25_obj_map[int(cid)] = obj
    for obj in bm25_spmc_bundle["docs"]:
        cid = obj.get("chunk_id")
        if cid is not None:
            bm25_obj_map[int(cid)] = obj

    final = []
    for cid, sc_h in fused_list:
        obj = dense_obj_map.get(cid) or bm25_obj_map.get(cid)
        if not obj:
            continue
        content = obj.get("content", "") or ""
        if not valid_content(content, min_han=MIN_HAN_IN_CONTENT):
            continue

        out = dict(obj)
        out["score_hybrid"] = float(sc_h)
        out["rank_bm25"] = bm25_rank.get(cid)
        out["rank_dense"] = dense_rank.get(cid)
        out["score_bm25"] = float(bm25_score.get(cid, 0.0))
        out["score_dense"] = float(dense_score.get(cid, 0.0))
        final.append(out)

        if len(final) >= final_topk:
            break

    return final

_HYBRID_STATE = {
    "ready": False,
    "bm25_content_bundle": None,
    "bm25_spmc_bundle": None,
    "dense_state": None,
}

def _ensure_hybrid_state_loaded():
    global _HYBRID_STATE

    if _HYBRID_STATE["ready"]:
        return

    # BM25
    bm25_content_bundle = load_bm25_bundle(BM25_CONTENT_INDEX, BM25_CONTENT_DOCS, BM25_CONTENT_CONF)
    bm25_spmc_bundle = load_bm25_bundle(BM25_SPMC_INDEX, BM25_SPMC_DOCS, BM25_SPMC_CONF)

    # Dense
    dense_state = load_dense_all()

    _HYBRID_STATE["bm25_content_bundle"] = bm25_content_bundle
    _HYBRID_STATE["bm25_spmc_bundle"] = bm25_spmc_bundle
    _HYBRID_STATE["dense_state"] = dense_state
    _HYBRID_STATE["ready"] = True


def hybrid_search_answer(query: str) -> list[dict[str, int | str]]:
    """
    在医学指南中对某个知识进行检索，并返回一个 list[dict[str, int | str]] 结果给 Agent。

    Args:
        query (str): 想要检索的内容、名称、关键词
    
    Returns:
        list[dict[str, int | str]]: 检索结果的列表，每个元素包含以下字段：
            - chunk_id (int): 证据块的唯一标识符
            - len (int): 证据块内容的长度（字符数）
            - specialty (str): 证据块所属的专业领域
            - subject (str): 证据块所属的学科
            - chapter (str): 证据块所属的章节
            - part (str): 证据块所属的部分
            - main_row (str): 证据块的主要行信息
            - content (str): 证据块的全文内容
            - score_hybrid (float): 融合后的检索得分
            - rank_bm25 (int): 在 BM25 检索中的排名
            - rank_dense (int): 在 Dense 检索中的排名
            - score_bm25 (float): 在 BM25 检索中的得分
            - score_dense (float): 在 Dense 检索中的得分
            - rank (int): 在最终融合结果中的排名
            - query (str): 用户的检索查询内容
    """
    final_topk = FINAL_TOPK
    bm25_topk = BM25_TOPK
    dense_topk = DENSE_TOPK
    query = (query or "").strip()
    print("[TOOL] hybrid_search_answer_tool called with query:", query)
    if not query:
        return []

    _ensure_hybrid_state_loaded()

    final = hybrid_search(
        query,
        bm25_content_bundle=_HYBRID_STATE["bm25_content_bundle"],
        bm25_spmc_bundle=_HYBRID_STATE["bm25_spmc_bundle"],
        dense_state=_HYBRID_STATE["dense_state"],
        bm25_topk=bm25_topk,
        dense_topk=dense_topk,
        final_topk=final_topk
    )

    if not final:
        return []

    out_list: List[Dict[str, Any]] = []
    for rank, item in enumerate(final, 1):
        obj = dict(item)

        obj["rank"] = int(rank)
        obj["query"] = query

        for k in ["chunk_id", "len", "rank_bm25", "rank_dense"]:
            if k in obj and obj[k] is not None:
                try:
                    obj[k] = int(obj[k])
                except Exception:
                    pass

        for k in ["score_hybrid", "score_bm25", "score_bm25_content", "score_bm25_title", "score_dense"]:
            if k in obj and obj[k] is not None:
                try:
                    obj[k] = float(obj[k])
                except Exception:
                    pass

        fs = obj.get("field_sims")
        if isinstance(fs, dict):
            obj["field_sims"] = {str(f): float(v) for f, v in fs.items()}

        out_list.append(obj)
    print("[TOOL] hybrid_search_answer_tool returned: ", out_list)

    return out_list


def main():
    # ---- load bm25
    if not (os.path.exists(BM25_CONTENT_INDEX) and os.path.exists(BM25_SPMC_INDEX)):
        raise FileNotFoundError("BM25 索引文件不存在，请先构建 bm25_index.pkl 与 bm25_index_spmc.pkl")

    bm25_content_bundle = load_bm25_bundle(BM25_CONTENT_INDEX, BM25_CONTENT_DOCS, BM25_CONTENT_CONF)
    bm25_spmc_bundle = load_bm25_bundle(BM25_SPMC_INDEX, BM25_SPMC_DOCS, BM25_SPMC_CONF)

    print("[OK] BM25 loaded")
    print(f"- content: N={bm25_content_bundle['N']} avgdl={bm25_content_bundle['avgdl']:.2f} vocab={len(bm25_content_bundle['df'])}")
    print(f"- spmc   : N={bm25_spmc_bundle['N']} avgdl={bm25_spmc_bundle['avgdl']:.2f} vocab={len(bm25_spmc_bundle['df'])}")
    print(f"- bm25 weights: content={BM25_W_CONTENT} title={BM25_W_TITLE}")

    # ---- load dense
    if not (os.path.exists(DENSE_META) and os.path.exists(DENSE_CONF)):
        raise FileNotFoundError("Dense 索引文件不存在，请先运行 densebuild.py 构建 ../knowledge/dense 下的文件")

    dense_state = load_dense_all()
    meta, _, _, model, _, dweights, topk_per_field = dense_state

    print("[OK] Dense loaded")
    print(f"- model: {model}")
    print(f"- dense weights: {dweights}")
    print(f"- topk_per_field: {topk_per_field}")
    print(f"- dense topk: {DENSE_TOPK}")
    print(f"- bm25 topk: {BM25_TOPK}")
    print(f"- final topk: {FINAL_TOPK}")
    print(f"- content filter: >= {MIN_HAN_IN_CONTENT} Chinese chars")

    while True:
        q = input("\n请输入 query（回车退出）：").strip()
        if not q:
            break

        final = hybrid_search(
            q,
            bm25_content_bundle=bm25_content_bundle,
            bm25_spmc_bundle=bm25_spmc_bundle,
            dense_state=dense_state,
            bm25_topk=BM25_TOPK,
            dense_topk=DENSE_TOPK,
            final_topk=FINAL_TOPK
        )

        if not final:
            print("\n[WARN] no results.")
            continue

        # ====== 控制台调试输出
        print(f"\nHybrid Top {len(final)} results:")
        for i, r in enumerate(final, 1):
            cid = r.get("chunk_id")
            sc_h = r.get("score_hybrid", 0.0)
            sc_b = r.get("score_bm25", 0.0)
            sc_d = r.get("score_dense", 0.0)
            rb = r.get("rank_bm25")
            rd = r.get("rank_dense")
            pre = preview30(r.get("content", ""))
            print(f"{i:02d}. hybrid={sc_h:.4f} bm25={sc_b:.4f}(r{rb}) dense={sc_d:.4f}(r{rd}) chunk_id={cid} preview='{pre}'")

        # ====== 给 Agent 的文本
        agent_text = "\n" + ("=" * 80) + "\n"
        agent_text += f"QUERY: {q}\n"
        agent_text += ("=" * 80) + "\n\n"
        for i, item in enumerate(final, 1):
            agent_text += format_for_agent(item, i)
            agent_text += "\n" + ("-" * 80) + "\n\n"

        print("\n========== BELOW IS READY-TO-FEED AGENT TEXT ==========")
        print(agent_text)


if __name__ == "__main__":
    # main()
    print(hybrid_search_answer(input("Query: ")))
