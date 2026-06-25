"""BM Builder — engine facade.

The orchestration engine was refactored into the ``engine/`` package (see
``engine/core.py`` and the feature modules). This module re-exports the engine's
public API so existing call sites — ``from dashboard_engine import ...`` in
``app.py`` and the tests — keep working unchanged.

Import from ``engine.core`` (or the focused submodules) in new code; this facade
exists for backward compatibility.
"""

from engine.core import *            # noqa: F401,F403  (public engine API)
from engine.graph import *           # noqa: F401,F403  (build_graph_dot)
from engine.reports import *         # noqa: F401,F403  (build_client_report, _md_to_html_doc)
from engine.usecases import *        # noqa: F401,F403  (staff_team, next_brainstorm_batch)

# A few intentionally-private helpers that callers import explicitly (``import *``
# skips leading-underscore names):
from engine.core import (            # noqa: F401
    _now,
    _list_code_files,
    _any_build_active,
)
