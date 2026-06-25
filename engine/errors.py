"""Engine error types and the call_agent failure-sentinel detector.

``call_agent`` is deliberately fail-soft: on any provider failure it returns a
distinctive *sentinel string* (e.g. ``"Claude Engine Error (model): ..."``) rather
than raising, so a background worker never crashes the UI. ``is_engine_error``
lets callers fail-closed on such a result instead of persisting it as success.

``EngineError`` is provided for call sites that prefer to raise/translate a failure
at a boundary; the sentinel-string contract remains the default for backward
compatibility.
"""
import re


class EngineError(Exception):
    """Raised (by opt-in callers) when an engine operation fails.

    The default ``call_agent`` path still returns a sentinel string; use
    ``is_engine_error`` to detect those. Prefer raising ``EngineError`` in new
    boundary code that wants normal exception handling.
    """


# Matches the sentinels call_agent returns: 'Engine Error (...)', 'Claude Engine
# Error (...)', 'Local Engine Error (...)'. Specific (model id in parens + colon)
# so it won't trip on prose that merely discusses errors.
_ENGINE_ERROR_RE = re.compile(r"(?:Claude |Local )?Engine Error \([^)]*\):")


def is_engine_error(text):
    """True if `text` is (or contains) a call_agent failure sentinel."""
    return bool(text) and bool(_ENGINE_ERROR_RE.search(text))
