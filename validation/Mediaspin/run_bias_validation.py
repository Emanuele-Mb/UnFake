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

BENCHMARK_CSV = VALIDATION_DIR / "datasets" / "benchmark_bias.csv"
RESULTS_JSON = Path(__file__).resolve().parent / "results_bias.json"


async def evaluate_group(df_group: pd.DataFrame, llm_config: dict, batch_size: int = 15, pause: float = 2.0) -> list[dict]:
    """Runs the LLM framing analyzer in batches on a headline split and collects bias predictions."""
    records = df_group.to_dict(orient="records")
    outputs = []

    for start in range(0, len(records), batch_size):
        batch_rows = records[start : start + batch_size]
        articles = [
            Article(
                title=r["headline"],
                source=r["outlet"] or "mediaspin",
                query_origin=f"{r['pair_id']}_{r['version']}",
            )
            for r in batch_rows
        ]

        print(f"  Batch {start + 1}-{start + len(batch_rows)} of {len(records)} ({batch_rows[0]['version']})...")
        try:
            analyses: list[Analysis] = await llm_framing_analysis(llm_config, articles)
            for row, analysis in zip(batch_rows, analyses):
                detected = {b.name: score for b, score in analysis.biases.items()}
                outputs.append({
                    **row,
                    "predicted_biases": detected,
                    "predicted_score": detected.get(row["target_bias"], 0),
                    "predicted_label": 1 if row["target_bias"] in detected else 0,
                    "tone_intensity": analysis.tone_intensity,
                })
        except Exception as e:
            print(f"  [ERROR] Batch skipped: {e}")

        if start + batch_size < len(records):
            await asyncio.sleep(pause)

    return outputs


def print_metrics(results: list[dict]):
    """Computes and displays Precision, Recall, F1, and pairwise accuracy for each bias category."""
    df = pd.DataFrame(results)
    print("\n" + "=" * 72)
    print(f"{'CATEGORY':16s} | {'PREC':>6s} | {'REC':>6s} | {'F1':>6s} | {'PAIR ACC':>8s} | {'N':>4s}")
    print("-" * 72)

    for bias_name, grp in df.groupby("target_bias"):
        tp = ((grp["ground_truth"] == 1) & (grp["predicted_label"] == 1)).sum()
        fp = ((grp["ground_truth"] == 0) & (grp["predicted_label"] == 1)).sum()
        fn = ((grp["ground_truth"] == 1) & (grp["predicted_label"] == 0)).sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        # Share of pairs where the edited headline receives a strictly higher bias score than its original
        piv = grp.pivot(index="pair_id", columns="version", values="predicted_score").dropna()
        pair_acc = (piv["edited"] > piv["original"]).mean() if len(piv) > 0 else 0.0

        print(f"{bias_name:16s} | {precision:6.2%} | {recall:6.2%} | {f1:6.2%} | {pair_acc:8.2%} | {len(grp):4d}")
    print("=" * 72)


async def main():
    """Loads benchmark headlines, evaluates original and edited splits separately, and saves results."""
    config = load_config()
    llm_config = config["llm_framing_analyzer"]

    df = pd.read_csv(BENCHMARK_CSV)
    print(f"Starting validation on {len(df)} headlines with model: {llm_config['model']}\n")

    # Evaluate splits separately so the model does not compare paired headlines in the same prompt
    orig_results = await evaluate_group(df[df["version"] == "original"], llm_config)
    edit_results = await evaluate_group(df[df["version"] == "edited"], llm_config)

    all_results = orig_results + edit_results
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nRaw results saved to: {RESULTS_JSON}")
    print_metrics(all_results)


if __name__ == "__main__":
    asyncio.run(main())
