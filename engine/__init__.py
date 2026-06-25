"""BM Builder engine package.

The orchestration engine lives here, split by concern:

- core.py       — kernel: providers/LLM routing, model registry, persistence,
                  status/board, cost ledger, settings, build jobs, planning.
- errors.py     — EngineError + the call_agent failure-sentinel detector.
- models.py     — lightweight typed shapes for the core artifacts.
- graph.py      — Graphviz DOT generation for the brainstorm whiteboard.
- reports.py    — project summary export (markdown + standalone HTML).

`dashboard_engine.py` at the repo root re-exports this package's public API, so
existing `from dashboard_engine import ...` call sites keep working unchanged.
"""
