"""Project summary export — a polished, shareable summary (markdown + HTML).

Depends only on the engine core (one-directional: reports -> core). The CEO agent
writes the summary; it's saved as SUMMARY.md and a standalone SUMMARY.html.
"""
from engine.core import (
    CEO_MODEL,
    call_agent,
    log_history,
    read_roadmap,
    roadmap_to_md,
    save_artifact,
    set_cost_context,
    _read_artifact_text,
)


def _md_to_html_doc(title, md):
    esc = ((md or "").replace("\\", "\\\\").replace("$", "\\$").replace("`", "\\`")
           .replace("</script>", "<\\/script>"))
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>" + title + "</title>"
        "<style>body{font-family:'Segoe UI',system-ui,sans-serif;max-width:820px;margin:40px auto;"
        "padding:0 16px;line-height:1.6;color:#1f2937}h1,h2,h3{color:#111827}code{background:#f1f5f9;"
        "padding:1px 5px;border-radius:4px}</style></head><body><div id='c'></div>"
        "<script src='https://cdn.jsdelivr.net/npm/marked/marked.min.js'></script>"
        "<script>document.getElementById('c').innerHTML=marked.parse(`" + esc + "`);</script>"
        "</body></html>")


def build_client_report(base_dir, name, model=None):
    """CEO writes a polished project summary; saved as SUMMARY.md + standalone SUMMARY.html."""
    set_cost_context(base_dir, name, "report")   # attribute this summary's API spend to the ledger
    prd = _read_artifact_text(base_dir, name, "prd.md")
    plan = _read_artifact_text(base_dir, name, "plan.md")
    rm_md = roadmap_to_md(read_roadmap(base_dir, name))
    report = call_agent("CEO", "", (
        "Write a polished project summary (professional, minimal jargon): executive summary, "
        "objectives, the v1 scope, the version roadmap overview, a rough timeline/milestones, and "
        "what's needed to proceed. Output clean markdown.\n\n"
        f"=== PRD (excerpt) ===\n{prd[:8000]}\n\n=== PLAN (excerpt) ===\n{plan[:5000]}\n\n"
        f"=== ROADMAP ===\n{rm_md[:4000]}"),
        model=(model or CEO_MODEL), max_tokens=6000)
    save_artifact(base_dir, name, "SUMMARY.md", report)
    save_artifact(base_dir, name, "SUMMARY.html", _md_to_html_doc(f"{name} — Summary", report))
    log_history(base_dir, name, "CEO", "Generated summary (md + html).")
    return report
