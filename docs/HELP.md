# BM Builder — Help & Usage Guide

A practical, step-by-step walkthrough. If you just want to get running, see the [Quickstart in the README](../README.md#quickstart).

---

## 1. Install & first run

1. **Install Python 3.9+** and confirm it works: `python --version`.
2. **Install dependencies:** `pip install -r requirements.txt`.
3. **Add a key (recommended):** copy `.env.example` to `.env` and paste your Anthropic API key, or add it later from the in-app **Settings** page.
4. **(Optional but recommended) Install Claude Code** for $0 autonomous builds:
   ```bash
   npm install -g @anthropic-ai/claude-code
   claude        # run once and sign in with your Claude subscription
   ```
5. **Start the app:** `streamlit run app.py`. It opens in your browser.

In the sidebar you'll see the **Engine** status. Green "Ready" means an Anthropic key is detected. You can still run agents on your Claude subscription without an API key — the key mainly enables metered fallback and visual review.

> **New to the tool?** Click **Setup & checks** in the sidebar. It has a guided picker that configures your AI provider for you, plus live checks (Python deps, key, Claude Code, VS Code, builds folder) — each with a one-line fix and a Re-check button. On first run, the dashboard also shows a "Let's get you set up" banner if no provider is configured yet.

---

## 2. The dashboard

- **New project** — starts a new app/SaaS build.
- **Refresh** — re-reads project state from disk.
- **What you need to develop projects** — checks whether Claude Code and VS Code are installed, with one-line fixes if not.
- Each project card shows its stage, readiness, last update, and API cost so far, plus a status chip (Idle / Building / Synced / Complete…). **Open** to resume, or use **More** to open in VS Code, sync from folder, or delete.

> **Builds path** (sidebar): where every project folder is saved. Defaults to a `workspace_builds/` folder beside the app. Point it anywhere you like.

---

## 3. Setup a new project

1. **Project name** and **Project idea** (describe your vision in detail — the more specific, the better the plan).
2. **Client inputs / requirements / constraints** — budget, deadlines, must-have features, compliance, etc.
3. **Auto-fill from a brief** (optional) — upload a PDF / Word / HTML / text brief and the app extracts the text into your client inputs.
4. **Reference material** (optional) — attach mockups, API docs, sample data, or brand assets to ground the plan and the build.
5. **Planning depth** — toggle optional steps (web research, acceptance criteria, tech spec, data model, blueprint, red-team) to control cost and time. Core planning always runs.
6. **Compute source per agent** — choose **Subscription** ($0, your Claude plan) or **Metered API** (billed, best for strict JSON) for each of CEO/CTO/CMO/PM/QA/Skeptic. Defaults to all on subscription.
7. Click **Convene the core team**.

---

## 4. Brainstorm

The team raises questions and suggestions in small batches:

- **Questions** — type your answer.
- **Suggestions** — Agree / Disagree / Other (with a note).

Submit the batch to continue. A **readiness** score climbs as the picture fills in. When you're satisfied (40%+ is enough; 80%+ is strong), click **Build the plan**. You can plan early with limited input if you tick the override.

---

## 5. Plan & PRD

Planning runs in the background — you can switch to the dashboard and work on another project meanwhile. When it finishes you'll see the PRD, plan, tech spec, data model, blueprint diagram, roadmap, and (if enabled) a red-team review. From here:

- **Approve & go to development**
- **Regenerate** (re-run planning)
- **Back to brainstorm** (add more detail first)

---

## 6. Development

Three ways to build:

1. **Develop on the dashboard** — Claude Code (Opus, on your subscription) writes, **runs**, and fixes the project autonomously. Needs Claude Code installed and signed in.
2. **Build task-by-task** — one focused Claude Code run per v1 roadmap feature. Better for large projects.
3. **Open in VS Code** — prepares the specs + a `CLAUDE.md` build brief and opens the folder so you can drive Claude Code (or Cursor / Copilot) yourself.

Watch live progress on the board. When a build finishes you can sign off, or mark a build done that you completed elsewhere. **Sync from folder** re-reads the project after you edit code so v2/v3 planning has the current state.

---

## 7. Delivered

You get a cost breakdown, a `RUN_GUIDE.md` explaining how to run the project, and the full project folder. From here you can **continue development**, **open in VS Code**, or go back to the dashboard. Use **Plan next version** on the development screen to start a v2/v3 brainstorm with the current build as context.

---

## 8. Settings

- **AI per agent** — set each agent (CEO, CTO, CMO, PM, QA, Skeptic) individually to the Claude subscription ($0, default), the Anthropic API, OpenAI, or an OpenAI-compatible endpoint (Groq, OpenRouter, custom). Agents on a metered/OpenAI provider share one model field. The autonomous **build** always uses the Claude subscription regardless.
- **API keys** — stored locally in `settings.json` (plaintext, git-ignored). Leave a field blank to keep the current value; tick **Clear** to remove a saved key.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| **"ANTHROPIC_API_KEY not set"** | Add a key in **Settings → API keys**, or to `.env`, then restart. Or run agents on your Claude subscription. |
| **Builds don't start / "Claude Code not installed"** | `npm install -g @anthropic-ai/claude-code`, run `claude` once to sign in, then click **Re-check**. |
| **"Open in VS Code" does nothing** | Install VS Code and enable the `code` command (Command Palette → *Shell Command: Install 'code' command in PATH*). |
| **Agents return malformed/empty output on subscription** | Switch the JSON-strict agents (QA / Skeptic) to **Claude API** in **Settings → AI per agent**, or run with an Anthropic key set. |
| **Sidebar warns "Source changed on disk"** | You edited the code while running. Stop Streamlit (Ctrl+C) and run `streamlit run app.py` again. |
| **A project looks stuck "Building"** | The app reconciles orphaned builds on load. Open the project, or **Sync from folder**, or restart the app. |
| **PDF/Word brief won't parse** | Install the optional parsers: `pip install pypdf python-docx`. |

---

## Where things are stored

- **Per project:** a folder under your Builds path with `project.json`, `prd.md`, `plan.md`, generated source, `RUN_GUIDE.md`, `history/`, `bugs.md`, and cost/status files.
- **Global, beside the app:** `settings.json` (keys + per-agent AI choices) — git-ignored.
