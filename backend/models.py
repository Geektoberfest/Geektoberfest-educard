from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, timezone
import uuid

class Card(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    deck_id: str
    type: Literal["flashcard", "mcq"] = "flashcard"
    question: str
    answer: str
    options: Optional[List[str]] = None  # For MCQs
    explanation: Optional[str] = None

class Deck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: str
    creator: str
    collaborators: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cards: List[Card] = Field(default_factory=list)

class DeckCreate(BaseModel):
    title: str
    description: str
    category: str
    creator: str
    collaborators: Optional[List[str]] = None

class Material(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    content: str
    chunk_count: int = 0
    uploaded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GenerateRequest(BaseModel):
    topic: str
    card_type: Literal["flashcard", "mcq", "mixed"] = "flashcard"
    count: int = 5
    material_id: Optional[str] = None

class ExplainRequest(BaseModel):
    question: str
    user_answer: str
    correct_answer: str
    understanding_level: Literal["ELI5", "Beginner", "Intermediate", "Advanced"] = "Beginner"
    hint_level: int = Field(default=4, ge=1, le=4)
    learner_attempt: Optional[str] = None
