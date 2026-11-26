from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List, Type

from headline_analyst.data import *
from headline_analyst.utils.schema import resolve_schema

ANALYSIS_PROMPT = """
You are an expert media framing and linguistic bias analyst. You will be given a numbered list of news headlines (or short statements).
For each item, produce a structured analysis object matching the schema.

CRITICAL RULES:
- Output a JSON object with a single key "analyses" containing one object per input item, in exact order.
- The "id" field must exactly match the item's number in the input list.
- Base your analysis exclusively on the text itself — do not rely on external background knowledge.
- Multi-label independence: Biases are NOT mutually exclusive. A single headline often exhibits 2 or 3 overlapping biases (e.g., POLITICAL + OPINION + SUBJECTIVE). Evaluate each category independently.
- Calibration consistency: Only strictly clinical, neutral headlines (tone = 1) should return "bias": []. If a headline contains loaded framing, evaluative adjectives, or non-neutral word choices (tone >= 2), identify the corresponding bias(es) at score 1 (subtle) rather than returning [].
- Quotation marks: Quotes do not automatically neutralize bias. If a headline highlights a personal attack, slur, or loaded accusation in quotes as its main hook, still score the corresponding bias (typically 1 or 2).

METRIC DEFINITIONS

1. BIAS  →  "bias": [ {{ "bias_type": BiasName, "score": 1-3 }}, ... ]
Score scale:
  1 = subtle / mild framing cue (e.g., a single loaded verb, mild evaluative adjective, or slight slant)
  2 = clear / noticeable framing that visibly steers reader perception
  3 = dominant / overt bias, slur, or aggressive editorializing

Categories (use exact string name for "bias_type"):
  - POLITICAL: Favors, criticizes, or frames a political party, ideology, politician, or policy stance unevenly.
    Mild (1): "Democrats push costly spending bill" | Strong (3): "Radical left sabotages the economy"
  - GENDER: Reinforces gender stereotypes, double standards, or unnecessary gender focus (including sexism, misogyny, misandry).
    Mild (1): "Working moms struggle to balance office return" | Strong (3): "Female engineer surprisingly solves complex problem"
  - CULTURAL: Generalizes, stereotypes, or "others" racial, ethnic, or national groups (racism, xenophobia, ethnocentrism).
    Mild (1): "Surge of migrants strains border towns" | Strong (3): "Immigrants flooding labor market"
  - AGE: Stereotypes, patronizes, or dismisses people based on age or generation (older or younger).
    Mild (1): "Millennials still reluctant to buy homes" | Strong (3): "Out-of-touch boomers ruin housing market"
  - RELIGION: Stereotypes, mocks, or portrays a religious group or belief system negatively/unevenly (including antisemitism, Islamophobia).
    Mild (1): "Questions raised over religious school funding" | Strong (3): "Muslim neighborhood linked to extremism"
  - DISABILITY: Portrays physical/mental disability or neurodivergence in a stigmatizing, mocking, or dehumanizing way (ableism).
    Mild (1): "Autistic man causes disturbance on flight" | Strong (3): "Facility for mentally deficient individuals"
  - STATEMENT: Non-neutral, loaded, or connotative word choices — especially loaded verbs, nouns, or labels — used instead of neutral reporting words ("says", "plan", "meeting").
    Mild (1): "Leaders struggle in tense talks" / "Critics slam new rule" | Strong (3): "Regime pushes socialist handout"
  - SENSATIONALISM: Dramatic, hyperbolic, alarmist, or clickbait language designed to heighten emotion or urgency.
    Mild (1): "Trump unleashes Twitter storm" / "Markets rattled by fears" | Strong (3): "Economy in freefall as chaos engulfs markets"
  - NEGATIVITY: Disproportionately emphasizes threat, failure, conflict, or bleak outcomes where neutral framing exists.
    Mild (1): "Growth slows amid mounting economic gloom" | Strong (3): "Country in downward spiral under failed leadership"
  - SUBJECTIVE: Evaluative or judgmental adjectives/adverbs that inject opinion into reporting (e.g., "steely", "troubling", "reckless", "bold", "disastrous", "bad").
    Mild (1): "Steely prosecutor faces tough test" | Strong (3): "The troubling, reckless rise of remote work"
  - ADHOMINEM: Attacks, ridicules, smears, or diminishes a person's character, integrity, competence, or motives rather than addressing policy/actions (mudslinging, mockery, derogatory epithets).
    Mild (1): "Mayor rampages on, to city's shame" / "Opponent mocks rival's faith" | Strong (3): "Clueless, corrupt senator proposes new bill"
  - OPINION: Presents a value judgment, prescription ("should", "must"), or subjective conclusion directly as objective fact without attribution.
    Mild (1): "If Trump wants plants open, he should protect workers" | Strong (3): "A carbon tax plan that's a bad deal for the public"

Disambiguation guide:
  - Evaluative adjective/adverb ("reckless", "bad", "steely") -> SUBJECTIVE (plus OPINION if the whole headline makes an unattributed value claim).
  - Loaded verb/noun/label ("slams", "struggle", "crusader", "regime", "war on") -> STATEMENT (plus SENSATIONALISM if dramatic/alarmist).
  - Attack/mockery/smear on a person's character or competence -> ADHOMINEM (do not suppress it just because POLITICAL or SUBJECTIVE also applies).
  - Political co-occurrence: When STATEMENT, ADHOMINEM, SUBJECTIVE, or OPINION frames or attacks a political party, institution, ideology, or political figure unevenly, assign POLITICAL alongside those labels rather than replacing it (do NOT assign POLITICAL to neutral, factual reporting of political events).

2. AGENCY  →  "agency": [ {{ "name": "...", "role": ID }}, ... ]
Extract all named and unnamed entities (persons, groups, organizations, nations, key grammatical subjects).
  2  ACTIVE    : Performs the action or drives the event described.
  1  PASSIVE   : Receives the action or is acted upon.
  3  MENTIONED : Present as context or backdrop without clear active/passive role.

3. FRAMING  →  "framing": ID (select 1)
  1 CONFLICT | 2 GAME_STRATEGY | 3 THEMATIC | 4 HUMAN_INTEREST | 5 EPISODIC | 6 OTHER

4. FOCUS  →  "focus": [ID] or [ID, ID] (select at most 2)
  1 ECONOMIC | 2 RESOURCES | 3 MORALITY | 4 FAIRNESS | 5 LEGAL | 6 POLICY | 7 CRIME
  8 SECURITY | 9 HEALTH | 10 QOL | 11 CULTURAL_ID | 12 PUBLIC_OPINION | 13 POLITICAL | 14 OTHER

5. GENRE  →  "genre": ID (select 1)
  1 INFORMATIVE | 2 INVESTIGATIVE | 3 ANALYTIC | 4 EDITORIAL | 5 ENTERTAINMENT | 6 OTHER

6. TONE  →  "tone": 1-5
  1 = Strictly clinical/neutral — plain factual reporting, no loaded words
  2 = Mildly expressive — subtle framing words ("struggle", "tense", "steely")
  3 = Moderately charged — clear evaluative or dramatic terms ("slams", "storm", "bad deal")
  4 = Strongly emotional/partisan — heavy loaded language or overt judgment
  5 = Extreme/sensational — inflammatory or catastrophizing language throughout

HEADLINES TO ANALYZE:
{items}
"""


class FramingAnalyzer(ABC):
    """
    Abstract class to implement LLM models for headline framing analysis.
    Concrete implementations must inherit from this class.
    """

    def __init__(self, output_model: Type[BaseModel]):
        self.output_model = output_model
        self.schema = resolve_schema(self.output_model.model_json_schema())

    @abstractmethod
    async def annotate_headline(self, articles: list[Article]) -> List[Analysis]:
        pass

    def _build_prompt(self, articles: list[Article]) -> str:
        items = "\n".join(f"id:{idx}. {a.title}" for idx, a in enumerate(articles))
        return ANALYSIS_PROMPT.format(items=items)

    def _parse_response(self, raw_json: str, expected_length: int) -> List[Analysis]:
        """Validates JSON response and aligns outputs by headline id."""
        try:
            validated = self.output_model.model_validate_json(raw_json)
            outputs = [Analysis.from_json(item.model_dump()) for item in validated.analyses]
        except Exception as e:
            raise ValueError(f"Schema validation failed: {e}")

        if len(outputs) != expected_length:
            raise ValueError(
                f"LLM analysis returned {len(outputs)} outputs, expected {expected_length}."
            )

        by_id = {item.headline_index: item for item in outputs}
        if set(by_id.keys()) == set(range(expected_length)):
            return [by_id[i] for i in range(expected_length)]

        return outputs
