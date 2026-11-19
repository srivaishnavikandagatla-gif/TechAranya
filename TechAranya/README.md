# 🌿 TechAranya – AI Plant Doctor

*Hackathon theme: AI for a Greener Tomorrow*

Snap or upload a photo of any plant, add a few details (plant name, where it grows) and get:

- **Health verdict**: Healthy / Mild issue / Needs attention / Critical, with a 0–100 health score
- **Current state**: visible symptoms and likely causes
- **Next steps**: a prioritised checklist (Do now → This week → Ongoing)
- **Location-specific tips** for terrace, balcony, indoor, garden, farm or greenhouse
- **Green tip**: an eco-friendly practice (composting, water saving, natural pest control)
- Answers in 10 Indian languages, with an **organic-only** mode

## How it works

```
Phone camera / upload ─► browser resizes image ─► FastAPI /api/diagnose
                                                     │ image + details
                                                     ▼
                                     Claude (vision + structured output)
                                                     │ validated JSON (Pydantic)
                                                     ▼
                                          Result cards in the browser
```

- `app/diagnose.py`: prompt, output schema (`Diagnosis`) and the Claude API call
- `app/main.py`: FastAPI server, upload validation, error handling
- `static/`: mobile-first UI (plain HTML/CSS/JS, no build step)

## Run it on a new laptop

**You need:** Python 3.10 or newer, internet access, and an Anthropic API key (https://console.anthropic.com → API Keys).

### Step 1: Install Python (once)

- **Windows:** download from https://www.python.org/downloads/ and run the installer.
  ⚠️ On the first screen, tick **"Add python.exe to PATH"**, then click Install Now.
- **Mac:** download from https://www.python.org/downloads/ and install, or run `brew install python` if you use Homebrew.

Check it worked. Open Terminal (Mac) or Command Prompt (Windows) and run `python3 --version` (Mac) or `python --version` (Windows). It should print 3.10 or higher.

### Step 2: Unzip

Unzip `TechAranya.zip` anywhere, for example to your Desktop. You get a folder called `TechAranya`.

### Step 3: Start the app

**Simplest (any OS):** in the `TechAranya` folder run **`python start.py`** (Windows) or **`python3 start.py`** (Mac).
On Windows you can also double-click `start.py`. It installs everything, asks for your key the first time, and opens the browser.

Or use the platform scripts (not included in the email-safe zip):

**Windows:** open the `TechAranya` folder and double-click **`run.bat`**.
(If Windows shows "Windows protected your PC", click **More info → Run anyway**.)

**Mac:** open Terminal and run:
```bash
cd ~/Desktop/TechAranya      # or wherever you unzipped it
bash run.sh
```

The first run takes 1–2 minutes to install packages.

### Step 4: Add your API key (first run only)

The first run creates a file called `.env` and opens it (Notepad on Windows, TextEdit on Mac). Replace `sk-ant-...` with your real key:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxx
```
Save, close, and run `run.bat` / `bash run.sh` again.

### Step 5: Use it

When you see `Uvicorn running on http://0.0.0.0:8000`, open **http://localhost:8000** in Chrome, Edge or Safari.
To stop the app, press **Ctrl + C** in the terminal window (or just close it).

### Troubleshooting

| Problem | Fix |
|---|---|
| `python is not recognized` / `Python 3.10+ not found` | Install Python (Step 1). On Windows, re-run the installer → Modify → tick "Add to PATH" |
| `address already in use` / port 8000 busy | Another app uses port 8000. Use another port. Windows (Command Prompt in the folder): `set PORT=8080` then `run.bat`. Mac: `PORT=8080 bash run.sh`. Then open http://localhost:8080 |
| "Server has no ANTHROPIC_API_KEY set" | The `.env` file is missing or still has `sk-ant-...`. Fix it and restart |
| "Server API key is missing or invalid" | Copy the key again from the Console; no spaces or quotes |
| Camera doesn't open | Allow camera access in the browser. On Mac also: System Settings → Privacy & Security → Camera. On Windows: Settings → Privacy & security → Camera. The live camera only works on `localhost` or `https://` |
| `.env` file not visible | It's a hidden file. Windows: View → Show → Hidden items. Mac Finder: Cmd + Shift + . |

**Using a phone:** the camera needs `https://`. Expose the laptop with a tunnel such as `ngrok http 8000` or `cloudflared tunnel --url http://localhost:8000` and open the https URL on the phone. Uploading photos also works over plain `http://<laptop-ip>:8000` on the same Wi-Fi.

### Manual setup (if the scripts don't work)

```bash
# Mac / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then put your key in .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
```bat
:: Windows (Command Prompt)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Deploy

Any Python host works (Render, Railway, Fly.io, Google Cloud Run). Start command:

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set `ANTHROPIC_API_KEY` as an environment variable on the host.

## Disclaimer

TechAranya gives guidance, not a guarantee. For serious crop loss, consult a local agriculture extension officer or nursery.
