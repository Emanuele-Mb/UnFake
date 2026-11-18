import asyncio
import json
import sys
from pathlib import Path
import pandas as pd

VALIDATION_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = VALIDATION_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from headline_analyst.utils.config_loader import load_config
from headline_analyst.data import Article, Analysis
from headline_analyst.analyzer.framing_analysis import llm_framing_analysis

BENCHMARK_CSV = VALIDATION_DIR / "datasets" / "beads_validation_clean.csv"
RESULTS_JSON = Path(__file__).resolve().parent / "results_beads.json"

TARGET_CATEGORIES = ["Gender", "Cultural", "Age", "Disability", "Religion"]


async def evaluate_beads(df: pd.DataFrame, llm_config: dict, batch_size: int = 15, pause: float = 2.0) -> list[dict]:
    """Runs the LLM framing analyzer in batches on BEADs validation texts."""
    records = df.to_dict(orient="records")
    outputs = []

    for start in range(0, len(records), batch_size):
        batch_rows = records[start : start + batch_size]
        articles = [
            Article(
                title=r["clean_text"],
                source="beads_aspects",
                query_origin=f"beads_{start + i}",
            )
            for i, r in enumerate(batch_rows)
        ]

        print(f"  Batch {start + 1}-{start + len(batch_rows)} of {len(records)}...")
        try:
            analyses: list[Analysis] = await llm_framing_analysis(llm_config, articles)
            for row, analysis in zip(batch_rows, analyses):
                detected = {b.name: score for b, score in analysis.biases.items()}
                outputs.append({
                    **row,
                    "predicted_biases": detected,
                    "tone_intensity": analysis.tone_intensity,
                })
        except Exception as e:
            print(f"  [ERROR] Batch skipped: {e}")

        if start + batch_size < len(records):
            await asyncio.sleep(pause)

    return outputs


def print_metrics(results: list[dict]):
    """Computes and displays Precision, Recall, F1, support, and false positives per category."""
    print("\n" + "=" * 68)
    print(f"{'CATEGORY':16s} | {'PREC':>6s} | {'REC':>6s} | {'F1':>6s} | {'SUPP':>5s} | {'FP':>4s}")
    print("-" * 68)

    for cat in TARGET_CATEGORIES:
        tp = fp = fn = 0
        cat_lower = cat.lower()

        for row in results:
            exp_raw = str(row["expected_biases"])
            exp_set = set() if exp_raw == "None" else {x.strip().lower() for x in exp_raw.split("|")}

            pred_dict = {k.lower(): v for k, v in row["predicted_biases"].items()}
            is_pred = pred_dict.get(cat_lower, 0) >= 1
            is_true = cat_lower in exp_set

            if is_true and is_pred:
                tp += 1
            elif not is_true and is_pred:
                fp += 1
            elif is_true and not is_pred:
                fn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        support = tp + fn

        print(f"{cat:16s} | {precision:6.2%} | {recall:6.2%} | {f1:6.2%} | {support:5d} | {fp:4d}")

    print("=" * 68)

    # Check false positive rate specifically on neutral control sentences
    neutral_rows = [r for r in results if str(r["expected_biases"]) == "None"]
    if neutral_rows:
        target_lower = {c.lower() for c in TARGET_CATEGORIES}
        neutral_fp = sum(
            1 for r in neutral_rows
            if any(k.lower() in target_lower and v >= 1 for k, v in r["predicted_biases"].items())
        )
        print(f"False positives on neutral controls (None): {neutral_fp}/{len(neutral_rows)} ({neutral_fp / len(neutral_rows):.2%})")


async def main():
    """Loads the BEADs validation dataset, runs LLM evaluation, saves JSON outputs, and prints metrics."""
    config = load_config()
    llm_config = config["llm_framing_analyzer"]

    df = pd.read_csv(BENCHMARK_CSV)
    print(f"Starting BEADs validation on {len(df)} texts with model: {llm_config['model']}\n")

    all_results = await evaluate_beads(df, llm_config)

    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nRaw results saved to: {RESULTS_JSON}")
    print_metrics(all_results)


if __name__ == "__main__":
    asyncio.run(main())
