"""Graphviz DOT generation for the brainstorm "whiteboard".

Pure rendering — takes the resolved brainstorm items and produces a DOT string the
UI hands to Streamlit's graphviz_chart. No engine state, no I/O.
"""


def build_graph_dot(items, readiness=0):
    # Forest & Gold (no AI-indigo). Gold needs dark text; the greens take white.
    agent_colors = {"CEO": ("#13402b", "white"), "CTO": ("#1d5a3c", "white"), "CMO": ("#b89339", "#171411")}
    lines = [
        "digraph G {", "  rankdir=LR;", "  bgcolor=transparent;",
        '  node [style=filled, fontname="Segoe UI", fontsize=10, color="#00000022"];',
        '  edge [color="#c9ddd0"];',
        f'  root [label="Project\\nreadiness {int(readiness)}%", shape=doubleoctagon, '
        'fillcolor="#13402b", fontcolor="white"];',
    ]
    for ag, (col, fc) in agent_colors.items():
        lines.append(f'  {ag} [shape=box, fillcolor="{col}", fontcolor="{fc}"];')
        lines.append(f'  root -> {ag};')
    for i, it in enumerate(items):
        ag = (it.get("agent") or "CEO").upper()
        if ag not in agent_colors:
            ag = "CEO"
        label = (it.get("text") or "")[:55].replace("\\", " ").replace('"', "'").replace("\n", " ")
        if it.get("type") == "question":
            fill = "#f6efd9"      # cream/gold-tint (was AI-blue #dbeafe); agree/disagree/pending stay semantic
        else:
            r = (it.get("response") or "").lower()
            fill = "#bbf7d0" if r.startswith("agree") else "#fecaca" if r.startswith("disagree") else "#fde68a"
        lines.append(f'  it{i} [shape=note, fillcolor="{fill}", label="{label}"];')
        lines.append(f'  {ag} -> it{i};')
    lines.append("}")
    return "\n".join(lines)
