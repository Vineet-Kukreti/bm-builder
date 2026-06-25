# BM Builder — Suggested Features & Improvements

Ideas to make BM Builder more useful for people downloading it from GitHub. Grouped by theme and tagged with rough priority and effort. This is a roadmap for discussion.

Priority: ⭐ high · ◐ medium · ○ nice-to-have   ·   Effort: S / M / L

> ### ✅ Already shipped
> - **In-app Setup hub ("Setup & checks")** — guided AI-provider picker + live diagnostics (deps, key, Claude Code, VS Code, builds folder) with fixes and Re-check, plus a first-run dashboard banner.
> - **One-command launchers** — `run.ps1` / `run.sh` create the venv, install deps, and start the app.
> - **Step-by-step setup docs** — [SETUP.md](SETUP.md) (branching by OS + provider) and [HELP.md](HELP.md).
> - **Repo hygiene** — `LICENSE` (Apache 2.0), `NOTICE`, `AUTHORS.md`, `CONTRIBUTING.md`, and a CI smoke test (`.github/workflows/ci.yml`).
>
> The items below are what's *left*.

---

## A. Onboarding & help (highest leverage for new users)

A stranger cloning the repo has none of your context. These reduce drop-off the most.

- **⭐ S — In-app Help / first-run guide.** A "Help" item in the sidebar that renders `docs/HELP.md`, plus a one-time welcome panel on the empty dashboard ("No projects yet → here's what to do"). Right now help only exists as a file.
- **⭐ S — Guided empty states.** Every stage should explain itself in one line when there's nothing yet, with a "what happens next" hint. Brainstorm and Development especially.
- **⭐ M — Setup self-check / "Doctor" panel.** A single screen that checks: Python deps installed, Anthropic key present, Claude Code installed & logged in, VS Code `code` on PATH, Builds path writable — each with a copy-paste fix. Today these checks are scattered.
- **◐ M — Bundled sample project.** A tiny, fully sanitized demo project (e.g. "Tip Calculator") so a new user can click **Open** and immediately see what a finished plan + build looks like, without spending a token. (Generate it lazily / ship it as static artifacts so it stays git-clean.)
- **◐ S — Cost preview before convening.** Estimate "~$X if any agents are metered; $0 if all on subscription" on the Setup screen so new users aren't surprised by a bill.

## B. Trust, safety & robustness (matters once strangers run it)

- **⭐ S — Key handling hardening.** Mask keys in all logs/UI, and add a visible "your keys never leave this machine except as provider calls" note. (Mostly there — make it explicit.)
- **⭐ M — Graceful "no provider configured" mode.** If neither a key nor Claude Code is available, show a friendly setup wall instead of letting agent calls error mid-flow.
- **◐ M — Atomic/locked writes for all project JSON.** The README notes single-user limits; finishing lock-serialization would make multi-tab use safe and prevent corrupt `project.json`.
- **◐ S — Provider/error surfacing.** When an agent call fails (rate limit, bad key, invalid JSON), show the reason and the chosen fallback clearly rather than a generic error.
- **○ S — "Export project" / "Import project" zip.** Lets users share or back up a build folder cleanly (and re-import on another machine).

## C. Core workflow improvements

- **⭐ M — Resume/repair any interrupted stage.** Planning and builds already self-reconcile somewhat; extend it so a crash mid-planning never leaves a project wedged.
- **◐ M — Editable plan documents in-app.** Let users tweak the PRD/plan/tech-spec text and re-run the build from the edit, instead of regenerating from scratch.
- **◐ M — Build diff & review view.** After a Claude Code build, show what files were created/changed and a short summary, so the user can review before signing off.
- **◐ L — Test generation + run gate.** Have the team generate tests and require them to pass before a build is marked "delivered."
- **○ M — Multiple build targets / stacks.** Let the user pick a preferred stack (e.g. Next.js, FastAPI, plain Python CLI) so the plan and build align with what they want to maintain.

## D. Collaboration & sharing (you're publishing this — lean into it)

- **◐ M — Shareable project report.** One self-contained HTML/Markdown export of the idea → plan → roadmap → cost, suitable for sending to a stakeholder. (The engine already builds a client report; expose it for the app flow and make sure it's PII-free by default.)
- **○ M — Templates / recipes.** Starter "idea templates" (CRUD app, API service, CLI tool, data dashboard) that pre-fill Setup and steer planning.
- **○ S — Project tags & search on the dashboard.** Once people accumulate builds, filtering by tag/status helps.

## E. Documentation & repo hygiene (do before/at launch)

- ~~**Add a `LICENSE`.**~~ ✅ Done — Apache 2.0 with `NOTICE`/`AUTHORS.md` attribution.
- **⭐ S — `CONTRIBUTING.md` + issue templates.** Set expectations (no secrets/PII in PRs, how to run locally).
- **◐ S — Screenshots / short GIF in the README.** A 10-second clip of idea → plan → build is worth more than paragraphs.
- **◐ S — Pin dependency versions.** `requirements.txt` is unpinned; pin known-good versions (or add a `constraints.txt`) so clones don't break on a future Streamlit/anthropic release.
- **◐ S — `.python-version` / supported-version note + a tiny smoke test** (`python -m py_compile` in CI via GitHub Actions) so PRs can't merge broken imports.
- **○ S — `CHANGELOG.md`** so users can see what changed between versions.

---

## Suggested next slice (what's left for a polished launch)

With the Setup hub, launchers, docs, and LICENSE done, the highest-value remaining items are:

1. **README screenshots / a 30-sec GIF** (D/E) — the biggest boost to the GitHub landing page.
2. **Bundled sample project** (A) — first open shows value without spending a token.
3. **Pin dependency versions + lean on the CI smoke test** (E) — clones keep working over time.
4. **In-app Help page** that renders these docs (A) — users never have to leave the app.
5. **Graceful "no provider" wall everywhere** (B) — extend the first-run nudge so no flow dead-ends mid-task.
