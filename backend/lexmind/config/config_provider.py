"""Typed configuration provider.

Application code accesses configuration exclusively through this provider.
It exposes the validated Pydantic models for each section.
"""

from lexmind.config.config_schema import (
    ApiConfig,
    CacheConfig,
    ChunkingConfig,
    EmbeddingsConfig,
    EventsConfig,
    KernelConfig,
    KnowledgeGraphConfig,
    LexMindConfig,
    LoggingConfig,
    McpConfig,
    MonitoringConfig,
    OcrConfig,
    ParserConfig,
    PerformanceConfig,
    PluginsConfig,
    RerankerConfig,
    RetrievalConfig,
    SecurityConfig,
    SystemConfig,
    TimelineConfig,
    UiConfig,
    VectorStoreConfig,
)


class ConfigurationProvider:
    """Read-only access to validated configuration sections."""

    def __init__(self, config: LexMindConfig) -> None:
        self._config = config

    @property
    def raw(self) -> LexMindConfig:
        return self._config

    @property
    def system(self) -> SystemConfig:
        return self._config.system

    @property
    def logging(self) -> LoggingConfig:
        return self._config.logging

    @property
    def kernel(self) -> KernelConfig:
        return self._config.kernel

    @property
    def events(self) -> EventsConfig:
        return self._config.events

    @property
    def plugins(self) -> PluginsConfig:
        return self._config.plugins

    @property
    def ocr(self) -> OcrConfig:
        return self._config.ocr

    @property
    def parser(self) -> ParserConfig:
        return self._config.parser

    @property
    def chunking(self) -> ChunkingConfig:
        return self._config.chunking

    @property
    def embeddings(self) -> EmbeddingsConfig:
        return self._config.embeddings

    @property
    def vector_store(self) -> VectorStoreConfig:
        return self._config.vector_store

    @property
    def retrieval(self) -> RetrievalConfig:
        return self._config.retrieval

    @property
    def reranker(self) -> RerankerConfig:
        return self._config.reranker

    @property
    def knowledge_graph(self) -> KnowledgeGraphConfig:
        return self._config.knowledge_graph

    @property
    def timeline(self) -> TimelineConfig:
        return self._config.timeline

    @property
    def mcp(self) -> McpConfig:
        return self._config.mcp

    @property
    def api(self) -> ApiConfig:
        return self._config.api

    @property
    def ui(self) -> UiConfig:
        return self._config.ui

    @property
    def cache(self) -> CacheConfig:
        return self._config.cache

    @property
    def security(self) -> SecurityConfig:
        return self._config.security

    @property
    def performance(self) -> PerformanceConfig:
        return self._config.performance

    @property
    def monitoring(self) -> MonitoringConfig:
        return self._config.monitoring
