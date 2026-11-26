from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Literal
from pydantic import BaseModel, Field, field_validator

# ---------------- ENUMS -------------------------- #

class Bias(Enum):
    POLITICAL = 1
    GENDER = 2
    CULTURAL = 3
    AGE = 4
    RELIGION = 5
    DISABILITY = 6
    STATEMENT = 7
    SENSATIONALISM = 8
    NEGATIVITY = 9
    SUBJECTIVE = 10
    ADHOMINEM = 11
    OPINION = 12


BiasName = Literal[
    "POLITICAL",
    "GENDER",
    "CULTURAL",
    "AGE",
    "RELIGION",
    "DISABILITY",
    "STATEMENT",
    "SENSATIONALISM",
    "NEGATIVITY",
    "SUBJECTIVE",
    "ADHOMINEM",
    "OPINION",
]


class Agency(Enum):
    PASSIVE = 1
    ACTIVE = 2
    MENTIONNED = 3


class GenericFraming(Enum):
    CONFLICT = 1
    GAME_STRATEGY = 2
    THEMATIC = 3
    HUMAN_INTEREST = 4
    EPISODIC = 5
    OTHER = 6


class Focus(Enum):
    ECONOMIC = 1
    RESOURCES = 2
    MORALITY = 3
    FAIRNESS = 4
    LEGAL = 5
    POLICY = 6
    CRIME = 7
    SECURITY = 8
    HEALTH = 9
    QOL = 10
    CULTURAL_ID = 11
    PUBLIC_OPINION = 12
    POLITICAL = 13
    OTHER = 14


class Genre(Enum):
    INFORMATIVE = 1
    INVESTIGATIVE = 2
    ANALYTIC = 3
    EDITORIAL = 4
    ENTERTAINMENT = 5
    OTHER = 6


class EmotionsEnum(Enum):
    ADMIRATION = 1
    AMUSEMENT = 2
    ANGER = 3
    ANNOYANCE = 4
    APPROVAL = 5
    CARING = 6
    CONFUSION = 7
    CURIOSITY = 8
    DESIRE = 9
    DISAPPOINTMENT = 10
    DISAPPROVAL = 11
    DISGUST = 12
    EMBARASSMENT = 13
    EXCITEMENT = 14
    FEAR = 15
    GRATITUDE = 16
    GRIEF = 17
    JOY = 18
    LOVE = 19
    NERVOUSNESS = 20
    OPTIMISM = 21
    PRIDE = 22
    REALIZATION = 23
    RELIEF = 24
    REMORSE = 25
    SADNESS = 26
    SURPRISE = 27
    NEUTRAL = 28


# ---------------- DATA CLASSES -------------------- #

@dataclass(frozen=True)
class Article:
    title: str
    source: str
    query_origin: str
    published_at: datetime | None = None
    url: str = ""
    description: str | None = None
    content: str | None = None

    def __str__(self):
        return f"{self.title}, source='{self.source}', query_origin='{self.query_origin}' - URL : {self.url}"

    def __repr__(self):
        return self.__str__()


@dataclass(frozen=True)
class Entity:
    name: str
    role: Agency

    def __str__(self):
        return f"{self.name}, role='{self.role.name}'"

    def __repr__(self):
        return self.__str__()


@dataclass(frozen=True)
class Emotion:
    label: EmotionsEnum
    score: float

    def __str__(self):
        return f"{self.label.name} (score : {self.score:.2f})"

    def __repr__(self):
        return self.__str__()


@dataclass
class Analysis:
    headline_index: int
    biases: Dict[Bias, int]
    agencies: List[Entity]
    frame: GenericFraming
    focus: List[Focus]
    genre: Genre
    tone_intensity: int
    emotions: List[Emotion] = field(default_factory=list)

    @classmethod
    def _parse_bias_key(cls, raw_key) -> Bias | None:
        if isinstance(raw_key, Bias):
            return raw_key
        if isinstance(raw_key, int) and 1 <= raw_key <= 13:
            return Bias(raw_key)
        if isinstance(raw_key, str):
            cleaned = raw_key.strip().upper()
            if cleaned.isdigit() and 1 <= int(cleaned) <= 13:
                return Bias(int(cleaned))
            if cleaned in Bias.__members__:
                return Bias[cleaned]
        return None

    @classmethod
    def from_json(cls, data: dict):
        """Parses the Schema JSON format into an Analysis object."""
        raw_bias = data.get("bias", [])
        biases: Dict[Bias, int] = {}

        if isinstance(raw_bias, dict):
            for k, v in raw_bias.items():
                b_enum = cls._parse_bias_key(k)
                if b_enum is not None:
                    biases[b_enum] = int(v)
        else:
            for item in raw_bias:
                raw_key = item.get("bias_type") if "bias_type" in item else item.get("bias_id")
                b_enum = cls._parse_bias_key(raw_key)
                if b_enum is not None:
                    biases[b_enum] = int(item["score"])

        return cls(
            headline_index=data["id"],
            biases=biases,
            agencies=[
                Entity(name=a["name"], role=Agency(a["role"]))
                for a in data["agency"]
            ],
            frame=GenericFraming(data["framing"]),
            focus=[Focus(int(k)) for k in data["focus"]],
            genre=Genre(data["genre"]),
            tone_intensity=data["tone"],
            emotions=[],
        )


# ------------------- CLASSES FOR THE FORMATTING OF JSON OUTPUTS ------------------------- #

class BiasModel(BaseModel):
    bias_type: BiasName = Field(description="Exact bias category name")
    score: int = Field(description="Intensity score (1: subtle/mild, 2: noticeable, 3: dominant)")


class AgencyModel(BaseModel):
    name: str = Field(description="Name of the entity detected")
    role: int = Field(description="Agency Enum ID (1: Passive, 2: Active, 3: Mentioned)")


class AnalysisItem(BaseModel):
    id: int = Field(description="The index of the headline")
    bias: List[BiasModel] = Field(description="List of detected biases and scores (1-3). Empty [] only if strictly neutral.")
    agency: List[AgencyModel]
    framing: int = Field(description="GenericFraming Enum ID (1-6)")
    focus: List[int] = Field(description="List of max 2 Focus IDs (1-14)", max_length=2)
    genre: int = Field(description="Genre Enum ID (1-6)")
    tone: int = Field(description="Tone intensity score 1-5")

    @field_validator("focus", mode="before")
    @classmethod
    def truncate_focus(cls, v):
        if isinstance(v, list) and len(v) > 2:
            return v[:2]
        return v


class AnalysisResponse(BaseModel):
    analyses: List[AnalysisItem]
