# Contributing to BM Builder

Thanks for your interest in improving BM Builder! This is a small, local-first Streamlit tool — contributions of all sizes are welcome.

## Ground rules

- **Never commit secrets or personal data.** No API keys, no `.env`, no `settings.json`, no real client/project content in code, tests, screenshots, or example data. These paths are already in [.gitignore](.gitignore) — keep it that way.
- **Keep it local-first.** The app assumes a single user on their own machine. Don't add features that silently send data anywhere except the user's chosen AI provider.
- **Match the surrounding style.** The codebase favors clear, compact Python and Streamlit idioms already used in `app.py` and `dashboard_engine.py`.

## Local setup

```bash
# 1. Fork & clone, then:
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 2. Add a key (or use your Claude Code subscription)
cp .env.example .env        # then paste your ANTHROPIC_API_KEY

# 3. Run
streamlit run app.py
```

See [docs/SETUP.md](docs/SETUP.md) for the full setup guide.

## Before you open a PR

Run the checks — they must pass (this is also enforced in CI):

```bash
python -m py_compile app.py dashboard_engine.py theme.py engine/*.py   # syntax
python -c "import app"                                                 # imports (ignore the ScriptRunContext warning)
python -m unittest discover -s tests                                   # unit tests
```

Then sanity-check the screens you touched still render:

```bash
streamlit run app.py
```

### Engine layout

The orchestration engine is the `engine/` package (`core.py` kernel + `errors.py`,
`models.py`, `graph.py`, `reports.py`, `usecases.py`). `dashboard_engine.py` is a
backward-compatibility facade that re-exports it — prefer importing from the focused
`engine.*` submodules in new code. Add unit tests in `tests/` for any pure logic you add.

## Pull requests

- Keep PRs focused and describe **what** changed and **why**.
- Note any new dependency and why it's needed (prefer optional, gracefully-degrading deps).
- If you change a user-facing flow, update [docs/HELP.md](docs/HELP.md) / [docs/SETUP.md](docs/SETUP.md) to match.

## Reporting issues

Open a GitHub issue with: what you did, what you expected, what happened, your OS and Python version, and whether you were on the Claude subscription or an API key. **Redact any keys or private content** from logs you paste.

## License of contributions

BM Builder is © 2026 Vineet Kukreti (Bespoke Mind AI) and licensed under the
[Apache License 2.0](LICENSE). By submitting a contribution, you agree it is licensed under
those same terms, and that the project's copyright/`NOTICE` attribution is retained.
