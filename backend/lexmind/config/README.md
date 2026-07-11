# Configuration Management

The centralized, layered, typed configuration system for LexMind.

## Layering & Priority

Sources are merged from lowest to highest precedence. Higher sources
override lower ones:

1. Runtime overrides (`ConfigManager.set_override`)
2. Environment variables (`LEXMIND_*`)
3. Workspace configuration (`workspace.yaml`)
4. Plugin configuration
5. Environment YAML (`development.yaml`, `production.yaml`, `testing.yaml`)
6. Default YAML (`default.yaml`)

## Typed Access

Application code never reads YAML directly. It accesses configuration
through the `ConfigurationProvider`, which exposes validated Pydantic v2
models:

```python
provider = ConfigManager("configs").load()
provider.vector_store.default_provider
provider.ocr.languages
provider.logging.level
```

## Validation

Configuration is validated for types, ranges, allowed values, unknown
sections, and deprecated keys. Validation failures raise
`ConfigValidationError` and publish `configuration.validation_failed`.

## Secrets

Secrets must never appear in YAML. YAML sources are scanned for
secret-like keys (`password`, `secret`, `api_key`, `token`,
`private_key`, `credential`) and rejected with `SecretInConfigError`.
Supply secrets via environment variables or a future secret provider
(Vault, Docker Secrets, Kubernetes Secrets).

## Environment Variables

Nested keys use a double-underscore separator:

```
LEXMIND_SYSTEM__DEBUG=true
LEXMIND_API__PORT=9001
```

## Versioning

Every configuration file must declare a `version`:

```yaml
version: 1
```

## Runtime Overrides

Temporary, session, and test overrides are applied in-memory without
modifying YAML files:

```python
manager.set_override("api.port", 8123)
```

## Events

`configuration.loaded`, `configuration.reloaded`,
`configuration.validation_failed`, and `configuration.changed` are
published on the event bus when an `EventBus` is provided.

## Best Practices

- Keep environment-specific values in the matching environment YAML.
- Never commit secrets; use environment variables.
- Add new sections as Pydantic models and register them in
  `config_registry.py`.

## Migration Strategy

Deprecated keys are declared in `DEPRECATED_KEYS` (`config_schema.py`)
and rejected on load. When renaming a key, add the old key to
`DEPRECATED_KEYS` and document the replacement here.
