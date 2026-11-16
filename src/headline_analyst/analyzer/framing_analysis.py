import os
import threading
from functools import lru_cache
from pathlib import Path

import torch
from transformers import pipeline

from headline_analyst.data import Article, Emotion, EmotionsEnum
from headline_analyst.analyzer.factory import create_framing_analyzer

_inference_lock = threading.Lock()


def _resolve_model_path(model_path: str) -> str:
    direct_path = Path(model_path)
    if direct_path.exists():
        return str(direct_path.resolve())

    project_root = Path(__file__).resolve().parents[3]
    root_relative_path = project_root / model_path
    if root_relative_path.exists():
        return str(root_relative_path.resolve())

    raise FileNotFoundError(
        f"Error: file not found in '{model_path}'. "
    )


@lru_cache(maxsize=1)
def _get_emotion_classifier(model_path: str):
    """RoBERTa emotion classifier model executed in local"""
    resolved_path = _resolve_model_path(model_path)
    device = 0 if torch.cuda.is_available() else -1

    return pipeline(
        task="text-classification",
        model=resolved_path,
        top_k=None,
        device=device,
        local_files_only=True,
    )


def warmup_emotion_classifier(model_path: str) -> None:
    _get_emotion_classifier(model_path)


def predict_emotions(model_config: dict, articles: list[Article]) -> list[list[Emotion]]:
    if not articles:
        return []

    classifier = _get_emotion_classifier(model_config["model"])
    batch_size = model_config.get("batch_size", 32)
    secondary_threshold = model_config.get("secondary_threshold", 0.15)

    headlines = [a.title for a in articles]

    with _inference_lock:
        model_outputs = classifier(headlines, batch_size=batch_size, truncation=True)

    results: list[list[Emotion]] = []
    for output in model_outputs:
        top_emotions: list[Emotion] = []
        for i, pred in enumerate(output[:2]):
            score = pred["score"]
            if i == 0 or score >= secondary_threshold:
                label_str = pred["label"].upper()
                top_emotions.append(Emotion(label=EmotionsEnum[label_str], score=score))
        results.append(top_emotions)

    return results


async def llm_framing_analysis(analyzer_config: dict, articles: list[Article]):
    llm_analyzer = create_framing_analyzer(analyzer_config)

    async with llm_analyzer:
        analyses = await llm_analyzer.annotate_headline(articles)

    return analyses
