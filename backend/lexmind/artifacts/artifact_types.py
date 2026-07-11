"""Artifact type enumerations."""

from enum import Enum, unique


@unique
class ArtifactType(Enum):
    """Classification of artifacts produced by the processing pipeline.

    Each type corresponds to a distinct output format or processing stage.
    """

    ORIGINAL_DOCUMENT = "original_document"
    OCR_TEXT = "ocr_text"
    OCR_LAYOUT = "ocr_layout"
    PARSED_DOCUMENT = "parsed_document"
    ENTITIES = "entities"
    RELATIONSHIPS = "relationships"
    CHUNKS = "chunks"
    EMBEDDINGS = "embeddings"
    VECTOR_INDEX = "vector_index"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    TIMELINE = "timeline"
    SUMMARY = "summary"
    REPORT = "report"
    EXPORT = "export"
    CACHE = "cache"
    THUMBNAIL = "thumbnail"
    PREVIEW = "preview"
    LOG = "log"
    METRICS = "metrics"


# Canonical pipeline ordering -- used for lineage tracking.
PIPELINE_ORDER: tuple[ArtifactType, ...] = (
    ArtifactType.ORIGINAL_DOCUMENT,
    ArtifactType.OCR_TEXT,
    ArtifactType.OCR_LAYOUT,
    ArtifactType.PARSED_DOCUMENT,
    ArtifactType.ENTITIES,
    ArtifactType.RELATIONSHIPS,
    ArtifactType.CHUNKS,
    ArtifactType.EMBEDDINGS,
    ArtifactType.VECTOR_INDEX,
    ArtifactType.KNOWLEDGE_GRAPH,
    ArtifactType.TIMELINE,
    ArtifactType.SUMMARY,
    ArtifactType.REPORT,
    ArtifactType.EXPORT,
)
