# BM Builder — Setup Guide (start here)

This walks you from **"I just downloaded the files"** to **"the app is running with my AI provider"** — step by step, on Windows, macOS, or Linux.

It takes about **5–10 minutes**. You do **four** things:

1. Install **Python** → 2. Download & install the **app** → 3. Set up **your AI provider** → 4. **Run** it.

> **In a hurry?** If you already have Python and a Claude or OpenAI account, jump to [Step 3](#step-3--set-up-your-ai-provider).

---

## Step 1 — Install Python (3.9 or newer)

Check whether you already have it. Open a terminal and run:

```bash
python --version      # Windows
python3 --version     # macOS / Linux
```

If it prints `Python 3.9` or higher, skip to Step 2. Otherwise install it:

| OS | How |
|----|-----|
| **Windows** | Download from [python.org/downloads](https://www.python.org/downloads/) and **tick "Add python.exe to PATH"** during install. **Or, no GUI:** run `winget install Python.Python.3.12`, then **open a new terminal**. |
| **macOS** | `brew install python` (needs [Homebrew](https://brew.sh)), or download from [python.org](https://www.python.org/downloads/). |
| **Linux** | `sudo apt update && sudo apt install python3 python3-pip python3-venv` (Debian/Ubuntu). |

**🪟 Windows — on the installer's first screen, tick "Add python.exe to PATH"** *before* clicking **Install Now**:

![Python installer: tick "Add python.exe to PATH" before clicking Install Now](img/python-add-to-path.png)

> **Don't see that checkbox?** If `python` sent you to the **Microsoft Store**, or you installed with **`winget`**, there's no checkbox to tick — that's expected for those methods. Just verify with `python --version`; if it fails, use the fix below.

> **🪟 Windows: seeing `Python was not found; run without arguments to install from the Microsoft Store…`?**
> That means Windows is intercepting the `python` command — Python isn't on your PATH, or the Store "app execution alias" is on. Fix it either way, then open a **new** terminal:
> 1. Reinstall from [python.org](https://www.python.org/downloads/) with **"Add python.exe to PATH"** ticked, **or**
> 2. **Settings → Apps → Advanced app settings → App execution aliases** → turn **off** the `python.exe` and `python3.exe` entries.
>
> *Tip:* the **`py`** launcher usually works even when `python` doesn't — try `py --version`, and use `py -m …` anywhere these docs say `python -m …` (e.g. `py -m streamlit run app.py`).

---

## Step 2 — Download and install the app

### 2a. Get the files

- **With Git:** `git clone <REPO_URL>` then `cd "BM Builder"`
- **Without Git:** on the GitHub page click **Code → Download ZIP**, unzip it, and open a terminal in that folder.

> **⚡ Express path:** once you have the files (and Python from Step 1), you can skip 2b–2c and Step 4 by running the bundled launcher, which makes the virtual env, installs everything, and starts the app:
> ```bash
> .\run.ps1                      # Windows (PowerShell)
> chmod +x run.sh && ./run.sh    # macOS / Linux
> ```
> Then come back and do **Step 3** (your AI provider) from inside the app's **Setup & checks** screen. Prefer to understand each step? Continue below.

### 2b. Create a virtual environment (recommended)

This keeps the app's dependencies separate from the rest of your system.

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

> On Windows, if activation is blocked, run once:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### 2c. Install dependencies

```bash
python -m pip install -r requirements.txt
```

> Use `python -m pip` (not a bare `pip`) — it always installs into the Python you just set up, and it works even when `pip` isn't on your PATH. On Windows you can use `py -m pip …` instead.

---

## Step 3 — Set up your AI provider

BM Builder needs an AI "brain." **You bring your own** — pick the option that fits you. Here's the quick decision:

| Option | Cost | Autonomous build on the dashboard? | Best for |
|--------|------|-----------------------------------|----------|
| **A. Claude subscription** (Claude Code) | **$0** with your Claude plan | ✅ Yes | **Most people — recommended** |
| **B. Anthropic API key** | Pay-per-use | ⚠️ Build needs Option A too | Reliable strict output; no subscription |
| **C. OpenAI** | Pay-per-use | ⚠️ Build needs Option A too | You already use OpenAI |
| **D. OpenAI-compatible** (Groq, OpenRouter, custom) | Pay-per-use | ⚠️ Build needs Option A too | Alternative / custom model hosts |

> **Important — read this once:** The **planning & brainstorming agents** can run on *any* option above. But the **one-click autonomous build** (where the app writes, runs, and fixes your project for you) **always uses Claude Code on your subscription** — no other provider can drive it. If you choose B, C, or D, you can still plan with that provider and then **hand the build off to VS Code** to build with your own tools. For the full experience, set up **Option A**.

Now follow the section for your choice. You can set up more than one (e.g. A for builds **and** B for the most reliable agents).

---

### Option A — Claude via your subscription (recommended, $0 builds)

This routes agents **and** the autonomous build through [Claude Code](https://docs.anthropic.com/en/docs/claude-code) on your existing Claude plan.

1. **Install Node.js** (Claude Code needs it). Check with `node --version`; if missing:
   - **Windows:** `winget install OpenJS.NodeJS.LTS` or [nodejs.org](https://nodejs.org).
   - **macOS:** `brew install node` or [nodejs.org](https://nodejs.org).
   - **Linux:** [nodejs.org](https://nodejs.org) or `nvm`.
2. **Install Claude Code:**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
3. **Sign in** (one time): run `claude` and follow the prompt to log in with your Claude subscription.
4. That's it — leave the app's provider on its default ("Claude — Subscription"). Optionally also add an Anthropic API key (Option B) so **visual/screenshot review** works.

> **🪟 Windows notes:**
> - Run these in **PowerShell** (the default terminal). All three commands above (`winget`, `npm install -g`, `claude`) work from **any folder** — `-g` installs globally, so you don't need to `cd` into the project. Only *running the app* (`.\run.ps1`) needs the project folder.
> - **If the app was already open when you installed Claude Code,** it won't see it yet — a running app keeps the PATH it started with. Click **↻ Re-check** on the dashboard, or restart the app (`Ctrl+C`, then `.\run.ps1`). Verify the install anytime with `claude --version` in a new terminal.

---

### Option B — Anthropic API key (metered)

1. Get a key at **[console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)**.
2. Add it **either** way:
   - **In the app (easiest):** start the app (Step 4) → sidebar **Settings** → **API keys** tab → paste your key → **Save settings**.
   - **Or in a file:** copy `.env.example` to `.env` and paste the key after `ANTHROPIC_API_KEY=`.
3. In **Settings → AI per agent**, set the agents you want to **"Claude — API (metered)"** and enter the model id (e.g. `claude-opus-4-8`) in the shared model field.

---

### Option C — OpenAI (metered)

1. Get a key at **[platform.openai.com/api-keys](https://platform.openai.com/api-keys)**.
2. Start the app (Step 4) → **Settings → API keys** → paste it in the **OpenAI API key** field → **Save**.
3. In **Settings → AI per agent**, set the agents you want to **"OpenAI (metered)"** and enter the model id (e.g. `gpt-4o`) in the shared model field.
4. To autonomously build, also set up **Option A** — or use **"Open in VS Code"** on the Development screen and build there.

---

### Option D — OpenAI-compatible (Groq, OpenRouter, custom)

Run agents through any OpenAI-compatible endpoint.

1. Get an API key and base URL from your provider, e.g.:
   - **Groq:** `https://api.groq.com/openai/v1`
   - **OpenRouter:** `https://openrouter.ai/api/v1`
2. Start the app → **Settings → AI per agent** → set the agents you want to **"OpenAI-compatible"**, then enter the **Base URL** and **Model name** in the shared model field.
3. Put the provider's key in the **OpenAI API key** field (**Settings → API keys**).
4. **Note:** image/visual review needs a vision-capable model — keep an Anthropic key (Option B) for that. Autonomous builds still need **Option A**.

---

## Step 4 — Run the app

```bash
python -m streamlit run app.py
```

> Run Streamlit **through Python** like this. Calling `streamlit run app.py` directly often fails on Windows with *"streamlit : The term 'streamlit' is not recognized…"* because `streamlit.exe` isn't on your PATH — `python -m streamlit` (or `py -m streamlit`) avoids that entirely.

Your browser opens to BM Builder. In the **sidebar**:

- Set the **Builds path** (where projects are saved — defaults to a `workspace_builds/` folder beside the app).
- Check the **Engine** status: green **"Ready"** means a key is detected. If it says **"Anthropic key not set,"** click **"Add your Anthropic key →"** to jump to Settings (or rely on your Claude subscription).

---

## Step 5 — Make your first project (confirm it works)

1. Click **New project**.
2. Give it a name and describe an idea (e.g. *"a CLI to-do app that stores tasks in a JSON file"*).
3. Click **Convene the core team** and answer a few questions in **Brainstorm**.
4. Click **Build the plan**, review the PRD/plan, then **Approve & go to development**.
5. On the Development screen, click **Develop with Claude Code** (Option A) — or **Open in VS Code** to build elsewhere.

🎉 If you see a plan and a build, you're set up correctly.

---

## (Optional) VS Code handoff

If you want the "Open in VS Code" buttons to work:

1. Install **[VS Code](https://code.visualstudio.com)**.
2. Enable the `code` command: in VS Code open the Command Palette (`Ctrl/Cmd+Shift+P`) → **"Shell Command: Install 'code' command in PATH."**

---

## Stuck? 

See the **[Troubleshooting table in HELP.md](HELP.md#troubleshooting)** for the common issues (missing key, Claude Code not found, PDF parsing, stale code, etc.).

## A word on cost & privacy

- **Local-first:** everything stays on your machine; the only thing sent out is your prompts to the provider **you** chose.
- **$0 is achievable:** with the Claude subscription (Option A) the agents and the build cost nothing extra.
- **Metered spend is tracked:** the app shows API cost per project and per phase. Non-Claude providers bill you directly and aren't tracked here.
- **Your keys stay private:** stored locally in `.env` / `settings.json`, both git-ignored — they're never committed or shared.
