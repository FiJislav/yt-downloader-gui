"""Single source of truth for the application version."""
with open(__file__.replace("__version__.py", "../VERSION")) as _f:
    __version__ = _f.read().strip()
