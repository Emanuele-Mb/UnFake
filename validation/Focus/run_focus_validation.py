import asyncio
import json
import re
import sys
from pathlib import Path
import pandas as pd

VALIDATION_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = VALIDATION_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from headline_analyst.utils.config_loader import load_config
from headline_analyst.data import Article, Analysis
from headline_analyst.analyzer.framing_analysis import llm_framing_analysis

BENCHMARK_CSV = VALIDATION_DIR / "datasets" / "gvfc_focus_clean.csv"
RESULTS_JSON = Path(__file__).resolve().parent / "results_focus.json"

FOCUS_DEFINITIONS = {
    "Economic": "Framed around financial cost, trade, economic growth, or fiscal impact.",
    "Resources": "Centered on natural resources, energy, land, or supply chains.",
    "Morality": "Raises ethical questions, values, or moral judgements.",
    "Fairness": "Concerns justice, equality, rights, or distribution of outcomes.",
    "Legal": "Involves legislation, regulation, court decisions, or legal accountability.",
    "Policy": "Discusses government decisions, public policy, or institutional action.",
    "Crime": "Relates to criminal activity, law enforcement, or public order.",
    "Security": "Covers threats, conflict, military action, or national security.",
    "Health": "Focuses on physical or mental health, medicine, or epidemiology.",
    "Quality of Life": "Addresses quality of life, wellbeing, housing, or social conditions.",
    "Cultural Identity": "Touches on cultural values, identity, religion, or social cohesion.",
    "Public Opinion": "Highlights polls, popular sentiment, or public reaction.",
    "Political": "Centers on electoral dynamics, party politics, or power relations.",
    "Other": "Headline does not clearly fit a standard category for focus.",
}

ALL_FOCUS_CATEGORIES = list(FOCUS_DEFINITIONS.keys())

NORMALIZE_FOCUS = {
    re.sub(r"[\s_-]+", " ", cat).strip().lower(): cat
    for cat in ALL_FOCUS_CATEGORIES
}


def normalize_focus_list(raw_focus: list) -> list[str]:
    """Converts model focus outputs (Enums or strings) into the 14 canonical categories.

    Any unrecognized non-empty category label is mapped to 'Other'.
    """
    normalized = []
    for item in raw_focus or []:
        raw_str = item.name if hasattr(item, "name") else str(item)
        key = re.sub(r"[\s_-]+", " ", raw_str).strip().lower()
        if not key or key in {"none", "nan", "null"}:
            continue
        canonical = NORMALIZE_FOCUS.get(key, "Other")
        if canonical not in normalized:
            normalized.append(canonical)
    return normalized


async def evaluate_focus(df: pd.DataFrame, llm_config: dict, batch_size: int = 15, pause: float = 2.0) -> list[dict]:
    """Runs the LLM framing analyzer in batches on GVFC headlines and collects focus predictions."""
    records = df.to_dict(orient="records")
    outputs = []

    for start in range(0, len(records), batch_size):
        batch_rows = records[start : start + batch_size]
        articles = [
            Article(
                title=r["headline"],
                source="gvfc",
                query_origin=str(r["headline_id"]),
            )
            for r in batch_rows
        ]

        print(f"  Batch {start + 1}-{start + len(batch_rows)} of {len(records)}...")
        try:
            analyses: list[Analysis] = await llm_framing_analysis(llm_config, articles)
            for row, analysis in zip(batch_rows, analyses):
                raw_focus = getattr(analysis, "focus", None) or getattr(analysis, "focus_areas", [])
                predicted = normalize_focus_list(raw_focus)
                outputs.append({
                    **row,
                    "predicted_focus": predicted,
                    "tone_intensity": analysis.tone_intensity,
                })
        except Exception as e:
            print(f"  [ERROR] Batch skipped: {e}")

        if start + batch_size < len(records):
            await asyncio.sleep(pause)

    return outputs


def print_metrics(results: list[dict]):
    """Computes and displays per-category Precision, Recall, F1 across all 14 Focus categories."""
    print("\n" + "=" * 72)
    print(f"{'CATEGORY':20s} | {'PREC':>6s} | {'REC':>6s} | {'F1':>6s} | {'SUPP':>5s} | {'FP':>4s}")
    print("-" * 72)

    tot_tp = tot_fp = tot_fn = 0
    precisions, recalls, f1s = [], [], []

    for cat in ALL_FOCUS_CATEGORIES:
        tp = fp = fn = 0
        for row in results:
            exp_set = {
                NORMALIZE_FOCUS.get(re.sub(r"[\s_-]+", " ", x).strip().lower(), "Other")
                for x in str(row["expected_focus"]).split("|")
                if x.strip()
            }
            pred_set = set(row["predicted_focus"])

            is_true = cat in exp_set
            is_pred = cat in pred_set

            if is_true and is_pred:
                tp += 1
            elif not is_true and is_pred:
                fp += 1
            elif is_true and not is_pred:
                fn += 1

        support = tp + fn
        tot_tp += tp
        tot_fp += fp
        tot_fn += fn

        if support == 0:
            print(f"{cat:20s} | {'N/A':>6s} | {'N/A':>6s} | {'N/A':>6s} | {support:5d} | {fp:4d}")
            continue

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

        print(f"{cat:20s} | {precision:6.2%} | {recall:6.2%} | {f1:6.2%} | {support:5d} | {fp:4d}")

    macro_p = sum(precisions) / len(precisions) if precisions else 0.0
    macro_r = sum(recalls) / len(recalls) if recalls else 0.0
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    micro_p = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) > 0 else 0.0
    micro_r = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) > 0 else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

    print("-" * 72)
    print(f"{'Macro Avg':20s} | {macro_p:6.2%} | {macro_r:6.2%} | {macro_f1:6.2%} | {'-':>5s} | {'-':>4s}")
    print(f"{'Micro Avg':20s} | {micro_p:6.2%} | {micro_r:6.2%} | {micro_f1:6.2%} | {tot_tp + tot_fn:5d} | {tot_fp:4d}")
    print("=" * 72)

    # Share of headlines where at least one predicted focus (up to 2) matches a ground-truth label
    any_match = sum(
        1 for r in results
        if set(r["predicted_focus"]).intersection(str(r["expected_focus"]).split("|"))
    )
    if results:
        print(f"Any-Match Rate (Hit@2): {any_match}/{len(results)} ({any_match / len(results):.2%})")


async def main():
    """Loads the GVFC focus dataset, runs LLM evaluation, saves JSON outputs, and prints metrics."""
    config = load_config()
    llm_config = config["llm_framing_analyzer"]

    df = pd.read_csv(BENCHMARK_CSV)
    print(f"Starting GVFC Focus validation on {len(df)} headlines with model: {llm_config['model']}\n")

    all_results = await evaluate_focus(df, llm_config)

    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nRaw results saved to: {RESULTS_JSON}")
    print_metrics(all_results)


if __name__ == "__main__":
    asyncio.run(main())
