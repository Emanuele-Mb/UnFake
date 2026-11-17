# UNFAKE — Validation Branch

This branch contains the offline validation suite used to benchmark **UNFAKE**'s LLM-based headline analysis against labeled ground-truth datasets. 

Unlike the `main` branch web application, this pipeline bypasses Flask, live news retrieval APIs, Firebase, and the local RoBERTa emotion classifier to evaluate the LLM framing analyzer (`llm_framing_analysis`) in isolation.

---

## Current Scope: Bias Detection

The first validation module evaluates **Bias Detection** using the **MediaSpin** corpus (`anonymous.4open.science/r/mediaspin-A5C7`), which pairs `original_headline` and `edited_headline` versions of the same news story and annotates which bias type was introduced (`1`), removed (`-1`), or unchanged (`0`).

### Category Mapping

Because MediaSpin focuses on editorial and linguistic spin rather than demographic biases (`GENDER`, `CULTURAL`, `AGE`, `RELIGION`, `DISABILITY`) or `NEGATIVITY`, this benchmark covers **7 of UNFAKE's 13 bias categories**:

| MediaSpin Column | UNFAKE `Bias` Enum | Description |
| :--- | :--- | :--- |
| `opinion_statements_presented_as_fact_value` | `OPINION` (13) | Subjective judgments framed as objective facts |
| `sensationalism_value` | `SENSATIONALISM` (9) | Hyperbolic or dramatic language |
| `mudslinging_value` | `ADHOMINEM` (12) | Personal attacks or character insults |
| `subjective_qualifying_adjectives_value` | `SUBJECTIVE` (11) | Evaluative adjectives inserted by the author |
| `word_choice_value` | `STATEMENT` (7) | Loaded or ideologically coded terminology |
| `bias_by_omission_value` | `OMISSION` (8) | One-sided framing missing key actors or perspectives |
| `slant_value` | `POLITICAL` (1) | Partisan or ideological framing |

---

##Setup
Base environment setup, API keys (.env), and model selection (config.yaml) follow the main branch README.md. With your existing .venv activated:
   1) Install pandas (required for dataset preprocessing and metric aggregation):
```bash
pip install pandas
```
   2) Add the dataset: Place the full MediaSpin CSV in the project root as mediaspin_full.csv (or update the FULL_CSV path at the top of validation/prepare_dataset.py).
   3) Verify LLM configuration: Ensure llm_framing_analyzer in config.yaml points to the model and API key you want to benchmark.

##Running the Benchmark
Run both scripts from the root directory, using the same python virtual environment as the main branch, in this order:
```bash
python validation/prepare_dataset.py
```
Which filters out malformed annotations and identical headline pairs and samples 25 pairs per category (25 original headlines with ground_truth = 0 and 25 edited headlines where the target bias was added, ground_truth = 1), producing 350 headlines in validation/benchmark_bias.csv.

```bash
python validation/run_bias_validation.py
```
That evaluates original and edited splits in separate passes (15 headlines per batch) so the LLM analyzes each headline independently without comparing pairs side-by-side, prints a per-category summary table and saves full structured outputs to validation/results_bias.json.
