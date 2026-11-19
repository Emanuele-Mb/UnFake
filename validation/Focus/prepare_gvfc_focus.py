from pathlib import Path
import pandas as pd

VALIDATION_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = VALIDATION_DIR / "datasets"

RAW_GVFC_XLSX = DATASETS_DIR / "GVFC_headlines_and_annotations.xlsx"
OUT_CSV = DATASETS_DIR / "gvfc_focus_clean.csv"

# Canonical 14 Focus categories (Media Frames Corpus adaptation)
FOCUS_CATEGORIES = [
    "Economic",
    "Resources",
    "Morality",
    "Fairness",
    "Legal",
    "Policy",
    "Crime",
    "Security",
    "Health",
    "Quality of Life",
    "Cultural Identity",
    "Public Opinion",
    "Political",
    "Other",
]

# Mapping from GVFC codes/labels to the 14 Focus categories.
# - GVFC frame 8 (society/culture: moral values, religion, ethical judgments) -> "Morality"
# - Any non-empty dataset category not matching the 14 target categories -> "Other"
GVFC_TO_FOCUS = {
    "1": "Legal",
    "2": "Policy",
    "3": "Political",
    "4": "Health",
    "5": "Security",
    "6": "Cultural Identity",
    "7": "Public Opinion",
    "8": "Morality",
    "9": "Economic",
    "2nd amendment": "Legal",
    "2nd amendment/gun rights": "Legal",
    "gun control": "Policy",
    "gun control/regulation": "Policy",
    "politics": "Political",
    "mental health": "Health",
    "school/public space safety": "Security",
    "race/ethnicity": "Cultural Identity",
    "public opinion": "Public Opinion",
    "society/culture": "Morality",
    "economic consequences": "Economic",
    "morality": "Morality",
    "fairness": "Fairness",
    "crime": "Crime",
    "resources": "Resources",
    "quality of life": "Quality of Life",
    "other": "Other",
}

EMPTY_TOKENS = {"", "nan", "none", "null"}
ABSENT_SECONDARY_TOKENS = EMPTY_TOKENS | {"99", "0"}


def map_gvfc_label(raw_val, is_secondary: bool = False) -> str | None:
    """Maps a GVFC frame code or label string to one of the 14 Focus categories.

    Unrecognized non-empty dataset categories are mapped to 'Other'.
    """
    if pd.isna(raw_val):
        return None
    key = str(raw_val).strip().lower()
    if key.endswith(".0"):
        key = key[:-2]

    if is_secondary:
        if key in ABSENT_SECONDARY_TOKENS:
            return None
    else:
        if key in EMPTY_TOKENS:
            return None

    return GVFC_TO_FOCUS.get(key, "Other")


def build_gvfc_dataset(
    input_path: Path = RAW_GVFC_XLSX,
    output_csv: Path = OUT_CSV,
    max_per_category: int | None = None,
    random_state: int = 42,
):
    """Cleans GVFC Excel annotations and maps primary/secondary frames into a Focus validation CSV."""
    if input_path.suffix.lower() in {".xlsx", ".xls"}:
        xls = pd.ExcelFile(input_path)
        df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
    else:
        df = pd.read_csv(input_path)

    title_col = next((c for c in ["news_title", "headline", "title"] if c in df.columns), None)
    primary_col = next((c for c in ["Q3 Theme1", "Theme1", "frame1", "primary_frame"] if c in df.columns), None)
    secondary_col = next((c for c in ["Q3 Theme2", "Theme2", "frame2", "secondary_frame"] if c in df.columns), None)

    if not title_col or not primary_col:
        raise ValueError(f"Expected title and primary frame columns not found in {list(df.columns)}")

    records = []
    for idx, row in df.iterrows():
        headline = str(row[title_col]).strip()
        if not headline or headline.lower() == "nan":
            continue

        # Combine primary and optional secondary GVFC frames; non-matching dataset labels become "Other"
        frames = []
        primary_mapped = map_gvfc_label(row[primary_col], is_secondary=False)
        if primary_mapped:
            frames.append(primary_mapped)

        if secondary_col and secondary_col in df.columns:
            secondary_mapped = map_gvfc_label(row[secondary_col], is_secondary=True)
            if secondary_mapped and secondary_mapped not in frames:
                frames.append(secondary_mapped)

        if not frames:
            continue

        records.append({
            "headline_id": f"gvfc_{idx}",
            "headline": headline,
            "expected_focus": "|".join(frames),
            "num_labels": len(frames),
        })

    clean_df = pd.DataFrame(records).drop_duplicates(subset=["headline"]).reset_index(drop=True)

    if max_per_category is not None:
        sampled_parts = []
        for cat in FOCUS_CATEGORIES:
            cat_rows = clean_df[clean_df["expected_focus"].str.contains(rf"(?:^|\|){cat}(?:\||$)", regex=True)]
            if not cat_rows.empty:
                sampled_parts.append(cat_rows.sample(n=min(len(cat_rows), max_per_category), random_state=random_state))
        clean_df = pd.concat(sampled_parts).drop_duplicates(subset=["headline"])
        clean_df = clean_df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(output_csv, index=False, encoding="utf-8")

    print(f"Dataset saved to '{output_csv}' ({len(clean_df)} unique headlines)")
    print("\nLabel distribution:")
    print(clean_df["expected_focus"].str.split("|").explode().value_counts().to_string())


if __name__ == "__main__":
    build_gvfc_dataset(max_per_category=None)
