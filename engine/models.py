"""Lightweight typed shapes for the engine's core artifacts.

The engine persists plain JSON dicts (so files stay human-readable and forward/
backward compatible). These ``TypedDict`` definitions document the *expected*
shape of each artifact for editors and readers — they are intentionally
``total=False`` (every key optional) so they describe, but never enforce, the
data. Import them for type hints; the runtime still passes ordinary dicts.
"""
from typing import Dict, List, TypedDict


class PhaseCost(TypedDict, total=False):
    usd: float
    input: int
    output: int
    calls: int


class Cost(TypedDict, total=False):
    """costs.json — per-project API spend ledger."""
    total_usd: float
    input_tokens: int
    output_tokens: int
    calls: int
    by_phase: Dict[str, PhaseCost]


class Status(TypedDict, total=False):
    """status.json — live state of the current build/planning run."""
    phase: str            # "planning" | "build" | ...
    engine: str           # "claude_code" | ...
    running: bool
    progress: int         # 0-100
    action: str
    started_at: str
    finished_at: str
    error: str
    interrupted: bool
    incomplete: bool
    synced: bool
    cancelled: bool
    cc_summary: str
    qa_summary: str


class RoadmapItem(TypedDict, total=False):
    id: str
    title: str
    detail: str
    version: str          # e.g. "v1 (MVP)", "v2", "Backlog"
    priority: str


class Roadmap(TypedDict, total=False):
    versions: List[str]
    items: List[RoadmapItem]
    next_id: int


class BoardTask(TypedDict, total=False):
    id: str
    title: str
    state: str            # "backlog" | "dev" | "done" | "error"
    assignee: str
    note: str


class ProjectState(TypedDict, total=False):
    """project.json — resumable per-project state shown on the dashboard."""
    name: str
    created_at: str
    updated_at: str
    stage: str            # "setup" | "brainstorm" | "planning" | "development" | "done"
    seed: str
    readiness: int
    team: List[str]
    model_map: Dict[str, str]
    prd_content: str
    plan_content: str
    state_summary: str
