# Gemini agentic search

This repository is a small set of **test code** for getting an **agentic Gemini-based system** up and running.

It uses the Gemini API with Google Search grounding to run internet searches and return structured results (e.g. soccer season analyses), via the same Gemini client as the Django app: **google-genai**, model **gemini-2.5-flash**.

## Project contents

| File | Description |
|------|-------------|
| `hand_test.py` | Minimal check: loads `GOOGLE_API_KEY` from `.env`, calls Gemini with Google Search for a Wrexham AFC 2024–2025 analysis, parses JSON with a `SoccerAnalysis` Pydantic schema, and prints the result. |
| `wrexham_season_report.py` | Full report: fetches the same analysis, validates against `SoccerAnalysis`, builds an HTML report, saves it as `wrexham_2024_2025_season.html`, and opens it in the default browser. |
| `requirements.txt` | Dependencies: `google-genai`, `python-decouple`, `pydantic`. |

## Setup

1. **Create a virtual environment** (from this directory):

   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the API key**:

   Copy `GOOGLE_API_KEY` from the Django app `.env` (e.g. `5 Django app/.env`) into a `.env` file in this directory:

   ```
   GOOGLE_API_KEY=your-key-here
   ```

   Do not commit `.env`; it is listed in `.gitignore`.

## Run

From this directory (with the venv activated):

### Hand test (minimal check)

```bash
python hand_test.py
```

Loads the API key, calls Gemini with Google Search for Wrexham AFC 2024–2025, formats the response as JSON using the `SoccerAnalysis` schema, and prints each field to the console.

### Wrexham season report (HTML report)

```bash
python wrexham_season_report.py
```

Uses Gemini with Google Search grounding to fetch an analysis of Wrexham AFC's 2024–2025 season. The result is validated against the `SoccerAnalysis` Pydantic schema, turned into an HTML page with sections for domestic performance, international performance, team notes, team photos, and notable events, then saved as `wrexham_2024_2025_season.html` and opened in your default browser.
