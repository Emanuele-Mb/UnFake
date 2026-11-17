from pathlib import Path
import pandas as pd

FULL_CSV = Path("mediaspin_full.csv")
OUT_CSV = Path(__file__).resolve().parent / "benchmark_bias.csv"

TARGET_COLS = {
    "opinion_statements_presented_as_fact_value": "OPINION",
    "sensationalism_value": "SENSATIONALISM",
    "mudslinging_value": "ADHOMINEM",
    "subjective_qualifying_adjectives_value": "SUBJECTIVE",
    "word_choice_value": "STATEMENT",
    "bias_by_omission_value": "OMISSION",
    "slant_value": "POLITICAL",
}

SAMPLES_PER_CATEGORY = 25
SEED = 42


def build_benchmark():
    """Extracts a balanced dataset of original/edited headline pairs from MediaSpin."""
    use_cols = ["original_headline", "edited_headline", "outlet"] + list(TARGET_COLS.keys())
    df = pd.read_csv(FULL_CSV, usecols=use_cols).dropna(subset=["original_headline", "edited_headline"])

    # Coerce labels to numeric (-1, 0, 1) and drop rows with malformed string annotations
    for col in TARGET_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=list(TARGET_COLS.keys()))
    df = df[df["original_headline"].str.strip() != df["edited_headline"].str.strip()]

    records = []
    used_indices = set()

    for col, unfake_bias in TARGET_COLS.items():
        # 1.0 means the edit introduced this specific bias into the headline
        candidates = df[(df[col] == 1.0) & (~df.index.isin(used_indices))]
        sampled = candidates.sample(n=min(SAMPLES_PER_CATEGORY, len(candidates)), random_state=SEED)

        for idx, row in sampled.iterrows():
            used_indices.add(idx)
            pair_id = f"{unfake_bias}_{idx}"

            records.append({
                "pair_id": pair_id,
                "target_bias": unfake_bias,
                "version": "original",
                "ground_truth": 0,
                "headline": str(row["original_headline"]).strip(),
                "outlet": str(row.get("outlet", "")),
            })

            records.append({
                "pair_id": pair_id,
                "target_bias": unfake_bias,
                "version": "edited",
                "ground_truth": 1,
                "headline": str(row["edited_headline"]).strip(),
                "outlet": str(row.get("outlet", "")),
            })

    out_df = pd.DataFrame(records)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8")

    print(f"Benchmark salvato in: {OUT_CSV}")
    print(f"Totale titoli estratti: {len(out_df)} ({len(out_df)//2} coppie)")
    print("\nRiepilogo per categoria:")
    print(out_df.groupby(["target_bias", "ground_truth"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    build_benchmark()
