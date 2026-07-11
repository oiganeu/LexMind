"""Single source of version truth."""

from importlib.metadata import PackageNotFoundError, version

from lexmind.__about__ import __version__


def get_version() -> str:
    """Return the package version."""
    try:
        return version("lexmind")
    except PackageNotFoundError:
        return __version__
