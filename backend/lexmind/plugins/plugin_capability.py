"""Plugin capability declarations.

These describe the functional capabilities a plugin can advertise. They are
distinct from the core module capabilities and cover the full extension
surface of LexMind.
"""

from enum import StrEnum


class PluginCapability(StrEnum):
    """Strongly typed plugin capabilities."""

    OCR = "ocr"
    PARSER = "parser"
    EMBEDDING = "embedding"
    VECTOR_STORE = "vector_store"
    RETRIEVER = "retriever"
    RERANKER = "reranker"
    LLM = "llm"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    TIMELINE = "timeline"
    EXPORTER = "exporter"
    IMPORTER = "importer"
    IMPORT_QUEUE = "import_queue"
    WORKER = "worker"
    TASK_EXECUTOR = "task_executor"
    IMAGE_PREPROCESSING = "image_preprocessing"
    LAYOUT_ANALYSIS = "layout_analysis"
    TABLE_DETECTION = "table_detection"
    BARCODE_QR_DETECTION = "barcode_qr_detection"
    LANGUAGE_DETECTION = "language_detection"
    OCR_QUALITY_METRICS = "ocr_quality_metrics"
    OCR_BENCHMARK = "ocr_benchmark"
    OCR_CACHE = "ocr_cache"
    OCR_PIPELINE = "ocr_pipeline"
    OCR_ARTIFACT_INTEGRATION = "ocr_artifact_integration"
    FILE_WATCH = "file_watch"
    UI = "ui"
    MCP = "mcp"
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    LOGGING = "logging"
    MONITORING = "monitoring"
