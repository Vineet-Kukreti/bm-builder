# BM Builder — AI App Studio
# Copyright 2026 Vineet Kukreti (Bespoke Mind AI) — https://bespokemind.ai
# Licensed under the Apache License, Version 2.0. See LICENSE and NOTICE.
import os
import html
import hashlib
from datetime import datetime

import streamlit as strl

try:
    from streamlit_sortables import sort_items
    _HAS_SORT = True
except Exception:
    _HAS_SORT = False

# --- Build / stale-code indicator -------------------------------------------
# Streamlit caches imported modules for the life of the server process, so source
# edits aren't picked up until a restart. We capture the signature of the loaded
# code ONCE (cache_resource = process lifetime) and compare it to a live read each
# render, so the sidebar can warn when the running code is stale.
_SRC_FILES = ("app.py", "dashboard_engine.py", "theme.py")


def _code_signature():
    h = hashlib.md5()
    here = os.path.dirname(os.path.abspath(__file__))
    for fn in _SRC_FILES:
        try:
            with open(os.path.join(here, fn), "rb") as f:
                h.update(f.read())
        except OSError:
            pass
    return h.hexdigest()[:8]


@strl.cache_resource
def _loaded_build():
    """Signature + time of the code as it was when this server process started."""
    return {"sig": _code_signature(), "at": datetime.now().strftime("%H:%M:%S")}

# Premium styling for the drag-and-drop roadmap board.
_ROADMAP_SORT_CSS = """
.sortable-component { font-family: 'Segoe UI', sans-serif; gap: 14px; }
.sortable-container {
  background-color: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 14px; padding: 8px; min-width: 180px;
}
.sortable-container-header {
  background-color: #0f172a; color: #ffffff; border-radius: 10px;
  padding: 9px 14px; font-weight: 600; font-size: 0.9rem; letter-spacing: .2px;
}
.sortable-container-body { padding: 10px 4px 2px; }
.sortable-item {
  box-sizing: border-box;
  background-color: #ffffff; color: #0f172a; border: 1px solid #e2e8f0;
  border-radius: 11px; padding: 11px 13px; margin-bottom: 9px; font-size: 0.85rem;
  box-shadow: 0 1px 2px rgba(15,23,42,0.06); cursor: grab;
  transition: box-shadow .15s ease, border-color .15s ease;
}
/* Hover changes ONLY paint (shadow + border colour). Hard-lock geometry so the card never
   resizes or moves on hover — any size/position change pulls the edge off the cursor and the
   hover toggles on/off in a flicker loop. The !important overrides the component's own hover CSS. */
.sortable-item:hover {
  box-shadow: 0 6px 16px rgba(15,23,42,0.14) !important;
  border-color: #b89339 !important;
  transform: none !important; padding: 11px 13px !important; margin-bottom: 9px !important;
  height: auto !important; min-height: 0 !important;
}
.sortable-item.dragging { box-shadow: 0 10px 24px rgba(184,147,57,0.30); border-color: #b89339; }
"""

from dashboard_engine import (
    call_agent,
    safe_json,
    encode_image,
    engine_status,
    model_for,
    MODEL_REGISTRY,
    CORE_TEAM,
    CEO_MODEL,
    ASSIGNABLE_ROLES,
    ROUTABLE_ROLES,
    DEFAULT_ASSIGNMENT,
    init_project,
    project_paths,
    log_history,
    log_bug,
    read_bugs,
    save_project_state,
    load_project_state,
    list_projects,
    build_graph_dot,
    read_status, reconcile_status, _list_code_files, cancel_build, write_status, _now,
    read_board,
    read_roadmap,
    write_roadmap,
    read_blueprint,
    sync_from_folder,
    save_reference,
    list_references,
    read_datamodel,
    write_datamodel,
    record_lessons,
    build_client_report,
    start_claude_code_build_tasks,
    open_in_vscode,
    prepare_vscode_build,
    generate_run_guide,
    start_claude_code_build,
    claude_code_available,
    vscode_available,
    node_available,
    start_planning,
    role_provider,
    provider_family,
    set_cost_context,
    clear_cost_context,
    read_costs,
    read_settings,
    write_settings,
    PROVIDER_CHOICES,
    delete_project,
    _any_build_active,
)

# Orchestration use-cases (LLM step + parse, no Streamlit) live in the engine; the UI
# functions below are thin glue over these.
from engine.usecases import staff_team, next_brainstorm_batch

import theme        # premium chrome (theme polish; no logic changes)

strl.set_page_config(page_title="BM Builder — AI App Studio", layout="wide")
theme.inject()      # apply the premium look to every page/flow

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
DEFAULTS = {
    "stage": "dashboard",        # dashboard → setup → brainstorm → planning → development → done
    "active_project": "",
    "seed": "",
    "brainstorm_items": [],      # resolved: {type, agent, text, response}
    "current_batch": [],         # pending items: [{type, agent, text}]
    "brainstorm_done": False,
    "readiness": 0,
    "coverage": {},
    "missing": [],
    "model_map": dict(DEFAULT_ASSIGNMENT),
    "model_rationale": "",
    "planning_options": {"research": False, "blueprint": True, "acceptance": True,
                         "tech_spec": True, "datamodel": True, "redteam": True},
    "team": list(CORE_TEAM),
    "prd_content": "",
    "plan_content": "",
    "visual_report": "",
    "gen_error": "",
}
for key, val in DEFAULTS.items():
    if key not in strl.session_state:
        strl.session_state[key] = val

# Reset cost attribution at the start of every run; each costed op sets its own
# context just before its API call (background threads set theirs separately).
clear_cost_context()

ICONS = {"Operator": "You", "CEO": "CEO", "CTO": "CTO", "CMO": "CMO",
         "DEVELOPER": "Dev", "QA": "QA", "DESIGNER": "Design", "PM": "PM"}

strl.markdown(
    '<div style="display:flex;align-items:baseline;gap:.6rem;margin:.1rem 0 1.1rem">'
    '<span style="font-size:1.6rem;font-weight:800;letter-spacing:-.03em;color:#1c1917">BM Builder</span>'
    '<span style="color:#a8a29e;font-weight:600;letter-spacing:-.01em">AI App Studio</span></div>',
    unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with strl.sidebar:
    # --- Brand -----------------------------------------------------------
    strl.markdown(
        '<div style="font-weight:800;letter-spacing:-.02em;font-size:1.12rem;color:#13402b;'
        'margin:.1rem 0 0">BM Builder</div>'
        '<div style="color:#a8a29e;font-size:.72rem;font-weight:600;letter-spacing:.02em;'
        'margin:0 0 .8rem">AI APP STUDIO</div>', unsafe_allow_html=True)

    # --- Navigate (most-used actions first) ------------------------------
    nav1, nav2 = strl.columns(2)
    if nav1.button("Dashboard", width="stretch"):
        strl.session_state.stage = "dashboard"
        strl.rerun()
    if nav2.button("Settings", width="stretch"):
        strl.session_state.stage = "settings"
        strl.rerun()
    if strl.button("Setup & checks", width="stretch", key="nav_doctor"):
        strl.session_state.stage = "doctor"
        strl.rerun()

    # --- Workspace folder (set once; collapsed to stay calm) -------------
    _default_builds = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace_builds")
    with strl.expander("Workspace folder", expanded=False):
        base_dir = strl.text_input("Builds path:", value=_default_builds,
                                   help="Each project gets its own folder here. Defaults to a "
                                        "'workspace_builds' folder beside the app.")

    # --- Current project card --------------------------------------------
    if strl.session_state.active_project:
        _name = strl.session_state.active_project
        _pstage = (load_project_state(base_dir, _name) or {}).get("stage", strl.session_state.stage)
        _SLAB = {"setup": "Setup", "brainstorm": "Brainstorm", "planning": "Planning",
                 "development": "Development", "done": "Delivered"}
        with strl.container(border=True):
            strl.markdown(f"**{html.escape(_name)}**")
            _cost = read_costs(base_dir, _name).get("total_usd", 0)
            strl.markdown(theme.chip(_SLAB.get(_pstage, "In progress"), "gold")
                          + f' <span style="color:#78716c;font-size:.78rem">· ${_cost:.2f} API</span>',
                          unsafe_allow_html=True)
            with strl.expander("Roster & models", expanded=False):
                for agent in strl.session_state.team:
                    m = CEO_MODEL if agent == "CEO" else model_for(agent, strl.session_state.model_map)
                    tag = "core" if agent in CORE_TEAM else "hired"
                    strl.markdown(f"**{agent}** · _{tag}_  \n`{m}`")

    # --- AI engine status -------------------------------------------------
    strl.markdown("**AI engine**")
    _es = engine_status()
    if not _es["anthropic_pkg"]:
        strl.markdown(theme.chip("anthropic package missing", "red"), unsafe_allow_html=True)
        strl.caption("Run `pip install -r requirements.txt`, then restart.")
    else:
        strl.markdown(theme.chip("Ready", "green"), unsafe_allow_html=True)
        strl.caption("Build runs on Claude subscription ($0). Per-agent AI below · verify in **Setup & checks**.")

    # --- Per-agent AI (read-only summary; edit in Settings) --------------
    _PROV_SHORT = {"claude_subscription": "Subscription", "anthropic": "Claude API",
                   "openai": "OpenAI", "openai_compatible": "OpenAI-compatible"}
    with strl.expander("Per-agent AI", expanded=False):
        for ag in ROUTABLE_ROLES:
            strl.markdown(f"<span class='osw-chip gray'>{ag}</span> "
                          f"{_PROV_SHORT.get(role_provider(ag), role_provider(ag))}",
                          unsafe_allow_html=True)
        strl.caption("Change which AI each agent uses in **Settings → AI per agent**.")

    # --- Footer: reset (+ a quiet warning only if the source changed on disk) --
    strl.markdown("---")
    if _code_signature() != _loaded_build()["sig"]:
        strl.warning("⚙️ The app's source changed on disk — **restart** to apply (Ctrl+C, then run again).")
    if strl.button("Reset session", width="stretch",
                   help="Clears the current view and returns to the dashboard. Your saved projects, "
                        "API keys and settings are NOT deleted."):
        strl.session_state.clear()
        strl.rerun()
    strl.caption("Clears the current view — your saved projects aren't touched.")

    # --- Authorship / Bespoke Mind AI -----------------------------------
    strl.markdown(
        '<div style="margin-top:.7rem;padding-top:.6rem;border-top:1px solid #e8e2d6;'
        'font-size:.72rem;color:#a8a29e;line-height:1.6">'
        'Built by <b style="color:#6f675b">Vineet Kukreti</b><br>'
        '<a href="https://bespokemind.ai" target="_blank" style="color:#13402b;font-weight:600">Bespoke Mind AI</a>'
        ' · <a href="https://linkedin.com/in/vineet-kukreti" target="_blank" style="color:#13402b;font-weight:600">LinkedIn</a>'
        '<br><span style="color:#c4bdb0">© 2026 · Apache-2.0</span></div>',
        unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def persist():
    """Snapshot the active project to project.json."""
    name = strl.session_state.active_project
    if not name:
        return
    save_project_state(base_dir, name, {
        "stage": strl.session_state.stage,
        "seed": strl.session_state.seed,
        "brainstorm_items": strl.session_state.brainstorm_items,
        "current_batch": strl.session_state.current_batch,
        "brainstorm_done": strl.session_state.brainstorm_done,
        "readiness": strl.session_state.readiness,
        "coverage": strl.session_state.coverage,
        "missing": strl.session_state.missing,
        "model_map": strl.session_state.model_map,
        "model_rationale": strl.session_state.model_rationale,
        "team": strl.session_state.team,
        "prd_content": strl.session_state.prd_content,
        "plan_content": strl.session_state.plan_content,
    })


def open_project(name):
    st = load_project_state(base_dir, name) or {}
    strl.session_state.active_project = name
    for k in ("seed", "brainstorm_items", "current_batch", "brainstorm_done", "readiness",
              "coverage", "missing", "model_map", "model_rationale", "team",
              "prd_content", "plan_content"):
        if k in st and st[k] is not None:
            strl.session_state[k] = st[k]
    strl.session_state.visual_report = ""
    strl.session_state.gen_error = ""          # don't carry one project's brainstorm error into another
    strl.session_state.stage = st.get("stage", "brainstorm")


def new_project():
    for k, v in DEFAULTS.items():
        if k not in ("stage",):
            strl.session_state[k] = (list(v) if isinstance(v, list)
                                     else dict(v) if isinstance(v, dict) else v)
    strl.session_state.stage = "setup"


def _reset_after_delete():
    """Clear the now-deleted active project from session state and return to the dashboard."""
    for k, v in DEFAULTS.items():
        strl.session_state[k] = (list(v) if isinstance(v, list)
                                 else dict(v) if isinstance(v, dict) else v)
    strl.session_state.stage = "dashboard"


def check_requirements(force=False):
    """Detect (and cache) whether Node.js, Claude Code and VS Code CLIs are available."""
    if force or "_reqs" not in strl.session_state:
        strl.session_state._reqs = {"claude": claude_code_available(),
                                    "vscode": vscode_available(),
                                    "node": node_available()}
    return strl.session_state._reqs


def format_items(items):
    if not items:
        return "(nothing discussed yet)"
    out = []
    for it in items:
        if it["type"] == "question":
            out.append(f"[{it['agent']} asked] Q: {it['text']}\n   Operator answered: {it['response']}")
        else:
            out.append(f"[{it['agent']} suggested] {it['text']}\n   Operator: {it['response']}")
    return "\n\n".join(out)


def assign_models(brief):
    """Thin UI glue: run the staffing use-case and store its result in session state."""
    set_cost_context(base_dir, strl.session_state.active_project, "staffing")
    result = staff_team(brief)
    strl.session_state.model_map = result["assignment"]
    strl.session_state.model_rationale = result["rationale"]
    log_history(base_dir, strl.session_state.active_project, "CEO",
                "Model roster assigned:\n"
                + "\n".join(f"- {r}: {m}" for r, m in strl.session_state.model_map.items())
                + f"\nRationale: {strl.session_state.model_rationale}")


def kick_off_planning():
    """Ensure the delivery roster is hired and start PRD/plan authoring in the
    background. Resets the planning auto-advance flag so the new run can advance."""
    name = strl.session_state.active_project
    for h in ("PM", "DEVELOPER", "QA", "DESIGNER"):
        if h not in strl.session_state.team:
            strl.session_state.team.append(h)
    strl.session_state.prd_content = ""
    strl.session_state.plan_content = ""
    strl.session_state[f"_adv_planning_{name}"] = False
    persist()
    # Pre-write running synchronously BEFORE the rerun so the planning screen never briefly reads the
    # PRIOR run's stale finished_at and flashes the "didn't produce a PRD" recovery branch.
    write_status(base_dir, name, phase="planning", running=True, progress=0,
                 action="Starting planning…", started_at=_now(), finished_at=None, error=None)
    discussion = strl.session_state.seed + "\n\n" + format_items(strl.session_state.brainstorm_items)
    start_planning(base_dir, name, strl.session_state.seed, discussion,
                   strl.session_state.team, strl.session_state.model_map,
                   options=strl.session_state.get("planning_options", {}))


def plan_next_version(name):
    """Start a fresh brainstorm for the next version, seeding the team with the
    current build state (from Sync) and the deferred roadmap items."""
    st = load_project_state(base_dir, name) or {}
    state_summary = st.get("state_summary", "")
    rm = read_roadmap(base_dir, name)
    versions = rm.get("versions", [])
    v1 = versions[0] if versions else "v1 (MVP)"
    deferred = [it for it in rm.get("items", []) if it.get("version") != v1]
    deferred_txt = "\n".join(f"- [{it.get('version')}] {it.get('title')}: {it.get('detail', '')}"
                             for it in deferred)
    seed = ("PLANNING THE NEXT VERSION.\n\n"
            + (f"CURRENT BUILD STATE:\n{state_summary}\n\n" if state_summary else
               "(Tip: click 'Sync from folder' first so the team knows the current code state.)\n\n")
            + (f"DEFERRED / NEXT-VERSION IDEAS FROM THE ROADMAP:\n{deferred_txt}\n\n" if deferred_txt else "")
            + "Discuss and scope the next version with the team.")
    strl.session_state.seed = seed
    strl.session_state.brainstorm_items = []
    strl.session_state.current_batch = []
    strl.session_state.brainstorm_done = False
    strl.session_state.prd_content = ""
    strl.session_state.plan_content = ""
    strl.session_state.stage = "brainstorm"
    persist()
    with strl.spinner("The team is reviewing the current state and preparing questions…"):
        generate_next_batch()
    persist()


def generate_next_batch():
    """Thin UI glue: run the brainstorm use-case and store its result in session state."""
    set_cost_context(base_dir, strl.session_state.active_project, "brainstorm")
    strl.session_state.gen_error = ""
    # Monotonic batch counter → unique widget keys per batch (len(items) doesn't change on
    # "Ask for more", so it aliased keys and pre-filled stale answers).
    strl.session_state.batch_seq = strl.session_state.get("batch_seq", 0) + 1
    context = strl.session_state.seed + "\n\n" + format_items(strl.session_state.brainstorm_items)
    result = next_brainstorm_batch(context)
    if result["error"]:
        strl.session_state.gen_error = result["error"]
        strl.session_state.current_batch = []
        return
    strl.session_state.readiness = result["readiness"]
    strl.session_state.coverage = result["coverage"]
    strl.session_state.missing = result["missing"]
    strl.session_state.current_batch = result["items"]
    strl.session_state.brainstorm_done = result["done"]


def render_insight_panel():
    """Readiness verdict + coverage bars + knowledge graph."""
    r = strl.session_state.readiness
    if r >= 80:
        strl.success(f"Readiness {r}% — strong understanding, good to build.")
    elif r >= 50:
        strl.info(f"Readiness {r}% — solid; more answers will sharpen the plan.")
    else:
        strl.warning(f"Readiness {r}% — needs more answers for a strong plan.")
    strl.progress(min(max(r, 0), 100) / 100)

    cov = strl.session_state.coverage or {}
    if cov:
        strl.caption("Coverage by area")
        for area in ("scope", "tech", "market", "ux", "risk"):
            if area in cov:
                strl.caption(f"{area.title()} — {int(cov[area])}%")
                strl.progress(min(max(int(cov[area]), 0), 100) / 100)
    if strl.session_state.missing:
        strl.caption("Still needed: " + "; ".join(strl.session_state.missing))

    strl.markdown("**Planning whiteboard**")
    strl.graphviz_chart(build_graph_dot(strl.session_state.brainstorm_items, r))


def _elapsed_str(started_at):
    if not started_at:
        return ""
    try:
        t0 = datetime.strptime(started_at, "%Y-%m-%d %H:%M:%S")
        secs = int((datetime.now() - t0).total_seconds())
        if secs < 0:
            return ""
        m, s = divmod(secs, 60)
        return f"{m}m{s:02d}s elapsed" if m else f"{s}s elapsed"
    except Exception:
        return ""


def _phase_label(s):
    return "Planning" if (s or {}).get("phase") == "planning" else "Build"


def _activity_feed(name, limit=8):
    """Most-recent changelog entries (newest first) for the live team feed."""
    path = project_paths(base_dir, name)["changelog"]
    if not os.path.exists(path):
        return []
    try:
        txt = open(path, encoding="utf-8").read()
    except Exception:
        return []
    entries = []
    for part in txt.split("\n### ")[1:]:
        head, _, body = part.partition("\n")
        ts, _, agent = head.partition("—")
        agent = agent.strip()
        entries.append({"ts": ts.strip(), "agent": agent,
                        "icon": ICONS.get(agent, ""), "msg": body.strip()[:280]})
    return entries[-limit:][::-1]


BUILD_LANES = [("To do", "backlog"), ("In Development", "dev"),
               ("In QA", "qa"), ("Done", "done")]
PLANNING_LANES = [("To draft", "backlog"), ("Drafting", "dev"), ("Done", "done")]


def _render_board(name):
    """Kanban board read from board.json — ONE renderer shared by the planning stage, the dev-stage
    live build view, and the orchestration tab. Failed cards surface in Done with their note."""
    board = read_board(base_dir, name)
    if board and board.get("phase"):
        rnd = f" · round {board['round']}" if board.get("round") else ""
        strl.markdown(f"#### {board['phase']}{rnd}")
    if not (board and board.get("tasks")):
        return
    lanes = PLANNING_LANES if board.get("kind") == "planning" else BUILD_LANES
    cols = strl.columns(len(lanes))
    for (title, key), col in zip(lanes, cols):
        with col:
            items = [t for t in board["tasks"]
                     if t.get("state") == key or (key == "done" and t.get("state") == "error")]
            strl.markdown(f"**{title}** ({len(items)})")
            for t in items:
                with strl.container(border=True):
                    strl.markdown(f"**{t.get('title', '')}**")
                    if t.get("purpose"):
                        strl.caption(t["purpose"])
                    line = " · ".join(x for x in [t.get("assignee", ""), t.get("note", "")] if x)
                    if line:
                        strl.caption(line)


@strl.fragment(run_every=2)
def render_orchestration(name):
    """Live development view: progress + cost, phase banner, Kanban board, and
    the team activity feed — all auto-refreshing. Auto-advances when the build
    finishes so the review section appears."""
    s = read_status(base_dir, name)
    if s:
        label = _phase_label(s)
        if s.get("error"):
            strl.error(f"{label} failed: {s['error']}")
        else:
            pct = min(max(int(s.get("progress", 0)), 0), 100)
            elapsed = _elapsed_str(s.get("started_at"))
            strl.progress(pct / 100, text=f"{label} {pct}% · {s.get('action', '')}"
                          + (f" · {elapsed}" if elapsed else ""))
        c = read_costs(base_dir, name)
        if c.get("total_usd", 0) > 0:
            strl.caption(f"API cost so far: ${c['total_usd']:.2f}")

    _render_board(name)

    feed = _activity_feed(name, limit=8)
    if feed:
        with strl.expander("Team activity (live)", expanded=True):
            for e in feed:
                strl.markdown(f"**{e['agent']}** · {e['ts']}")
                strl.caption(e["msg"])

    if s and not s.get("running") and s.get("finished_at") and not s.get("error"):
        flag = f"_adv_{s.get('phase', 'build')}_{name}"
        if not strl.session_state.get(flag):
            strl.session_state[flag] = True
            strl.rerun()


@strl.fragment(run_every=3)
def render_cc_progress(name):
    """Live progress for an autonomous Claude Code build (long-running subprocess)."""
    reconcile_status(base_dir, name)        # heal an orphaned 'running' (app restarted mid-build)
    s = read_status(base_dir, name) or {}
    if s.get("interrupted"):
        strl.warning(s.get("error", "The build was interrupted. Start it again to continue."))
        return
    if s.get("incomplete"):
        strl.warning(s.get("error", "The build finished but isn't verified. Review the logs or retry."))
        _render_board(name)        # show which features built / failed
        return
    if s.get("cancelled"):
        strl.warning(s.get("error", "Build cancelled. Start a fresh build when you're ready."))
        _render_board(name)
        return
    if s.get("error"):
        strl.error(f"Claude Code: {s['error']}")
        return
    pct = min(max(int(s.get("progress", 0)), 0), 100)
    elapsed = _elapsed_str(s.get("started_at"))
    strl.progress(pct / 100, text=f"Claude Code {pct}% · {s.get('action', '')}"
                  + (f" · {elapsed}" if elapsed else ""))
    _render_board(name)            # live Kanban of the approved v1 features (both build paths)
    if s.get("running"):
        strl.caption("Claude Code is building, running and fixing the project on your subscription "
                     "— this can take several minutes. You can work on another project meanwhile.")
        if strl.checkbox("Stop this build", key=f"cc_cancel_ck_{name}",
                         help="Files created so far are kept; you can start a fresh build anytime."):
            if strl.button("Confirm cancel", key=f"cc_cancel_{name}", type="primary"):
                cancel_build(base_dir, name)
                strl.rerun()
        logp = os.path.join(project_paths(base_dir, name)["history"], "claude_code_build.log")
        if os.path.exists(logp):
            try:
                tail = open(logp, encoding="utf-8").read()[-1500:]
            except Exception:
                tail = ""
            if tail.strip():
                with strl.expander("Claude Code log (live)", expanded=False):
                    strl.code(tail)
    elif s.get("finished_at"):
        strl.success("Claude Code build complete.")
        if not strl.session_state.get(f"_adv_build_{name}"):
            strl.session_state[f"_adv_build_{name}"] = True
            strl.rerun()


def render_finished_common(name, show_reviews=True):
    """The shared 'build finished' view: run guide + keys, optional code reviews,
    visual QA, bug knowledge base, and sign-off."""
    root = project_paths(base_dir, name)["root"]
    st = read_status(base_dir, name) or {}

    rg = os.path.join(root, "RUN_GUIDE.md")
    strl.markdown("## ▶️ How to run & see the front end")
    if os.path.exists(rg):
        with open(rg, encoding="utf-8") as f:
            strl.markdown(f.read())
    else:
        strl.info("No run guide yet for this build.")
        if strl.button("Generate run guide", key=f"genrg_{name}"):
            with strl.spinner("Writing a run guide from the actual files..."):
                generate_run_guide(base_dir, name)
            strl.rerun()
    readme = os.path.join(root, "README.md")
    if os.path.exists(readme):
        with strl.expander("README.md (written during the build)", expanded=False):
            with open(readme, encoding="utf-8") as f:
                strl.markdown(f.read())

    env_vars = st.get("env_vars") or []
    strl.markdown("## What you need to provide")
    if env_vars:
        strl.info("Add these keys to the project's `.env`, then follow the run guide.")
        strl.code("\n".join(f"{v}=" for v in env_vars))
        strl.caption(f"File: `{os.path.join(root, '.env')}`")
    else:
        strl.caption("No external API keys flagged — follow the run guide.")

    if show_reviews:
        strl.markdown("## Reviews")
        strl.markdown("### CTO — code review vs engineering guidelines")
        ca = st.get("cto_aligned")
        if ca is True:
            strl.success("CTO: conforms to the engineering guidelines.")
        elif ca is False:
            strl.warning("CTO: deviations — see below (logged in `bugs.md`).")
        strl.markdown(st.get("cto_summary") or "")
        for v in (st.get("cto_violations") or []):
            strl.caption(f"• [{v.get('severity', '')}] {v.get('file', '')}: {v.get('issue', '')}")
        strl.markdown("### Project Manager — alignment vs PRD & plan")
        pa = st.get("pm_aligned")
        if pa is True:
            strl.success("PM: aligned with the PRD & plan.")
        elif pa is False:
            strl.warning("PM: gaps — see below (logged in `bugs.md`).")
        strl.markdown(st.get("pm_summary") or "")
        for g in (st.get("pm_gaps") or []):
            strl.caption(f"• {g}")
        strl.markdown(f"### QA — {st.get('rounds', 1)} round(s)")
        strl.markdown(st.get("qa_summary") or "_No summary returned._")

    strl.markdown("## Visual front-end QA")
    designer_model = model_for("DESIGNER", strl.session_state.model_map)
    strl.caption(f"Reviewer: **{designer_model}** (vision)")
    shots = strl.file_uploader("Upload front-end screenshots", type=["png", "jpg", "jpeg", "webp"],
                               accept_multiple_files=True, key=f"vqa_{name}")
    if strl.button("Run visual front-end QA", key=f"vqabtn_{name}"):
        if shots:
            with strl.spinner(f"{designer_model} is reviewing the front-end..."):
                images = [encode_image(f.name, f.getvalue()) for f in shots]
                known = read_bugs(base_dir, name)
                vis_prompt = (
                    "Review these front-end screenshots for layout, visual hierarchy, spacing, "
                    "alignment, accessibility, responsiveness and overall UX. First check whether "
                    "any PREVIOUSLY LOGGED FRONTEND BUGS have regressed.\n\n"
                    f"=== PREVIOUSLY LOGGED BUGS ===\n{known}\n\n"
                    'Return JSON: {"summary": str, "issues": [{"title": str, "detail": str, '
                    '"severity": "low|medium|high"}]}.'
                )
                set_cost_context(base_dir, name, "visual_qa")
                vis_raw = call_agent("DESIGNER", "Respond with valid JSON only.", vis_prompt,
                                     model=designer_model, images=images, json_mode=True)
                vis = safe_json(vis_raw, default={"summary": vis_raw, "issues": []})
                strl.session_state.visual_report = vis.get("summary", "")
                for issue in vis.get("issues", []):
                    log_bug(base_dir, name, issue.get("title", "Untitled"),
                            issue.get("detail", ""), issue.get("severity", "medium"), "FRONTEND")
                log_history(base_dir, name, "DESIGNER",
                            f"Visual QA on {len(images)} screenshot(s): "
                            f"{len(vis.get('issues', []))} issue(s) logged.")
            strl.rerun()
        else:
            strl.warning("Upload at least one screenshot first.")
    if strl.session_state.visual_report:
        strl.success("Visual QA complete.")
        strl.markdown(strl.session_state.visual_report)

    strl.markdown("## Bug knowledge base")
    strl.code(read_bugs(base_dir, name), language="markdown")

    _imperfect = bool(st.get("error") or st.get("incomplete"))
    _no_output = not _list_code_files(base_dir, name)
    _ack = True
    if _no_output:
        strl.warning("No source files were produced for this project yet — there's nothing built to "
                     "deliver. Run the build first, or acknowledge below to sign off anyway.")
        _ack = strl.checkbox("Sign off even though nothing was built", key=f"signoff_ack_{name}")
    _label = ("Sign off (nothing built)" if _no_output
              else "Sign off (with known issues)" if _imperfect else "Sign off & complete")
    if strl.button(_label, type="primary", key=f"signoff_{name}", disabled=not _ack):
        with strl.spinner("Capturing lessons learned for future projects…"):
            try:
                record_lessons(base_dir, name)
            except Exception:
                pass
        log_history(base_dir, name, "Operator",
                    "Signed off with no build output." if _no_output else
                    "Signed off with unresolved build issues." if _imperfect
                    else "Signed off. Project complete.")
        strl.session_state.stage = "done"
        persist()
        strl.rerun()


def _safe_label(s, n=42):
    return str(s)[:n].replace("\\", " ").replace('"', "'").replace("\n", " ")


def build_blueprint_dot(bp):
    """Premium left-to-right hierarchy: Project → folders → files → key functions.
    Orthogonal (straight, right-angle) connectors and a refined palette."""
    files = bp.get("files", []) or []
    lines = [
        "digraph G {",
        "  rankdir=LR;",                # horizontal
        "  bgcolor=transparent;",
        "  pad=0.4;",
        "  nodesep=0.30;",
        "  ranksep=0.95 equally;",
        "  splines=ortho;",             # straight right-angle connectors (no curves)
        "  concentrate=true;",
        '  node [shape=box, style="filled,rounded", fontname="Segoe UI", fontsize=11, '
        'penwidth=1.1, margin="0.22,0.13", height=0.44];',
        '  edge [color="#cbd5e1", penwidth=1.2, arrowsize=0.7, arrowhead=normal];',
        '  root [label="Project", fillcolor="#0f172a", fontcolor="#ffffff", color="#0f172a", '
        'fontsize=13, margin="0.30,0.18"];',
    ]
    folders = {}
    for i, f in enumerate(files):
        parts = str(f.get("path", "")).replace("\\", "/").split("/")
        folder = parts[0] if len(parts) > 1 else "(root)"
        folders.setdefault(folder, []).append((i, f))
    for fi, (folder, fl) in enumerate(folders.items()):
        fid = f"fold{fi}"
        lines.append(f'  {fid} [label="{_safe_label(folder)}", fillcolor="#13402b", '
                     f'fontcolor="#ffffff", color="#13402b"];')
        lines.append(f"  root -> {fid};")
        for i, f in fl:
            fileid = f"file{i}"
            fname = str(f.get("path", "")).split("/")[-1]
            lines.append(f'  {fileid} [label="{_safe_label(fname)}", fillcolor="#ffffff", '
                         f'fontcolor="#171411", color="#937326"];')
            lines.append(f"  {fid} -> {fileid};")
            fns = f.get("functions", []) or []
            for j, fn in enumerate(fns[:6]):
                fnid = f"fn{i}_{j}"
                lines.append(f'  {fnid} [label="{_safe_label(fn)}", fillcolor="#f8fafc", '
                             f'fontcolor="#475569", color="#e2e8f0", fontsize=10];')
                lines.append(f"  {fileid} -> {fnid};")
            if len(fns) > 6:
                mid = f"more{i}"
                lines.append(f'  {mid} [label="+{len(fns) - 6} more…", fillcolor="#f8fafc", '
                             f'fontcolor="#94a3b8", color="#f1f5f9", fontsize=9];')
                lines.append(f"  {fileid} -> {mid};")
    lines.append("}")
    return "\n".join(lines)


def _read_artifact(name, fn):
    p = os.path.join(project_paths(base_dir, name)["root"], fn)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    return ""


def render_references(name):
    """Attach & list reference material that grounds the plan and the build."""
    strl.caption("Attach mockups, API docs (OpenAPI), sample data, brand assets. The team uses "
                 "text references to ground the plan, and Claude Code reads everything from the "
                 "`references/` folder during the build.")
    up = strl.file_uploader("Add reference files", accept_multiple_files=True, key=f"refup_{name}")
    if up and strl.button("Save references", key=f"refsave_{name}"):
        for f in up:
            save_reference(base_dir, name, f.name, f.getvalue())
        strl.success(f"Saved {len(up)} reference(s).")
        strl.rerun()
    refs = list_references(base_dir, name)
    if refs:
        strl.markdown("**Attached:**")
        for r in refs:
            strl.caption("• " + r)
    else:
        strl.caption("No references attached yet.")


def render_project_views(name, show_board=True):
    """Unified tabbed view of all project artifacts. `show_board=False` omits the live Kanban
    tab on screens that already show the board elsewhere (the dev-stage build section), so the
    board never renders twice (and we don't run a second auto-refreshing fragment)."""
    _labels = ["Blueprint", "PRD", "Plan", "Guidelines", "Tech spec",
               "Data model", "Acceptance", "Roadmap", "Red-team", "References"]
    if show_board:
        _labels.append("Kanban")
    tabs = strl.tabs(_labels)
    with tabs[0]:
        bp = read_blueprint(base_dir, name)
        if bp.get("summary"):
            strl.caption(bp["summary"])
        if bp.get("files"):
            strl.graphviz_chart(build_blueprint_dot(bp))
            with strl.expander("Files & functions (list)", expanded=False):
                for f in bp["files"]:
                    strl.markdown(f"**{f.get('path', '')}** — {f.get('purpose', '')}")
                    for fn in (f.get("functions", []) or []):
                        strl.caption("• " + str(fn))
        else:
            strl.caption("No blueprint yet — it's generated during planning, or click "
                         "**Sync from folder** to build it from the actual code.")
    with tabs[1]:
        strl.markdown(_read_artifact(name, "prd.md") or strl.session_state.get("prd_content") or "_(none)_")
    with tabs[2]:
        strl.markdown(_read_artifact(name, "plan.md") or strl.session_state.get("plan_content") or "_(none)_")
    with tabs[3]:
        strl.markdown(_read_artifact(name, "TECH_BRIEF.md") or "_(none)_")
    with tabs[4]:
        strl.markdown(_read_artifact(name, "TECH_SPEC.md") or "_(generated during planning)_")
    with tabs[5]:
        render_datamodel_editor(name)
    with tabs[6]:
        strl.markdown(_read_artifact(name, "ACCEPTANCE.md") or "_(generated during planning)_")
    with tabs[7]:
        render_roadmap_editor(name)
    with tabs[8]:
        _sps = (load_project_state(base_dir, name) or {}).get("spec_score")
        if _sps is not None:
            strl.metric("Spec readiness (red-team score)", f"{_sps}/100")
        strl.caption("The Skeptic agent stress-tests the plan before development.")
        strl.markdown(_read_artifact(name, "REDTEAM.md") or "_(generated during planning)_")
    with tabs[9]:
        render_references(name)
    if show_board:
        with tabs[10]:
            render_orchestration(name)

    # --- Team & models: confirm or override the CEO's per-role picks -------
    _editable = [r for r in ASSIGNABLE_ROLES if r in strl.session_state.team]
    if _editable:
        with strl.expander("Team & models — confirm or change the CEO's picks", expanded=False):
            strl.caption("The CEO assigned a model to each role. Override any below — each list is "
                         "limited to that agent's provider (set in **Settings → AI per agent**). "
                         "CEO and CTO are pinned.")
            strl.markdown(f"**CEO** · `{CEO_MODEL}`  ·  **CTO** · `{model_for('CTO', strl.session_state.model_map)}`")
            _mm = dict(strl.session_state.model_map)
            for _role in _editable:
                _prov = role_provider(_role)
                if _prov == "openai_compatible":
                    strl.markdown(f"**{_role}** — uses your OpenAI-compatible model from Settings")
                    continue
                _fam = provider_family(_prov)
                _opts = [m for m, meta in MODEL_REGISTRY.items() if meta["provider"] == _fam]
                if not _opts:
                    continue
                _cur = _mm.get(_role) or model_for(_role, _mm)
                _idx = _opts.index(_cur) if _cur in _opts else 0
                _mm[_role] = strl.selectbox(
                    _role, _opts, index=_idx, key=f"mm_{name}_{_role}",
                    format_func=lambda m: f"{m} · {MODEL_REGISTRY[m]['provider']}")
            if strl.button("Save model choices", key=f"savemm_{name}"):
                strl.session_state.model_map = _mm
                persist()
                strl.toast("Model choices saved.")
                strl.rerun()

    cr1, cr2 = strl.columns([1, 3])
    with cr1:
        if strl.button("Generate summary", key=f"cr_{name}"):
            with strl.spinner("CEO is writing a summary…"):
                build_client_report(base_dir, name)
            strl.rerun()
    crp = os.path.join(project_paths(base_dir, name)["root"], "SUMMARY.md")
    if os.path.exists(crp):
        with cr2:
            with open(crp, encoding="utf-8") as _f:
                strl.download_button("Download summary (.md)", _f.read(),
                                     file_name=f"{name}_summary.md", key=f"crdl_{name}")
            strl.caption(f"Shareable HTML also saved: `{os.path.join(project_paths(base_dir, name)['root'], 'SUMMARY.html')}`")


_PRI_ICON = {"high": "High", "med": "Med", "medium": "Med", "low": "Low"}


def render_roadmap_editor(name):
    """Jira-like version roadmap: versions as columns of feature cards, with
    add / move / delete. Persists to roadmap.json (+ roadmap.md)."""
    rm = read_roadmap(base_dir, name)
    versions = rm.get("versions") or []
    items = rm.get("items") or []

    with strl.expander("Add a feature / version", expanded=False):
        with strl.form(key=f"rm_add_{name}"):
            t = strl.text_input("Feature / item")
            d = strl.text_input("Detail (optional)")
            fc1, fc2 = strl.columns(2)
            with fc1:
                v = strl.selectbox("Version", versions or ["v1 (MVP)"], key=f"rm_addv_{name}")
            with fc2:
                pr = strl.selectbox("Priority", ["high", "med", "low"], index=1, key=f"rm_addp_{name}")
            if strl.form_submit_button("Add item") and t.strip():
                nid = rm.get("next_id", len(items))
                items.append({"id": f"r{nid}", "title": t.strip(), "detail": d.strip(),
                              "version": v, "priority": pr})
                rm["items"] = items
                rm["next_id"] = nid + 1
                write_roadmap(base_dir, name, rm)
                strl.rerun()
        nv1, nv2 = strl.columns([3, 1])
        with nv1:
            newv = strl.text_input("New version name", key=f"rm_newv_{name}",
                                   label_visibility="collapsed", placeholder="New version name (e.g. v4)")
        with nv2:
            if strl.button("Add version", key=f"rm_addvbtn_{name}") and newv.strip():
                if newv.strip() not in versions:
                    versions.append(newv.strip())
                    rm["versions"] = versions
                    write_roadmap(base_dir, name, rm)
                    strl.rerun()

    if not versions:
        strl.caption("No versions yet — add one above. (A roadmap is generated during planning.)")
        return

    if _HAS_SORT:
        strl.caption("**Drag features between versions** to re-plan scope — changes save automatically.")
        # Build a unique label per item so the dragged result maps back to an id.
        label_to_id, containers = {}, []
        for v in versions:
            labels = []
            for it in items:
                if it.get("version") == v:
                    icon = _PRI_ICON.get(it.get("priority", ""), "")
                    base = f"{icon} {it.get('title', '')}".strip()
                    lbl, n = base, 2
                    while lbl in label_to_id:
                        lbl, n = f"{base} ({n})", n + 1
                    label_to_id[lbl] = it["id"]
                    labels.append(lbl)
            containers.append({"header": v, "items": labels})
        arranged = sort_items(containers, multi_containers=True, direction="horizontal",
                              custom_style=_ROADMAP_SORT_CSS, key=f"rm_sort_{name}")
        # Map each returned container back by its header (the version name).
        changed = False
        for cont in (arranged or []):
            v = cont.get("header")
            if v not in versions:
                continue
            for lbl in cont.get("items", []):
                it = next((x for x in items if x["id"] == label_to_id.get(lbl)), None)
                if it and it.get("version") != v:
                    it["version"] = v
                    changed = True
        if changed:
            rm["items"] = items
            write_roadmap(base_dir, name, rm)
            strl.rerun()

        strl.caption("To remove a feature, open **Edit or delete features** below and click its **✕**.")
        with strl.expander("Edit or delete features", expanded=False):
            _opts = ["high", "med", "low"]
            for it in items:
                ec1, ec2, ec3 = strl.columns([5, 2, 1])
                with ec1:
                    strl.markdown(f"{_PRI_ICON.get(it.get('priority', ''), '')} "
                                  f"**{it.get('title', '')}** · _{it.get('version', '')}_")
                    if it.get("detail"):
                        strl.caption(it["detail"])
                with ec2:
                    cur = it.get("priority", "med")
                    np = strl.selectbox("Priority", _opts,
                                        index=_opts.index(cur) if cur in _opts else 1,
                                        key=f"rm_pri_{it['id']}_{name}", label_visibility="collapsed")
                    if np != it.get("priority"):
                        it["priority"] = np
                        write_roadmap(base_dir, name, rm)
                        strl.rerun()
                with ec3:
                    if strl.button("✕", key=f"rm_del_{it['id']}_{name}", help="Delete this feature"):
                        rm["items"] = [x for x in items if x["id"] != it["id"]]
                        write_roadmap(base_dir, name, rm)
                        strl.rerun()
        return

    # Fallback (component unavailable): columns with a "Move to" selectbox.
    strl.caption("Tip: `pip install streamlit-sortables` to enable drag-and-drop.")
    cols = strl.columns(len(versions))
    for v, col in zip(versions, cols):
        with col:
            vitems = [it for it in items if it.get("version") == v]
            strl.markdown(f"**{v}**  ({len(vitems)})")
            for it in vitems:
                with strl.container(border=True):
                    strl.markdown(f"{_PRI_ICON.get(it.get('priority', ''), '')} **{it.get('title', '')}**")
                    if it.get("detail"):
                        strl.caption(it["detail"])
                    mc1, mc2 = strl.columns([3, 1])
                    with mc1:
                        nv = strl.selectbox("Move to", versions, index=versions.index(v),
                                            key=f"rm_mv_{it['id']}_{name}", label_visibility="collapsed")
                        if nv != v:
                            it["version"] = nv
                            write_roadmap(base_dir, name, rm)
                            strl.rerun()
                    with mc2:
                        if strl.button("✕", key=f"rm_del_{it['id']}_{name}", help="Delete this feature"):
                            rm["items"] = [x for x in items if x["id"] != it["id"]]
                            write_roadmap(base_dir, name, rm)
                            strl.rerun()


def render_datamodel_editor(name):
    """Editable schema designer: entities/fields grid + API endpoints grid."""
    dm = read_datamodel(base_dir, name)
    strl.caption("Edit the entities/fields and API endpoints, then Save — written to "
                 "`datamodel.json` + `datamodel.md` (read by the AI during the build).")
    field_rows = []
    for ent in dm.get("entities", []):
        for f in (ent.get("fields", []) or []):
            field_rows.append({"entity": ent.get("name", ""), "field": f.get("name", ""),
                               "type": f.get("type", ""), "notes": f.get("notes", "")})
    if not field_rows:
        field_rows = [{"entity": "", "field": "", "type": "", "notes": ""}]
    strl.markdown("**Entities & fields**")
    ed_f = strl.data_editor(field_rows, num_rows="dynamic", width="stretch",
                            key=f"dm_fields_{name}")
    ep_rows = dm.get("endpoints", []) or [{"method": "", "path": "", "request": "",
                                           "response": "", "notes": ""}]
    strl.markdown("**API endpoints**")
    ed_e = strl.data_editor(ep_rows, num_rows="dynamic", width="stretch",
                            key=f"dm_eps_{name}")
    if strl.button("Save data model & API", key=f"dm_save_{name}"):
        rows = ed_f if isinstance(ed_f, list) else ed_f.to_dict("records")
        eps = ed_e if isinstance(ed_e, list) else ed_e.to_dict("records")
        ents = {}
        for r in rows:
            en, fn = str(r.get("entity") or "").strip(), str(r.get("field") or "").strip()
            if not en or not fn:
                continue
            ents.setdefault(en, []).append({"name": fn, "type": str(r.get("type") or ""),
                                            "notes": str(r.get("notes") or "")})
        endpoints = [{"method": str(r.get("method") or ""), "path": str(r.get("path") or ""),
                      "request": str(r.get("request") or ""), "response": str(r.get("response") or ""),
                      "notes": str(r.get("notes") or "")}
                     for r in eps if str(r.get("path") or "").strip() or str(r.get("method") or "").strip()]
        write_datamodel(base_dir, name, {"entities": [{"name": k, "fields": v} for k, v in ents.items()],
                                         "endpoints": endpoints})
        strl.success("Saved data model & API.")
        strl.rerun()


# --------------------------------------------------------------------------
# Progress stepper for the app/SaaS flow.
# --------------------------------------------------------------------------
_SAAS_STEPS = [("setup", "Setup"), ("brainstorm", "Brainstorm"), ("planning", "Plan"),
               ("development", "Build"), ("done", "Done")]
_SAAS_STAGE_SET = {s for s, _ in _SAAS_STEPS}


def saas_rail(current):
    order = [s for s, _ in _SAAS_STEPS]
    cur_i = order.index(current) if current in order else -1
    chips = ['<span class="osw-chip gray">App / SaaS</span>', '<span class="osw-arrow">·</span>']
    for i, (s, label) in enumerate(_SAAS_STEPS):
        if i < cur_i:
            cls, txt = "done", f"✓ {label}"
        elif i == cur_i:
            cls, txt = "current", f"▶ {label}"
        else:
            cls, txt = "locked", label
        if i:
            chips.append('<span class="osw-arrow">→</span>')
        chips.append(f'<span class="osw-step {cls}">{txt}</span>')
    nm = strl.session_state.get("active_project")
    if nm:
        chips.append('<span class="osw-arrow">·</span>')
        chips.append(theme.chip(nm))     # escapes the (user-supplied) project name
    strl.markdown('<div class="osw-rail">' + "".join(chips) + "</div>", unsafe_allow_html=True)


# Guard against an unknown/corrupted stage (e.g. a stale project.json) → don't render a blank page.
_KNOWN_STAGES = {"dashboard", "settings", "doctor"} | _SAAS_STAGE_SET
if strl.session_state.stage not in _KNOWN_STAGES:
    strl.warning(f"Unknown stage '{strl.session_state.stage}' — returning to the dashboard.")
    strl.session_state.stage = "dashboard"

if strl.session_state.stage in _SAAS_STAGE_SET:
    saas_rail(strl.session_state.stage)


# ==========================================================================
# STAGE — DASHBOARD
# ==========================================================================
if strl.session_state.stage == "dashboard":
    theme.page_header("My Projects",
                      "Describe an app or SaaS idea and the team takes it from brainstorm → plan → "
                      "autonomous build → QA. Everything autosaves to your builds folder.")
    top1, top2, _ = strl.columns([1.2, 1, 4.8])
    with top1:
        if strl.button("New project", type="primary", width="stretch"):
            new_project()
            strl.rerun()
    with top2:
        if strl.button("Refresh", width="stretch"):
            strl.rerun()

    reqs = check_requirements()
    # First-run nudge: if there's no way to run the AI at all, point to the Setup hub.
    if not (engine_status()["anthropic_key"] or reqs["claude"]):
        with strl.container(border=True):
            strl.markdown("#### 👋 First time here? Let's get you set up.")
            strl.caption("No AI provider is configured yet. Open **Setup & checks** to pick how to run "
                         "the AI (Claude subscription or an API key) and verify your machine.")
            if strl.button("Open Setup & checks", type="primary", key="dash_open_doctor"):
                strl.session_state.stage = "doctor"
                strl.rerun()

    ready = reqs["claude"] and reqs["vscode"]
    with strl.expander("What you need to develop projects" + ("" if ready else " — action needed"),
                       expanded=not ready):
        strl.markdown(
            f"- {'✓' if reqs['vscode'] else '—'} **VS Code installed** "
            + ("" if reqs["vscode"] else "→ install from https://code.visualstudio.com and enable "
               "the `code` command (Command Palette → *Shell Command: Install 'code' command in PATH*).") + "\n"
            f"- {'✓' if reqs['node'] else '—'} **Node.js installed** (provides the `npm` command that Claude Code needs) "
            + ("" if reqs["node"] else "→ `winget install OpenJS.NodeJS.LTS` (or https://nodejs.org), then open a "
               "**new** terminal.") + "\n"
            f"- {'✓' if reqs['claude'] else '—'} **Claude Code installed & logged in** "
            + ("" if reqs["claude"] else "→ **after installing Node.js**, run `npm install -g @anthropic-ai/claude-code`, "
               "then `claude` once and sign in with your Claude subscription.") + "\n"
            "- Both development options use **Claude Code on your subscription** (the CEO-assigned "
            "Developer model) — no API cost."
        )
        if strl.button("↻ Re-check"):
            check_requirements(force=True)
            strl.rerun()

    projects = list_projects(base_dir)
    if not projects:
        with strl.container(border=True):
            strl.markdown("#### No projects yet")
            strl.caption("Click **New project** to start an app/SaaS build. The team walks you "
                         "through it, step by step.")
    for proj in projects:
        name = proj.get("name", "?")
        with strl.container(border=True):
            c1, c2, c3 = strl.columns([3.2, 2, 1.5])
            with c1:
                strl.markdown(f"#### {name}")
                strl.markdown(theme.chip("App · SaaS", "gray"), unsafe_allow_html=True)
                _c = read_costs(base_dir, name)
                strl.caption(f"Stage **{proj.get('stage', '?')}** · "
                             f"Readiness {int(proj.get('readiness', 0))}% · "
                             f"Updated {proj.get('updated_at', '?')} · "
                             f"${_c.get('total_usd', 0):.2f}")
            with c2:
                s = reconcile_status(base_dir, name)
                if not s:
                    strl.markdown(theme.chip("Idle", "gray"), unsafe_allow_html=True)
                elif s.get("interrupted"):
                    strl.markdown(theme.chip("Build interrupted", "amber"), unsafe_allow_html=True)
                elif s.get("incomplete"):
                    strl.markdown(theme.chip("Build incomplete", "amber"), unsafe_allow_html=True)
                elif s.get("error"):
                    strl.markdown(theme.chip(f"{_phase_label(s)} failed", "red"), unsafe_allow_html=True)
                elif s.get("running"):
                    pct = min(max(int(s.get("progress", 0)), 0), 100)
                    elapsed = _elapsed_str(s.get("started_at"))
                    strl.progress(pct / 100, text=f"{_phase_label(s)} {pct}%" + (f" · {elapsed}" if elapsed else ""))
                elif s.get("synced"):
                    strl.markdown(theme.chip("Synced", "gray"), unsafe_allow_html=True)
                elif s.get("finished_at"):
                    strl.markdown(theme.chip(f"{_phase_label(s)} complete", "green"), unsafe_allow_html=True)
                else:
                    strl.markdown(theme.chip("Idle", "gray"), unsafe_allow_html=True)
            with c3:
                if strl.button("Open", key=f"open_{name}", width="stretch"):
                    open_project(name)
                    strl.rerun()
                with strl.popover("More"):
                    if strl.button("Open in VS Code", key=f"vsc_{name}", width="stretch"):
                        open_in_vscode(project_paths(base_dir, name)["root"])
                    if strl.button("Sync from folder", key=f"syncdash_{name}", width="stretch"):
                        with strl.spinner("Syncing from the project folder…"):
                            sync_from_folder(base_dir, name)
                        strl.rerun()
                    strl.markdown("---")
                    strl.caption("Danger zone")
                    _busy = _any_build_active(name)
                    if _busy:
                        strl.caption("A build is running — stop it before deleting.")
                    _ok = strl.checkbox(
                        f"Permanently delete '{name}' and all its files",
                        key=f"delck_{name}", disabled=_busy,
                        help=f"Removes the folder {project_paths(base_dir, name)['root']} and everything in "
                             "it — code, history, briefs. This cannot be undone.")
                    if strl.button("Delete project", key=f"delproj_{name}", width="stretch",
                                   disabled=(not _ok) or _busy):
                        ok, msg = delete_project(base_dir, name)
                        if ok:
                            if strl.session_state.get("active_project") == name:
                                _reset_after_delete()
                            strl.toast(msg)
                            strl.rerun()
                        else:
                            strl.warning(msg)
                            # A partial delete (Windows lock) guts the folder; don't keep it as the
                            # active project. A build-active refusal leaves it intact → keep it.
                            if (strl.session_state.get("active_project") == name
                                    and not _any_build_active(name)):
                                _reset_after_delete()
                                strl.rerun()

# ==========================================================================
# STAGE — SETTINGS (global: API keys + the default agent model, both flows)
# ==========================================================================
elif strl.session_state.stage == "settings":
    theme.page_header("Settings",
                      "API keys and the default AI model for your agents. Stored locally and "
                      "applied immediately.")
    if strl.button("← Back to dashboard"):
        strl.session_state.stage = "dashboard"
        strl.rerun()

    # After a save, blank the password inputs *before* they're instantiated this run
    # (Streamlit forbids assigning a widget's key after the widget renders).
    if strl.session_state.pop("_settings_saved", False):
        for _f in ("anthropic", "openai"):
            strl.session_state.pop(f"set_k_{_f}", None)
            strl.session_state.pop(f"set_clr_{_f}", None)

    _cur = read_settings()
    _PROV_LABELS = {
        "claude_subscription": "Claude — Subscription ($0, recommended)",
        "anthropic": "Claude — API (metered)",
        "openai": "OpenAI (metered)",
        "openai_compatible": "OpenAI-compatible (Groq, OpenRouter, custom)",
    }
    _KEY_ENV = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}

    def _key_status(field):
        v = os.environ.get(_KEY_ENV[field], "") or ""
        return (f"Currently set · …{v[-4:]}" if len(v) >= 4 else "Currently set") if v else "Not set"

    # Seed the shared model/base widgets once from saved settings (then the widgets own them).
    strl.session_state.setdefault("set_model", _cur["default_model"].get("model", ""))
    strl.session_state.setdefault("set_base", _cur["default_model"].get("base_url", ""))

    tab_model, tab_keys = strl.tabs(["AI per agent", "API keys"])

    with tab_model:
        strl.caption("Pick the AI each agent runs on. **Default: all on your Claude subscription "
                     "($0).** Agents set to Claude API / OpenAI / Local use the shared model below.")
        _cur_agents = _cur.get("agents", {})
        _def_prov = _cur["default_model"].get("provider", "claude_subscription")
        _acol = strl.columns(2)
        for _i, _ag in enumerate(ROUTABLE_ROLES):
            _ap = _cur_agents.get(_ag, _def_prov)
            with _acol[_i % 2]:
                strl.selectbox(_ag, PROVIDER_CHOICES,
                               index=PROVIDER_CHOICES.index(_ap) if _ap in PROVIDER_CHOICES else 0,
                               format_func=lambda p: _PROV_LABELS.get(p, p), key=f"agprov_{_ag}")
        strl.caption("DEVELOPER & DESIGNER aren't listed: the autonomous build always uses your Claude "
                     "subscription, and visual review uses Claude / a vision model.")

        _chosen = {strl.session_state.get(f"agprov_{ag}", _def_prov) for ag in ROUTABLE_ROLES}
        # Claude agents (subscription / API): the CEO assigns a Claude model per project — nothing
        # to type. Only OpenAI / OpenAI-compatible need a model/endpoint here.
        if "anthropic" in _chosen and not os.environ.get("ANTHROPIC_API_KEY"):
            strl.warning("Some agents use the **Claude API** but no Anthropic key is set — add one in "
                         "**API keys**, or switch them to the Claude subscription.")
        if _chosen & {"openai", "openai_compatible"}:
            with strl.container(border=True):
                strl.markdown("**OpenAI / OpenAI-compatible**")
                strl.text_input("Model name (optional for OpenAI — the CEO picks one; required for OpenAI-compatible)",
                                key="set_model", placeholder="e.g. gpt-4o · llama-3.3-70b-versatile")
                if "openai_compatible" in _chosen:
                    strl.text_input("Base URL (OpenAI-compatible only)", key="set_base",
                                    placeholder="https://api.groq.com/openai/v1")
                if not os.environ.get("OPENAI_API_KEY"):
                    strl.caption("These agents use the OpenAI key — set it in the **API keys** tab.")
        strl.caption("Claude agents are assigned a Claude model by the CEO per project. The autonomous "
                     "code build always runs on your Claude subscription ($0); non-Claude usage is "
                     "billed by your provider and not tracked here.")

    with tab_keys:
        strl.markdown("**Your Anthropic API key** powers the metered agents and visual review. Get one at "
                      "[console.anthropic.com](https://console.anthropic.com/settings/keys), paste it below, "
                      "and click **Save settings**. (Autonomous builds run on your Claude Code subscription "
                      "and don't need a key.)")
        strl.caption("Stored locally in settings.json on your machine (plaintext — same trust model as your "
                     ".env — and git-ignored, so it's never shared). Leave a field blank to keep its current "
                     "value; tick **Clear** to remove a saved key.")
        for _f, _lab in (("anthropic", "Anthropic API key"), ("openai", "OpenAI API key (optional)")):
            strl.text_input(_lab, type="password", key=f"set_k_{_f}",
                            placeholder="leave blank to keep current")
            kc1, kc2 = strl.columns([3, 1])
            kc1.caption(_key_status(_f))
            kc2.checkbox("Clear", key=f"set_clr_{_f}", disabled=not os.environ.get(_KEY_ENV[_f]),
                         help="Remove the saved key when you Save (a key also in .env returns on restart).")

    strl.markdown("---")
    if strl.button("Save settings", type="primary"):
        _model = (strl.session_state.get("set_model", "") or "").strip()
        _base = (strl.session_state.get("set_base", "") or "").strip()
        _newkeys = dict(_cur["keys"])
        for _f in ("anthropic", "openai"):
            if strl.session_state.get(f"set_clr_{_f}"):
                _newkeys[_f] = ""                       # explicit clear
                os.environ.pop(_KEY_ENV[_f], None)
                continue
            _v = (strl.session_state.get(f"set_k_{_f}", "") or "").strip()
            if _v:
                _newkeys[_f] = _v
        _agents = {ag: strl.session_state.get(f"agprov_{ag}", "claude_subscription") for ag in ROUTABLE_ROLES}
        # default_model.provider stays "claude_subscription" (the fallback for delivery roles + the
        # build); model/base_url are the shared model config for any metered/OpenAI/local agent.
        _dm = {"provider": "claude_subscription", "model": _model, "base_url": _base}
        write_settings({"keys": _newkeys, "default_model": _dm, "agents": _agents})
        strl.session_state["_settings_saved"] = True   # blanks the password fields on the next run
        strl.toast("Settings saved and applied.")
        strl.rerun()

# ==========================================================================
# STAGE — SETUP & CHECKS (onboarding hub: provider wizard + live diagnostics)
# ==========================================================================
elif strl.session_state.stage == "doctor":
    theme.page_header("Setup & checks",
                      "Pick how to run the AI, then confirm your machine is ready. "
                      "Aim for green — yellow items are optional.")
    if strl.button("← Back to dashboard", key="doc_back"):
        strl.session_state.stage = "dashboard"
        strl.rerun()

    # ---- 1) Guided provider setup -----------------------------------------
    _PROVS = ["claude_subscription", "anthropic", "openai", "openai_compatible"]
    _PROV_WIZ_LABELS = {
        "claude_subscription": "Claude — Subscription ($0, recommended) · needs Claude Code",
        "anthropic": "Claude — API key (metered)",
        "openai": "OpenAI (metered)",
        "openai_compatible": "OpenAI-compatible (Groq, OpenRouter, custom)",
    }
    with strl.container(border=True):
        strl.markdown("### 1) Choose how to run the AI agents")
        strl.caption("Not sure? Pick **Claude — Subscription**: it's $0 and also powers the one-click "
                     "autonomous build. The other options run the planning agents; the autonomous build "
                     "still needs Claude Code (or use the VS Code hand-off).")
        _cur = read_settings()
        _cur_prov = _cur["default_model"].get("provider", "claude_subscription")
        # Persistent confirmation after Apply — a toast alone is easy to miss, and re-applying the
        # current default produces no other visible change, which made the button feel like a no-op.
        _just_saved = strl.session_state.pop("_wiz_saved", "")
        if _just_saved:
            strl.success(f"✓ Saved — the planning & brainstorm agents will run on **{_just_saved}**.")
        strl.caption(f"Currently active: **{_PROV_WIZ_LABELS.get(_cur_prov, _cur_prov)}**")
        _wiz = strl.radio("Run the planning & brainstorm agents on:", _PROVS,
                          index=_PROVS.index(_cur_prov) if _cur_prov in _PROVS else 0,
                          format_func=lambda p: _PROV_WIZ_LABELS[p], key="wiz_prov")

        _wiz_model, _wiz_base, _wiz_key = "", "", ""
        if _wiz == "claude_subscription":
            strl.info("Nothing to type here. Make sure **Claude Code** is installed and signed in "
                      "(see the checks below). Optionally add an Anthropic API key for visual review.")
        elif _wiz == "anthropic":
            strl.caption("Get a key at https://console.anthropic.com/settings/keys")
            _wiz_key = strl.text_input("Anthropic API key", type="password",
                                       placeholder="sk-ant-…  (blank = keep current)", key="wiz_anth_key")
            _wiz_model = strl.text_input("Model id", value="claude-opus-4-8", key="wiz_anth_model")
        elif _wiz == "openai":
            strl.caption("Get a key at https://platform.openai.com/api-keys")
            _wiz_key = strl.text_input("OpenAI API key", type="password",
                                       placeholder="sk-…  (blank = keep current)", key="wiz_oai_key")
            _wiz_model = strl.text_input("Model id", value="gpt-4o", key="wiz_oai_model")
        else:  # openai_compatible
            _wiz_base = strl.text_input("Base URL", placeholder="https://api.groq.com/openai/v1",
                                        key="wiz_oc_base")
            _wiz_model = strl.text_input("Model id", placeholder="e.g. llama-3.3-70b-versatile",
                                         key="wiz_oc_model")
            _wiz_key = strl.text_input("API key", type="password",
                                       placeholder="sk-…  (blank = keep current)", key="wiz_oc_key")

        if strl.button("Apply this choice", type="primary", key="wiz_apply"):
            _keys = dict(_cur["keys"])
            _k = (_wiz_key or "").strip()
            if _k and _wiz in ("anthropic",):
                _keys["anthropic"] = _k
            elif _k and _wiz in ("openai", "openai_compatible"):
                _keys["openai"] = _k
            _dm = {"provider": _wiz,
                   "model": (_wiz_model or "").strip() if _wiz != "claude_subscription" else "",
                   "base_url": (_wiz_base or "").strip() if _wiz == "openai_compatible" else ""}
            write_settings({"keys": _keys, "default_model": _dm})
            strl.session_state["_wiz_saved"] = _PROV_WIZ_LABELS.get(_wiz, _wiz)
            strl.toast("Provider configured and applied.")
            strl.rerun()

    # ---- 2) System checks -------------------------------------------------
    # Step-by-step install guides shown in a "How to set up" popup, only for checks that fail.
    _G_DEPS = (
        "**Install the Python dependencies**\n\n"
        "From the project folder, run:\n```\npip install -r requirements.txt\n```\n"
        "Tip: the bundled launcher does this for you — `.\\run.ps1` (Windows) or "
        "`./run.sh` (macOS / Linux)."
    )
    _G_KEY = (
        "**Add your Anthropic API key**\n\n"
        "1. Get a key at https://console.anthropic.com/settings/keys\n"
        "2. Paste it into **section 1 above** (choose *Claude — API key*) or the "
        "**Settings → API keys** page, then **Save**.\n"
        "3. Or add it to the project's `.env` file:\n```\nANTHROPIC_API_KEY=sk-ant-...\n```\n"
        "It powers the metered Claude API and visual / screenshot review."
    )
    _G_CLAUDE = (
        "**Install Claude Code** — runs agents *and* the autonomous build on your Claude plan ($0).\n\n"
        "**1. Install Node.js** (provides `npm`). Check with `node --version`; if it's missing:\n"
        "- **Windows:** `winget install OpenJS.NodeJS.LTS`  ·  or download from https://nodejs.org\n"
        "- **macOS:** `brew install node`  ·  or https://nodejs.org\n"
        "- **Linux:** https://nodejs.org\n\n"
        "**2. Install Claude Code:**\n```\nnpm install -g @anthropic-ai/claude-code\n```\n"
        "**3. Sign in once** with your Claude subscription:\n```\nclaude\n```\n"
        "**4.** Come back here and click **↻ Re-check**."
    )
    _G_VSCODE = (
        "**Install VS Code + the `code` command** (optional — only for the *Open in VS Code* hand-off).\n\n"
        "1. Install VS Code from https://code.visualstudio.com\n"
        "2. Enable the `code` command: open VS Code → Command Palette (`Ctrl/Cmd+Shift+P`) → "
        "**Shell Command: Install 'code' command in PATH**.\n"
        "3. Click **↻ Re-check**."
    )
    _G_BUILDS = (
        "**Choose a writable builds folder**\n\n"
        "The **Builds path** in the sidebar can't be written to. Set it to a folder you own — "
        "e.g. a folder under your user / home directory — then return here. The default "
        "(`workspace_builds` beside the app) usually works."
    )
    _G_RUN = (
        "**Give the agents a way to run** — do *either*:\n\n"
        "- **$0 (recommended):** install **Claude Code** — see the *Claude Code* row's guide, or\n"
        "- **Metered:** add an **Anthropic API key** — see the *Anthropic API key* row's guide.\n\n"
        "Either one lets the planning agents run; the autonomous build always needs Claude Code."
    )
    _G_OPENAI = (
        "**Add your OpenAI API key**\n\n"
        "1. Get a key at https://platform.openai.com/api-keys\n"
        "2. Paste it into the **OpenAI API key** field in **section 1 above** or "
        "**Settings → API keys**, then **Save**."
    )
    _G_BASEURL = (
        "**Set the OpenAI-compatible endpoint**\n\n"
        "In **section 1 above**, choose *OpenAI-compatible* and enter the **Base URL**, e.g.:\n"
        "- Groq: `https://api.groq.com/openai/v1`\n"
        "- OpenRouter: `https://openrouter.ai/api/v1`\n"
        "Then set the model id and paste the provider's API key."
    )

    def _check_row(ok, label, ok_msg="", fix_msg="", guide=""):
        """ok=True ✅ · ok=None ⚠️ (optional / not installed) · ok=False ❌.
        When the check isn't passing and a `guide` is given, show a 'How to set up' popup beside it."""
        icon = "✅" if ok is True else ("⚠️" if ok is None else "❌")
        if ok is not True and guide:
            row, act = strl.columns([5, 1.3])
            row.markdown(f"{icon}&nbsp; **{label}**", unsafe_allow_html=True)
            if fix_msg:
                row.caption(fix_msg)
            try:
                pop = act.popover("How to set up", use_container_width=True)
            except TypeError:                                  # older Streamlit without use_container_width
                pop = act.popover("How to set up")
            with pop:
                strl.markdown(guide)
        else:
            strl.markdown(f"{icon}&nbsp; **{label}**", unsafe_allow_html=True)
            msg = ok_msg if ok is True else fix_msg
            if msg:
                strl.caption(msg)

    def _path_writable(p):
        try:
            os.makedirs(p, exist_ok=True)
            _t = os.path.join(p, ".bm_write_test")
            with open(_t, "w", encoding="utf-8") as _f:
                _f.write("ok")
            os.remove(_t)
            return True
        except Exception:
            return False

    with strl.container(border=True):
        cc1, cc2 = strl.columns([4, 1])
        cc1.markdown("### 2) System checks")
        if cc2.button("↻ Re-check", key="doc_recheck"):
            check_requirements(force=True)
            strl.rerun()

        _st = engine_status()
        _reqs = check_requirements()
        _settings = read_settings()
        _prov = _settings["default_model"].get("provider", "claude_subscription")

        # Core: a way to run the agents at all.
        _check_row(_st["anthropic_pkg"], "Python: anthropic package",
                   "Installed.", "Run `pip install -r requirements.txt` in your environment.",
                   guide=_G_DEPS)

        _has_key = _st["anthropic_key"]
        _can_run = _has_key or _reqs["claude"]
        _check_row(_can_run, "A way to run the agents is configured",
                   "Ready — Claude subscription and/or an Anthropic key is available.",
                   "No Anthropic key and no Claude Code login detected. Use section 1 above, or add a key "
                   "in **Settings → API keys**.", guide=_G_RUN)

        _check_row(True if _has_key else None, "Anthropic API key",
                   "Set — enables metered fallback and visual/screenshot review.",
                   "Optional but recommended (needed for visual review even on the subscription).",
                   guide=_G_KEY)

        _check_row(_reqs["claude"], "Claude Code (for $0 autonomous builds)",
                   "Installed and signed in.",
                   "Without it you can still plan and hand the build off to VS Code.",
                   guide=_G_CLAUDE)

        _check_row(True if _reqs["vscode"] else None, "VS Code CLI (optional hand-off)",
                   "The `code` command is available.",
                   "Optional — only needed for the 'Open in VS Code' hand-off.",
                   guide=_G_VSCODE)

        _check_row(_path_writable(base_dir), "Builds folder is writable",
                   f"OK — projects save to `{base_dir}`.",
                   f"Can't write to `{base_dir}`. Pick a different **Builds path** in the sidebar.",
                   guide=_G_BUILDS)

        # Provider-config sanity for the chosen default.
        if _prov == "anthropic":
            _check_row(_has_key, "Provider config: Claude API key present",
                       "Anthropic key found for the selected provider.",
                       "You chose the Anthropic API but no key is set.", guide=_G_KEY)
        elif _prov == "openai":
            _check_row(bool(os.environ.get("OPENAI_API_KEY")), "Provider config: OpenAI key present",
                       "OpenAI key found.",
                       "You chose OpenAI but no key is set.", guide=_G_OPENAI)
        elif _prov == "openai_compatible":
            _check_row(bool((_settings["default_model"].get("base_url") or "").strip()),
                       "Provider config: base URL set",
                       "Base URL configured for the local/compatible endpoint.",
                       "You chose a local/compatible provider but no Base URL is set.", guide=_G_BASEURL)
        else:
            _check_row(_reqs["claude"], "Provider config: subscription ready",
                       "Claude Code is ready to run the subscription agents and builds.",
                       "Subscription selected but Claude Code isn't signed in yet.", guide=_G_CLAUDE)

        strl.caption("Full instructions: see **docs/SETUP.md** in the project folder.")

# ==========================================================================
# STAGE — SETUP
# ==========================================================================
elif strl.session_state.stage == "setup":
    theme.page_header("New project", "Bring it to the table — describe your vision in detail.")
    name = strl.text_input("Project name:", value="my_app")
    user_idea = strl.text_area("Project idea (your vision, in detail):", height=160,
                               placeholder="e.g. A mobile app for restaurants to log food-safety checks. "
                                           "Include any budget, deadlines, must-have features or constraints.")
    refs_up = strl.file_uploader("Attach reference material (optional): mockups, API docs, sample "
                                 "data, brand assets — grounds the plan & the build",
                                 accept_multiple_files=True, key="setup_refs")

    with strl.expander("Planning depth (toggle optional steps to control cost/time)", expanded=False):
        po = strl.session_state.planning_options
        oc1, oc2, oc3 = strl.columns(3)
        po["research"] = oc1.checkbox("Web research", value=po.get("research", False),
                                      help="Ground the plan with live web search (needs API; extra cost).")
        po["acceptance"] = oc1.checkbox("Acceptance criteria", value=po.get("acceptance", True))
        po["tech_spec"] = oc2.checkbox("Tech spec", value=po.get("tech_spec", True))
        po["datamodel"] = oc2.checkbox("Data model/API", value=po.get("datamodel", True))
        po["blueprint"] = oc3.checkbox("Blueprint", value=po.get("blueprint", True))
        po["redteam"] = oc3.checkbox("Red-team + score", value=po.get("redteam", True))
        strl.caption("Core (sections → PRD/plan → guidelines → roadmap) always runs. "
                     "Each enabled step is one more agent call.")

    strl.caption("Each agent's AI follows your **Settings → AI per agent** (all on your Claude "
                 "subscription by default). The autonomous build always uses your subscription.")

    if strl.button("Convene the core team", type="primary"):
        if user_idea and name.strip():
            strl.session_state.active_project = name.strip()
            init_project(base_dir, name.strip())
            for _rf in (refs_up or []):
                save_reference(base_dir, name.strip(), _rf.name, _rf.getvalue())
            seed = f"PROJECT IDEA:\n{user_idea}"
            strl.session_state.seed = seed
            strl.session_state.brainstorm_items = []
            strl.session_state.brainstorm_done = False
            log_history(base_dir, name.strip(), "Operator", f"Project kicked off.\n{seed}")
            with strl.spinner("CEO (Opus 4.8) is staffing the team..."):
                assign_models(seed)
            with strl.spinner("The team is preparing its first questions..."):
                generate_next_batch()
            strl.session_state.stage = "brainstorm"
            persist()
            strl.rerun()
        else:
            strl.error("Enter a project name and an idea to begin.")

# ==========================================================================
# STAGE — BRAINSTORM (1–3 item batches + readiness + visuals)
# ==========================================================================
elif strl.session_state.stage == "brainstorm":
    theme.page_header("Brainstorm",
                      badge_html=theme.chip(strl.session_state.active_project, "gray"))
    if strl.session_state.model_rationale:
        strl.caption(f"**CEO staffing:** {strl.session_state.model_rationale}")

    left, right = strl.columns([3, 2])

    with right:
        render_insight_panel()

    with left:
        items = strl.session_state.brainstorm_items
        if items:
            with strl.expander(f"Discussion so far ({len(items)} resolved)", expanded=False):
                for it in items:
                    verb = "asked" if it["type"] == "question" else "suggested"
                    strl.markdown(f"**{it['agent']} {verb}:** {it['text']}")
                    strl.caption(f"You: {it['response']}")

        if strl.session_state.gen_error:
            strl.error(f"Couldn't generate the next items: {strl.session_state.gen_error}")

        batch = strl.session_state.current_batch
        bkey = strl.session_state.get("batch_seq", 0)  # monotonic — unique widget namespace per batch

        if batch:
            with strl.form(key=f"batch_{bkey}"):
                strl.markdown(f"#### The team raised {len(batch)} item(s):")
                for i, it in enumerate(batch):
                    verb = "asks" if it["type"] == "question" else "suggests"
                    strl.markdown(f"**{it['agent']} {verb}:** {it['text']}")
                    if it["type"] == "question":
                        strl.text_area("Your answer:", key=f"q_{bkey}_{i}", height=90)
                    else:
                        strl.radio("Your response:", ["Agree", "Disagree", "Other"],
                                   key=f"r_{bkey}_{i}", horizontal=True)
                        strl.text_input("If 'Other', specify:", key=f"n_{bkey}_{i}")
                    strl.markdown("---")
                submitted = strl.form_submit_button("Submit batch & continue", type="primary")

            if submitted:
                errors, recorded = [], []
                for i, it in enumerate(batch):
                    if it["type"] == "question":
                        ans = strl.session_state.get(f"q_{bkey}_{i}", "").strip()
                        if not ans:
                            errors.append(f"Answer needed for: {it['text'][:40]}…")
                        recorded.append((it, ans))
                    else:
                        ch = strl.session_state.get(f"r_{bkey}_{i}", "Agree")
                        note = strl.session_state.get(f"n_{bkey}_{i}", "").strip()
                        if ch == "Other" and not note:
                            errors.append(f"Add input for 'Other' on: {it['text'][:40]}…")
                        recorded.append((it, ch if ch != "Other" else f"Other: {note}"))
                if errors:
                    for e in errors:
                        strl.warning(e)
                else:
                    for it, resp in recorded:
                        entry = {**it, "response": resp}
                        strl.session_state.brainstorm_items.append(entry)
                        kind = "Q" if it["type"] == "question" else "Suggestion"
                        log_history(base_dir, strl.session_state.active_project, it["agent"],
                                    f"{kind}: {it['text']}\nOperator: {resp}")
                    with strl.spinner("The team is considering your responses..."):
                        generate_next_batch()
                    persist()
                    strl.rerun()
        else:
            strl.success("The team has no more items right now.")
            if strl.button("Ask the team for more"):
                with strl.spinner("Thinking..."):
                    generate_next_batch()
                persist()
                strl.rerun()

        strl.markdown("---")
        r = strl.session_state.readiness
        ready = r >= 40 and len(strl.session_state.brainstorm_items) > 0
        proceed = True
        if not ready:
            strl.caption("The team has limited input so far — planning now may produce a thin plan.")
            proceed = strl.checkbox("Plan anyway with limited input", key="plan_low_ok")
        if strl.button(f"Build the plan (readiness {r}%)",
                       type="primary" if r >= 80 else "secondary", disabled=not proceed):
            kick_off_planning()                 # starts background authoring
            strl.session_state.stage = "planning"
            strl.rerun()

# ==========================================================================
# STAGE — PLANNING (multi-agent, very detailed)
# ==========================================================================
elif strl.session_state.stage == "planning":
    name = strl.session_state.active_project
    theme.page_header("Plan & PRD", badge_html=theme.chip(name, "gray"))
    s = reconcile_status(base_dir, name)        # heal an orphaned planning run (app restarted)
    is_planning = bool(s and s.get("phase") == "planning")

    if strl.session_state.prd_content:
        # Documents ready — show them.
        strl.success(f"Roster: {', '.join(strl.session_state.team)}")
        _c = read_costs(base_dir, name)
        _pl = _c.get("by_phase", {}).get("planning", {})
        strl.caption(f"Planning API cost: ${_pl.get('usd', 0):.2f} · "
                     f"project total ${_c.get('total_usd', 0):.2f}")
        render_project_views(name)
        c1, c2, c3 = strl.columns(3)
        with c1:
            if strl.button("Approve & go to development", type="primary"):
                strl.session_state.stage = "development"
                persist()
                strl.rerun()
        with c2:
            if strl.button("Regenerate"):
                kick_off_planning()
                strl.rerun()
        with c3:
            if strl.button("Back to brainstorm"):
                strl.session_state.stage = "brainstorm"
                persist()
                strl.rerun()

    elif is_planning and s.get("error"):
        strl.error(f"Planning failed: {s['error']}")
        if strl.button("Retry"):
            kick_off_planning()
            strl.rerun()
        if strl.button("Back to brainstorm"):
            strl.session_state.stage = "brainstorm"
            strl.rerun()

    elif is_planning and s.get("running"):
        strl.info("The execs are authoring the PRD, plan & engineering guidelines — watch the "
                  "board below. You can also go to the Dashboard and work on another project.")
        render_orchestration(name)

    elif is_planning and s.get("finished_at"):
        # Done — load the documents the background thread wrote, then show them. Backstop: if the
        # PRD came back empty, show a recovery screen instead of re-running forever (the source now
        # fails-closed to an error, but never loop here even if an empty result slips through).
        ps = load_project_state(base_dir, name) or {}
        strl.session_state.prd_content = ps.get("prd_content", "")
        strl.session_state.plan_content = ps.get("plan_content", "")
        strl.session_state.team = ps.get("team", strl.session_state.team)
        if strl.session_state.prd_content.strip():
            strl.rerun()
        else:
            strl.warning("Planning finished but didn't produce a PRD this time. You can try again, "
                         "or go back to add a bit more detail.")
            bcol1, bcol2 = strl.columns(2)
            if bcol1.button("Try planning again", type="primary", key="plan_retry_empty"):
                kick_off_planning()
                strl.rerun()
            if bcol2.button("Back to brainstorm", key="plan_back_empty"):
                strl.session_state.stage = "brainstorm"
                persist()
                strl.rerun()

    else:
        # No planning job yet — start one.
        kick_off_planning()
        strl.rerun()

# ==========================================================================
# STAGE — DEVELOPMENT (background build + VS Code + live progress)
# ==========================================================================
elif strl.session_state.stage == "development":
    name = strl.session_state.active_project
    theme.page_header("Development", badge_html=theme.chip(name, "gray"))
    root = project_paths(base_dir, name)["root"]

    sc1, sc2, _sc3 = strl.columns([1, 1, 4])
    with sc1:
        if strl.button("Sync from folder", key=f"sync_{name}",
                       help="Re-read the project folder (after you edit code in VS Code): refreshes "
                            "the blueprint and a current-state summary used for v2/v3 planning."):
            with strl.spinner("Reading the folder and refreshing the blueprint…"):
                sync_from_folder(base_dir, name)
            strl.rerun()
    with sc2:
        if strl.button("Plan next version", key=f"nextver_{name}",
                       help="Start a new brainstorm for v2/v3 — the team is given the current build "
                            "state and deferred roadmap items as context."):
            plan_next_version(name)
            strl.rerun()

    with strl.expander("Project views — Blueprint · PRD · Plan · Guidelines · Roadmap",
                       expanded=True):
        render_project_views(name, show_board=False)   # the live Kanban is in the build section below

    reconcile_status(base_dir, name)            # heal an orphaned build (app restarted mid-build)
    st = read_status(base_dir, name)
    engine = (st or {}).get("engine")
    cc_active = engine == "claude_code"
    cc_running = bool(cc_active and st.get("running"))
    cc_finished = bool(cc_active and st.get("finished_at") and not st.get("error"))

    # Requirements
    reqs = check_requirements()
    rq1, rq2, rq3 = strl.columns([3, 3, 1])
    rq1.caption(("✓ " if reqs["claude"] else "— ") + "Claude Code "
                + ("installed & ready" if reqs["claude"]
                   else ("— install Node.js first (`winget install OpenJS.NodeJS.LTS`), then "
                         "`npm i -g @anthropic-ai/claude-code` and `claude` to log in"
                         if not reqs.get("node")
                         else "— `npm i -g @anthropic-ai/claude-code`, then `claude` to log in")))
    rq2.caption(("✓ " if reqs["vscode"] else "— ") + "VS Code "
                + ("installed" if reqs["vscode"] else "— install VS Code with the `code` command"))
    if rq3.button("↻ Re-check", key=f"recheck_{name}"):
        check_requirements(force=True)
        strl.rerun()

    # ---- Option 1: develop on the dashboard with Claude Code (subscription) ----
    _dev_model = model_for("DEVELOPER", strl.session_state.model_map)
    with strl.container(border=True):
        strl.markdown("### 1) Develop on the dashboard")
        strl.caption(f"The build runs as **Claude Code on your subscription** using the Developer "
                     f"model the CEO assigned (**{_dev_model}**) — it builds, RUNS and fixes the project "
                     "right here (no API cost). Needs Claude Code installed and signed in; runs "
                     "autonomously on your machine. (Change it under **Team & models** on the plan screen.)")
        if not cc_running:
            d1, d2 = strl.columns(2)
            with d1:
                if strl.button("Develop with Claude Code", type="primary", key=f"ccbuild_{name}"):
                    strl.session_state[f"_adv_build_{name}"] = False
                    strl.session_state[f"_force_signoff_{name}"] = False   # fresh build → no stale sign-off
                    prepare_vscode_build(base_dir, name)
                    if not start_claude_code_build(base_dir, name):
                        strl.toast("A build is already running for this project.")
                    strl.rerun()
            with d2:
                if strl.button("Build task-by-task (per v1 feature)", key=f"cctasks_{name}",
                               help="Run Claude Code once per v1 roadmap feature with focused "
                                    "context — better for large projects."):
                    strl.session_state[f"_adv_build_{name}"] = False
                    strl.session_state[f"_force_signoff_{name}"] = False   # fresh build → no stale sign-off
                    prepare_vscode_build(base_dir, name)
                    if not start_claude_code_build_tasks(base_dir, name):
                        strl.toast("A build is already running for this project.")
                    strl.rerun()
        if cc_active:
            render_cc_progress(name)

    # ---- Option 2: open in VS Code and develop there ----
    with strl.container(border=True):
        strl.markdown("### 2) Open in VS Code and develop there")
        strl.caption("Prepares the specs + a `CLAUDE.md` build brief and opens the folder in VS Code; "
                     "you run Claude Code (or Cursor / Copilot) there on your subscription. Needs VS Code.")
        v1, v2 = strl.columns(2)
        with v1:
            if strl.button("Prepare & open in VS Code", type="primary", key=f"ccprep_{name}"):
                prepare_vscode_build(base_dir, name)
                open_in_vscode(root)
                strl.rerun()
        with v2:
            if strl.button("Open folder in VS Code", key=f"ccopen_{name}"):
                open_in_vscode(root)
        _bvp = os.path.join(root, "BUILD_IN_VSCODE.md")
        if os.path.exists(_bvp):
            with strl.expander("▶️ VS Code build steps (terminal commands)", expanded=False):
                with open(_bvp, encoding="utf-8") as _f:
                    strl.markdown(_f.read())

    # ---- Reaching sign-off / 'done' is never a dead-end: clean build, errored/incomplete build
    # (sign off anyway), or a build done in VS Code (mark built). An INTERRUPTED build is retry-only. ----
    if cc_finished:
        strl.markdown("---")
        render_finished_common(name, show_reviews=False)
    else:
        strl.markdown("---")
        signoff_label = None
        if cc_active and st.get("interrupted"):
            strl.caption("The build was interrupted before it finished — start it again above to continue.")
        elif cc_active and st.get("finished_at") and st.get("incomplete"):
            strl.caption("This build ran, but we couldn't verify every step — it may be incomplete. "
                         "Rebuild to finish it, or sign off as-is when you're ready.")
            signoff_label = "Sign off as-is"
        elif cc_active and st.get("finished_at"):
            strl.caption("This build finished, but some steps hit errors. Rebuild to fix them, or sign "
                         "off as-is — your call.")
            signoff_label = "Sign off anyway"
        elif _list_code_files(base_dir, name):
            strl.caption("Built this outside the dashboard? Mark it done here and move to sign-off.")
            signoff_label = "Mark built & sign off"
        else:
            strl.caption("Nothing built yet — develop above (or in VS Code), then come back to sign off.")
        if signoff_label and (strl.session_state.get(f"_force_signoff_{name}")
                              or strl.button(signoff_label, key=f"force_signoff_{name}")):
            strl.session_state[f"_force_signoff_{name}"] = True
            render_finished_common(name, show_reviews=False)

# ==========================================================================
# STAGE — DONE
# ==========================================================================
elif strl.session_state.stage == "done":
    name = strl.session_state.active_project
    root = project_paths(base_dir, name)["root"]
    st = read_status(base_dir, name) or {}
    # Claim only what actually happened — the CTO/PM/QA code review and visual QA are optional and
    # frequently never run, so don't assert them by default.
    _code_qa = bool(st.get("qa_summary")) and (st.get("cto_aligned") is not None
                                               or st.get("pm_aligned") is not None)
    _vis_qa = bool(st.get("visual_report"))
    _issues = bool(st.get("error") or st.get("incomplete"))
    if not _issues:
        strl.balloons()
    theme.page_header("Delivered", badge_html=theme.chip(name, "gray"))
    if _issues:
        strl.info("Built and logged, with known issues noted in `bugs.md`.")
    elif _code_qa and _vis_qa:
        strl.success("Designed, built, and QA-reviewed (code and visual). Everything is logged.")
    elif _code_qa:
        strl.success("Designed, built, and code-reviewed. Logged.")
    else:
        strl.info("Built and logged.")

    with strl.container(border=True):
        strl.markdown("### ✅ Next steps")
        strl.markdown(
            "1. **See it run** — follow **How to run & see the front end** below to launch the app and "
            "open the front end (or click **Open in VS Code** to run it there).\n"
            "2. **QA it** — click through the flows; for UI review use **Continue development → Visual "
            "front-end QA** (upload screenshots). Issues are tracked in `bugs.md`.\n"
            "3. **Deploy (when you're happy)** — see **Deploy options** below.")

    _c = read_costs(base_dir, name)
    strl.markdown(f"**Total API cost:** ${_c.get('total_usd', 0):.2f}  "
                  f"({_c.get('input_tokens', 0):,} in / {_c.get('output_tokens', 0):,} out tokens)")
    bp = _c.get("by_phase", {})
    if bp:
        for ph, v in bp.items():
            strl.caption(f"• {ph}: ${v.get('usd', 0):.2f} ({v.get('calls', 0)} calls)")
    strl.markdown(f"**Workspace:** `{os.path.abspath(root)}`")
    strl.markdown("- `plan.md`, `prd.md`  ·  generated source files  ·  `RUN_GUIDE.md`\n"
                  "- `history/changelog.md`  ·  `bugs.md`  ·  `project.json`")
    _rg = os.path.join(root, "RUN_GUIDE.md")
    if os.path.exists(_rg):
        with strl.expander("▶️ How to run & see the front end", expanded=True):
            with open(_rg, encoding="utf-8") as _f:
                strl.markdown(_f.read())
    with strl.expander("🚀 Deploy options (when you're ready)", expanded=False):
        strl.markdown(
            "First, version-control it: `git init`, commit, and push to GitHub. Then host it based on "
            "the stack (check the project's `RUN_GUIDE.md` / `README.md` for the exact start command):\n\n"
            "- **Streamlit app** → Streamlit Community Cloud (free) or any container host.\n"
            "- **Web frontend** (Next.js / React / static) → Vercel, Netlify, or Cloudflare Pages.\n"
            "- **API / backend** (FastAPI / Flask / Node) → Render, Railway, Fly.io, or a VPS.\n"
            "- **Anything containerized** → build a Docker image and deploy to your cloud of choice.\n"
            "- **CLI / desktop / library** → publish the repo or a packaged release.\n\n"
            "Add any required API keys as **environment variables on the host** — never commit them.")
    c1, c2, c3 = strl.columns(3)
    with c1:
        if strl.button("Continue development",
                       help="Reopen this project's build to iterate or request changes — no new spend."):
            strl.session_state.stage = "development"   # dev screen reads the finished build from disk; no clobber
            persist()
            strl.rerun()
    with c2:
        if strl.button("Open in VS Code"):
            open_in_vscode(root)
    with c3:
        if strl.button("Back to dashboard"):
            strl.session_state.stage = "dashboard"
            strl.rerun()
