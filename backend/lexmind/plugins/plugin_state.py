"""Plugin lifecycle states."""

from enum import StrEnum


class PluginState(StrEnum):
    """Enumeration of plugin lifecycle states."""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    STARTED = "started"
    STOPPED = "stopped"
    FAILED = "failed"
    DISABLED = "disabled"
    UNINSTALLED = "uninstalled"
