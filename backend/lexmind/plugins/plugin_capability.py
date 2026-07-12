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
    FILE_WATCH = "file_watch"
    UI = "ui"
    MCP = "mcp"
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    LOGGING = "logging"
    MONITORING = "monitoring"
