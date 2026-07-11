# Plugins

## Purpose

The Plugins package is the generic extensibility framework of LexMind.
Plugins are discoverable, isolated, versioned, declare capabilities, and
are hot-loadable in the future.

This framework has **no concrete plugin implementations** — only the
plumbing every plugin relies on.

## Architecture

```
PluginManager
  ├── PluginRegistry      (id lookup, capability index)
  ├── Discovery           (filesystem / namespace scanning)
  ├── PluginLoader        (entrypoint resolution)
  └── Dependency validation + kernel compatibility
```

## Lifecycle

Plugins move through: `discovered → loaded → initialized → started →
stopped → uninstalled`. `failed` and `disabled` are special states.

Each plugin implements: `initialize(context)`, `start()`, `stop()`,
`dispose()`, `health()`.

## Discovery

- **Filesystem**: scan directories for `plugin.yaml` manifests.
- **Namespace packages**: future import-based discovery.
- **Future**: pip packages, remote registry.

## Loading

A manifest declares an `entrypoint` of the form `module:attribute`. The
loader imports the module and resolves the attribute, which must be a
callable or plugin class.

## Capabilities

`PluginCapability` enumerates OCR, Parser, Embedding, VectorStore,
Retriever, Reranker, LLM, KnowledgeGraph, Timeline, Exporter, Importer, UI,
MCP, Security, Authentication, Authorization, Logging, Monitoring.

## Security Model

- Plugins never access each other directly.
- Communication is only through interfaces or the Event Bus.
- Plugins receive a `PluginContext` (config, logger, event bus, kernel,
  service provider, workspace) — no globals.
- Future: permission system, sandboxing, digital signatures, marketplace.

## Future

Documented but not implemented: hot reload, plugin marketplace, digital
signatures, sandboxing, permission system, automatic updates, version
compatibility enforcement at runtime.
