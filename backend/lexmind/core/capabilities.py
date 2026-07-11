"""Capability model for LexMind modules."""

from enum import StrEnum
from typing import Final


class Capability(StrEnum):
    """Strongly typed capabilities a module may expose."""

    OCR = "ocr"
    PARSER = "parser"
    EMBEDDING = "embedding"
    VECTOR_STORE = "vector_store"
    RETRIEVER = "retriever"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    TIMELINE = "timeline"
    CONTRADICTION_DETECTION = "contradiction_detection"
    AI_PROVIDER = "ai_provider"
    PLUGIN = "plugin"


CORE_CAPABILITIES: Final[frozenset[Capability]] = frozenset(
    {
        Capability.PARSER,
        Capability.PLUGIN,
    }
)
