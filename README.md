# UNFAKE — Validation Branch

This branch contains the offline validation suite used to benchmark **UNFAKE**'s LLM-based headline analysis against labeled ground-truth datasets. 

Unlike the `main` branch web application, this pipeline bypasses Flask, live news retrieval APIs, Firebase, and the local RoBERTa emotion classifier to evaluate the LLM framing analyzer (`llm_framing_analysis`) in isolation.

## Bias Results Format
The results of bias analyses will be both a table in the terminal for instant lookup and a json file.
The columns in the tables are the following:
   1) CATEGORY: The evaluated bias class (e.g., Gender, Cultural, Age, Disability, Religion, or framing type).
   2) PREC (Precision): Percentage of correct positive predictions out of all instances flagged by the model for that category.
   3) REC (Recall): Percentage of actual ground-truth instances in that category successfully identified by the model.
   4) F1 (F1-Score): Harmonic mean of Precision and Recall, summarizing the balance between reliability and coverage in a single metric.
   5) SUPP (Support): Total number of actual positive examples for that category present in the test dataset.
   6) FP (False Positives): Number of texts where the model erroneously flagged that category despite its absence in the ground truth.    

---

## Setup
Base environment setup, API keys (.env), and model selection (config.yaml) follow the main branch README.md. With your existing .venv activated:
   1) Install pandas (required for dataset preprocessing and metric aggregation):
```bash
pip install pandas
```
   2) Add the dataset: Place the full MediaSpin CSV in the project root as mediaspin_full.csv (or update the FULL_CSV path at the top of validation/prepare_dataset.py).
   3) Verify LLM configuration: Ensure llm_framing_analyzer in config.yaml points to the model and API key you want to benchmark.

## Running the Benchmark
Run both scripts from the root directory, using the same python virtual environment as the main branch, in this order:
```bash
python validation/prepare_dataset.py
```
Which filters out malformed annotations and identical headline pairs and samples 25 pairs per category (25 original headlines with ground_truth = 0 and 25 edited headlines where the target bias was added, ground_truth = 1), producing 350 headlines in validation/benchmark_bias.csv.

```bash
python validation/run_bias_validation.py
```
That evaluates original and edited splits in separate passes (15 headlines per batch) so the LLM analyzes each headline independently without comparing pairs side-by-side, prints a per-category summary table and saves full structured outputs to validation/results_bias.json.
