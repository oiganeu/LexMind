"""Pydantic v2 configuration schema.

All application code accesses configuration through typed models. Dictionaries
are never exposed to consumers.
"""

from pydantic import BaseModel, ConfigDict, Field

from lexmind.config.config_types import Environment, LogLevel


class _Base(BaseModel):
    """Base configuration model. Unknown keys are forbidden."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SystemConfig(_Base):
    app_name: str = "LexMind"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    data_dir: str = "./data"


class LoggingConfig(_Base):
    level: LogLevel = LogLevel.INFO
    json_format: bool = False
    correlation_id: bool = True


class KernelConfig(_Base):
    version: str = "0.1.0"
    max_modules: int = Field(default=256, ge=1)
    fail_fast: bool = False


class EventsConfig(_Base):
    enabled: bool = True
    history_size: int = Field(default=1000, ge=0)
    async_dispatch: bool = False


class PluginsConfig(_Base):
    enabled: bool = True
    auto_discover: bool = True
    directories: list[str] = Field(default_factory=list)


class OcrConfig(_Base):
    default_provider: str = "tesseract"
    languages: list[str] = Field(default_factory=lambda: ["ron", "eng"])
    dpi: int = Field(default=300, ge=50, le=1200)


class ParserConfig(_Base):
    default_parser: str = "pdf"
    extract_metadata: bool = True


class ChunkingConfig(_Base):
    strategy: str = "recursive"
    chunk_size: int = Field(default=1024, ge=64)
    chunk_overlap: int = Field(default=128, ge=0)


class EmbeddingsConfig(_Base):
    default_provider: str = "openai"
    model: str = "text-embedding-3-small"
    dimensions: int = Field(default=1536, ge=1)


class VectorStoreConfig(_Base):
    default_provider: str = "pgvector"
    collection: str = "lexmind"
    distance: str = "cosine"


class RetrievalConfig(_Base):
    top_k: int = Field(default=10, ge=1)
    hybrid_alpha: float = Field(default=0.5, ge=0.0, le=1.0)


class RerankerConfig(_Base):
    enabled: bool = True
    model: str = "cross-encoder"
    top_n: int = Field(default=5, ge=1)


class KnowledgeGraphConfig(_Base):
    enabled: bool = True
    backend: str = "networkx"


class TimelineConfig(_Base):
    enabled: bool = True
    date_formats: list[str] = Field(default_factory=lambda: ["%Y-%m-%d"])


class McpConfig(_Base):
    enabled: bool = False
    transport: str = "stdio"


class ApiConfig(_Base):
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: list[str] = Field(default_factory=list)


class UiConfig(_Base):
    enabled: bool = True
    theme: str = "auto"


class CacheConfig(_Base):
    enabled: bool = True
    backend: str = "memory"
    ttl_seconds: int = Field(default=3600, ge=0)


class SecurityConfig(_Base):
    auth_required: bool = False
    allowed_hosts: list[str] = Field(default_factory=list)


class PerformanceConfig(_Base):
    workers: int = Field(default=4, ge=1)
    max_concurrency: int = Field(default=64, ge=1)


class MonitoringConfig(_Base):
    enabled: bool = False
    metrics_port: int = Field(default=9090, ge=1, le=65535)


class LexMindConfig(_Base):
    """Root configuration model aggregating all sections."""

    version: int = 1
    system: SystemConfig = Field(default_factory=SystemConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    kernel: KernelConfig = Field(default_factory=KernelConfig)
    events: EventsConfig = Field(default_factory=EventsConfig)
    plugins: PluginsConfig = Field(default_factory=PluginsConfig)
    ocr: OcrConfig = Field(default_factory=OcrConfig)
    parser: ParserConfig = Field(default_factory=ParserConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)
    knowledge_graph: KnowledgeGraphConfig = Field(default_factory=KnowledgeGraphConfig)
    timeline: TimelineConfig = Field(default_factory=TimelineConfig)
    mcp: McpConfig = Field(default_factory=McpConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    ui: UiConfig = Field(default_factory=UiConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)


# Deprecated keys that must not appear in any configuration source.
DEPRECATED_KEYS: frozenset[str] = frozenset(
    {
        "system.use_legacy_ocr",
        "logging.colors",
        "ocr.use_gpu_old",
    }
)
