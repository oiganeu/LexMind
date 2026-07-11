"""Event type declarations.

These are identifiers for the events LexMind modules may emit. They are
declarations only — no business logic is attached.
"""

from enum import StrEnum


class EventType(StrEnum):
    """Canonical event names used across the platform."""

    APPLICATION_STARTED = "application.started"
    APPLICATION_STOPPED = "application.stopped"
    MODULE_LOADED = "module.loaded"
    MODULE_STARTED = "module.started"
    MODULE_STOPPED = "module.stopped"
    MODULE_FAILED = "module.failed"
    CONFIGURATION_LOADED = "configuration.loaded"
    DOCUMENT_ADDED = "document.added"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_REMOVED = "document.removed"
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    HEALTH_CHANGED = "health.changed"
