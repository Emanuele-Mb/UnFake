import html
from pathlib import Path
import re
import pandas as pd

VALIDATION_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = VALIDATION_DIR / "datasets"

STRICT_MAPPING = {
    "Gender": [
        "sexism", "misogyny", "sexist", "misandry",
        "slutshaming", "misgendering", "heteronormativity"
    ],
    "Cultural": [
        "racism", "ethnocentric", "xenophobia",
        "colorism", "eurocentrism", "racist"
    ],
    "Age": [
        "ageism", "ageist", "agebias"
    ],
    "Disability": [
        "ableism"
    ],
    "Religion": [
        "antisemitism", "religion"
    ]
}

BROAD_EXTRA = {
    "Gender": ["gender"],
    "Cultural": ["racial", "ethnic", "cultural", "race", "sociocultural", "racerelated"],
    "Age": ["age", "agerelated"],
    "Disability": ["disability", "handicap", "deafness", "impairment"],
    "Religion": []
}

NEUTRAL_TAGS = ["weather", "schedule", "food", "sport", "music", "travel"]


def clean_social_text(text: str) -> str:
    """Strips HTML entities, URLs, and @mentions to normalize social text toward headline style."""
    text = html.unescape(str(text))
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def build_validation_set(
    input_csv: Path = DATASETS_DIR / "aspects.csv",
    output_csv: Path = DATASETS_DIR / "beads_validation_clean.csv",
    use_broad: bool = False,
    max_per_category: int = 300,
    neutral_samples: int = 300,
    random_state: int = 42
):
    """Filters, cleans, and balances BEADs bias records alongside neutral controls into a validation CSV."""
    df = pd.read_csv(input_csv)
    df["Aspect_clean"] = df["Aspect"].astype(str).str.strip().str.lower()

    tag_to_category = {}
    for cat, tags in STRICT_MAPPING.items():
        all_tags = tags + (BROAD_EXTRA[cat] if use_broad else [])
        for t in all_tags:
            tag_to_category[t] = cat

    pos_df = df[df["Aspect_clean"].isin(tag_to_category)].copy()
    pos_df["target_category"] = pos_df["Aspect_clean"].map(tag_to_category)
    pos_df["clean_text"] = pos_df["text"].apply(clean_social_text)
    pos_df = pos_df[pos_df["clean_text"].str.split().str.len() >= 4]

    # Merge duplicate texts carrying multiple aspect annotations into pipe-separated labels
    grouped_pos = (
        pos_df.groupby("clean_text")
        .agg(
            expected_biases=("target_category", lambda x: "|".join(sorted(set(x)))),
            raw_aspects=("Aspect_clean", lambda x: "|".join(sorted(set(x))))
        )
        .reset_index()
    )

    sampled_parts = []
    for cat in STRICT_MAPPING.keys():
        cat_rows = grouped_pos[grouped_pos["expected_biases"].str.contains(cat)]
        n = min(len(cat_rows), max_per_category)
        sampled_parts.append(cat_rows.sample(n=n, random_state=random_state))

    final_pos = pd.concat(sampled_parts).drop_duplicates(subset=["clean_text"])

    neg_df = df[df["Aspect_clean"].isin(NEUTRAL_TAGS)].copy()
    neg_df["clean_text"] = neg_df["text"].apply(clean_social_text)
    neg_df = neg_df[
        (neg_df["clean_text"].str.split().str.len() >= 5) &
        (~neg_df["clean_text"].isin(final_pos["clean_text"]))
    ].drop_duplicates(subset=["clean_text"])

    final_neg = neg_df.sample(n=min(len(neg_df), neutral_samples), random_state=random_state)[["clean_text"]].copy()
    final_neg["expected_biases"] = "None"
    final_neg["raw_aspects"] = "neutral_control"

    validation_df = pd.concat([final_pos, final_neg], ignore_index=True)
    validation_df = validation_df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    validation_df.to_csv(output_csv, index=False)

    print(f"Dataset saved to '{output_csv}' ({len(validation_df)} total rows):")
    print(validation_df["expected_biases"].value_counts())


if __name__ == "__main__":
    build_validation_set(use_broad=False, max_per_category=300, neutral_samples=300)
