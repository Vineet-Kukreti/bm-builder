"""Application use-cases (orchestration) lifted out of the UI layer.

Each function runs one LLM step and returns plain data — no Streamlit, no session
state — so the UI is a thin caller and the orchestration logic is unit-testable.
One-directional dependency: usecases -> core.
"""
from engine.core import (
    ASSIGNABLE_ROLES,
    CEO_MODEL,
    CORE_TEAM,
    MODEL_REGISTRY,
    call_agent,
    is_engine_error,
    provider_family,
    role_provider,
    safe_json,
    validate_assignment,
)


def staff_team(brief, model=None):
    """CEO picks the delivery roster for a project brief.

    Returns ``{"assignment": {role: model}, "rationale": str}`` with the assignment
    validated (gaps filled, designer forced vision-capable). Never raises.
    """
    # Each role's provider family follows the operator's per-agent choice in Settings.
    fams = {r: provider_family(role_provider(r)) for r in ASSIGNABLE_ROLES}
    by_fam = {}
    for name, meta in MODEL_REGISTRY.items():
        by_fam.setdefault(meta["provider"], []).append(
            f"{name} ({'vision' if meta['vision'] else 'text'}): {meta['desc']}")
    menu = "".join(f"\n{fam.upper()} models:\n" + "\n".join(f"  - {m}" for m in models)
                   for fam, models in by_fam.items())
    role_lines = "\n".join(f"- {r}: assign a {fams[r].upper()} model (the operator set this agent's provider)"
                           for r in ASSIGNABLE_ROLES)
    prompt = (
        "You are staffing the delivery team for a new project. The operator has chosen each agent's "
        "AI provider in Settings — assign each role a specific MODEL from its REQUIRED provider "
        "family below, optimising quality per role.\n"
        "- The DEVELOPER must produce REAL, runnable, multi-file code — pick a strong model.\n"
        "- The DESIGNER does visual front-end review, so it MUST be vision-capable.\n\n"
        f"=== REQUIRED PROVIDER PER ROLE ===\n{role_lines}\n\n"
        f"=== AVAILABLE MODELS ==={menu}\n\n"
        f"=== PROJECT BRIEF ===\n{brief}\n\n"
        'Respond with valid JSON only: {"assignment": {"CMO": "<model>", "DEVELOPER": "<model>", '
        '"QA": "<model>", "DESIGNER": "<model>", "PM": "<model>"}, "rationale": "<why>"}'
    )
    raw = call_agent("CEO", "Respond with valid JSON only.", prompt, model=model or CEO_MODEL)
    data = safe_json(raw, default={})
    return {"assignment": validate_assignment(data.get("assignment", {}), fams),
            "rationale": data.get("rationale", "")}


def next_brainstorm_batch(context, model=None):
    """Moderator returns 1-3 distinct next items + a build-readiness assessment.

    Returns ``{"items", "readiness", "coverage", "missing", "done", "error"}``.
    On a provider failure ``error`` holds the sentinel and ``items`` is empty.
    Never raises.
    """
    prompt = (
        "You are moderating a scoping session for an AI solutions studio. The exec team is CEO "
        "(business/scope/risk), CTO (architecture/feasibility/security), CMO (market/users/UX).\n\n"
        "Raise 1 to 3 DISTINCT, non-overlapping NEXT items (fewer as understanding nears "
        "complete). Each item is a \"question\" (needs an answer) or a \"suggestion\" (a proactive "
        "idea, constraint, feature or risk the operator can Agree/Disagree with). NEVER repeat "
        "anything already covered below. Attribute each to CEO, CTO or CMO. Also assess overall "
        "build-readiness (0-100) and per-area coverage.\n\n"
        f"=== PROJECT SO FAR ===\n{context}\n=== END ===\n\n"
        "Respond with valid JSON only:\n"
        '{"items": [{"type": "question|suggestion", "agent": "CEO|CTO|CMO", "text": "..."}], '
        '"done": false, "readiness": 0-100, "coverage": {"scope":0-100,"tech":0-100,'
        '"market":0-100,"ux":0-100,"risk":0-100}, "missing": ["short gap bullets"]}\n'
        "If nothing high-value remains, return items: [] and done: true with the final readiness."
    )
    raw = call_agent("CEO", "You are the team moderator. Respond with valid JSON only.",
                     prompt, model=model or CEO_MODEL)
    if is_engine_error(raw):
        return {"items": [], "readiness": 0, "coverage": {}, "missing": [], "done": False, "error": raw}
    data = safe_json(raw, default={})
    clean = []
    for it in (data.get("items", []) or [])[:3]:
        text = (it.get("text") or "").strip()
        if not text:
            continue
        agent = (it.get("agent") or "CEO").upper()
        if agent not in CORE_TEAM:
            agent = "CEO"
        itype = it.get("type", "question")
        if itype not in ("question", "suggestion"):
            itype = "question"
        clean.append({"type": itype, "agent": agent, "text": text})
    return {
        "items": clean,
        "readiness": int(data.get("readiness", 0) or 0),
        "coverage": data.get("coverage", {}) or {},
        "missing": data.get("missing", []) or [],
        "done": bool(data.get("done")) or (not clean),
        "error": "",
    }
