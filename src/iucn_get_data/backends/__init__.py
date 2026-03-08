"""Plugin-based backend discovery for ecosystem map storage."""

from abc import ABC, abstractmethod
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ecosystem_map import EcosystemMap

ENTRY_POINT_GROUP = "iucn_get_data.ecosystem_backends"

# Hardcoded fallback for editable installs where entry points may not register
_BUILTIN_BACKENDS = {
    "parquet": "iucn_get_data.backends.parquet:ParquetBackend",
    "cog": "iucn_get_data.backends.cog:CogBackend",
    "ee_vector": "iucn_get_data.backends.ee_vector:EEVectorBackend",
    "ee_raster": "iucn_get_data.backends.ee_raster:EERasterBackend",
}


class EcosystemBackendEntrypoint(ABC):
    """Abstract base class for ecosystem map backend plugins.

    Third-party packages can register backends via entry points in pyproject.toml::

        [project.entry-points."iucn_get_data.ecosystem_backends"]
        my_backend = "my_package.module:MyBackend"
    """

    priority: int = 100  # lower = tried first

    @classmethod
    @abstractmethod
    def guess_can_open(cls, data) -> bool:
        """Return True if this backend can handle the given data."""
        ...

    @classmethod
    @abstractmethod
    def open_ecosystem_map(cls, data, **kwargs) -> "EcosystemMap":
        """Create and return a fully initialized EcosystemMap subclass instance."""
        ...


def _load_class(dotted_path: str) -> type:
    """Import a class from a 'module:ClassName' string."""
    module_path, class_name = dotted_path.rsplit(":", 1)
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


_engines_cache: dict[str, type[EcosystemBackendEntrypoint]] | None = None


def list_engines() -> dict[str, type[EcosystemBackendEntrypoint]]:
    """Discover all registered ecosystem map backends.

    Returns backends from entry points, falling back to built-in backends
    for editable installs where entry points may not be registered.
    """
    global _engines_cache
    if _engines_cache is not None:
        return _engines_cache

    engines: dict[str, type[EcosystemBackendEntrypoint]] = {}

    # Try entry points first
    eps = entry_points(group=ENTRY_POINT_GROUP)
    for ep in eps:
        engines[ep.name] = ep.load()

    # Fallback: load built-in backends not already discovered via entry points
    if not engines:
        for name, dotted_path in _BUILTIN_BACKENDS.items():
            if name not in engines:
                try:
                    engines[name] = _load_class(dotted_path)
                except (ImportError, AttributeError):
                    pass

    _engines_cache = engines
    return engines


def refresh_engines() -> None:
    """Clear the engine cache, forcing re-discovery on next call."""
    global _engines_cache
    _engines_cache = None


def open_ecosystem_map(data, *, engine: str | None = None, **kwargs) -> "EcosystemMap":
    """Open an ecosystem map using auto-detection or an explicit engine.

    Args:
        data: Data source (file path, gs:// URI, EE asset ID, or EE object).
        engine: Backend name (e.g., 'parquet', 'ee_vector'). If None,
            backends are tried in priority order.
        **kwargs: Passed to the backend's open_ecosystem_map method.

    Returns:
        An EcosystemMap subclass instance.

    Raises:
        ValueError: If no backend can handle the data, or if the named
            engine is not found.
    """
    engines = list_engines()

    if engine is not None:
        if engine not in engines:
            available = ", ".join(sorted(engines.keys()))
            raise ValueError(
                f"Unknown engine {engine!r}. Available engines: {available}"
            )
        return engines[engine].open_ecosystem_map(data, **kwargs)

    # Auto-detect: try backends sorted by priority
    sorted_backends = sorted(engines.items(), key=lambda x: x[1].priority)
    for name, backend in sorted_backends:
        if backend.guess_can_open(data):
            return backend.open_ecosystem_map(data, **kwargs)

    raise ValueError(
        f"No backend can handle data: {data!r}. "
        f"Available engines: {', '.join(sorted(engines.keys()))}"
    )
