# Gemini agentic search

Calls the Gemini API with Google Search grounding to run an internet search and return the top results (e.g. for "Mike Woodward").

Uses the same Gemini service as the Django app: `google-genai`, model `gemini-2.5-flash`.

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

   Copy `GOOGLE_API_KEY` from the Django app `.env` (in `5 Django app/.env`) into a `.env` file in this directory:

   ```
   GOOGLE_API_KEY=your-key-here
   ```

   Do not commit `.env`; it is listed in `.gitignore`.

## Run

From this directory (with the venv activated):

### Wrexham season report

```bash
python wrexham_season_report.py
```

The script uses Gemini with Google Search grounding to fetch an analysis of Wrexham AFC's 2024-2025 season. The result is validated against a Pydantic schema (`SoccerAnalysis`), turned into an HTML page with headings for domestic performance, international performance, team notes, team photos, and notable events, then saved as `wrexham_2024_2025_season.html` and opened in your default browser.
