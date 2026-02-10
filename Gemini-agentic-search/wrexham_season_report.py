"""
Wrexham AFC season report: Gemini with Google Search grounding.

Fetches season analysis from the web, enforces a Pydantic schema,
and writes an HTML report opened in the browser.
"""

import json
import os
import sys
import traceback
import webbrowser

from decouple import config
from google import genai
from google.genai import types
from pydantic import BaseModel


# Settings for the report
CLUB: str = "Wrexham AFC"
SEASON: str = "2024-2025"
MODEL: str = "gemini-2.5-flash"
OUTPUT_HTML_FILENAME: str = "wrexham_2024_2025_season.html"


class SoccerAnalysis(BaseModel):
    """Defines the required keys and value types for the JSON output."""

    Domestic_performance: str
    International_performance: str
    Team_notes: str
    Team_photos: str
    Notable_events: str


def build_prompt(club: str, season: str) -> str:
    """Build the analysis prompt parameterised by club and season."""
    return (
        f"Using only soccer websites, give me an analysis of the "
        f"English soccer team {club}'s season {season}. "
        "The analysis MUST be returned as a JSON object, strictly "
        "following the provided schema. "
        "The analysis should include: "
        "* Domestic league and cup performance. Include best and "
        "worst results. (HTML string). "
        "* International performance (\"No international games played.\" "
        "if no games) (HTML string). "
        "* Team notes (best players, team and manager changes) "
        "(HTML string). "
        "* Team photos (if you can definitely find photos for this "
        "team for this season, include them as links. If not, say "
        "so.) "
        "* Any notable drama/scandals on or off the pitch "
        "(HTML string)."
    )


def call_gemini_search_only(
    client: genai.Client,
    prompt: str,
) -> types.GenerateContentResponse | None:
    """One Gemini call with Google Search only (no schema)."""
    try:
        return client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
    except Exception as e:
        _, _, tb = sys.exc_info()
        line = tb.tb_lineno if tb else "?"
        print(f"Gemini search-only call failed (line {line}): {e}")
        return None


def call_gemini_format_only(
    client: genai.Client,
    raw_text: str,
) -> types.GenerateContentResponse | None:
    """Ask Gemini to convert raw text into SoccerAnalysis JSON (no search)."""
    format_prompt = (
        "Convert the following analysis text into a JSON object with exactly "
        "these keys (all string values): Domestic_performance, "
        "International_performance, Team_notes, Team_photos, Notable_events. "
        "Use the content below; if a section is missing, use a short placeholder. "
        "Output only valid JSON, no markdown.\n\n"
        f"{raw_text}"
    )
    try:
        return client.models.generate_content(
            model=MODEL,
            contents=format_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SoccerAnalysis,
            ),
        )
    except Exception as e:
        _, _, tb = sys.exc_info()
        line = tb.tb_lineno if tb else "?"
        print(f"Gemini format-only call failed (line {line}): {e}")
        return None


def parse_response_to_analysis(
    response: types.GenerateContentResponse,
) -> SoccerAnalysis | None:
    """
    Parse Gemini response into a SoccerAnalysis instance.

    Uses response.parsed if available, else response.text + JSON parse + validate.
    """
    if getattr(response, "parsed", None) is not None:
        if isinstance(response.parsed, SoccerAnalysis):
            return response.parsed
        # SDK might return a dict
        try:
            return SoccerAnalysis.model_validate(response.parsed)
        except Exception:
            pass
    text = (response.text or "").strip()
    if not text:
        return None
    # Strip markdown code fence if present
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        data = json.loads(text)
        # Accept nested {"analysis": {"domestic_performance": ..., ...}}
        if isinstance(data, dict) and "analysis" in data and isinstance(data["analysis"], dict):
            inner = data["analysis"]
            # Map snake_case to schema field names
            mapping = {
                "domestic_performance": "Domestic_performance",
                "international_performance": "International_performance",
                "team_notes": "Team_notes",
                "team_photos": "Team_photos",
                "notable_events": "Notable_events",
            }
            flattened = {}
            for snake, pascal in mapping.items():
                val = inner.get(snake) or inner.get(pascal)
                if val is not None:
                    flattened[pascal] = str(val)
                else:
                    flattened[pascal] = ""
            if len(flattened) == 5:
                return SoccerAnalysis.model_validate(flattened)
        return SoccerAnalysis.model_validate(data)
    except (json.JSONDecodeError, Exception) as e:
        _, _, tb = sys.exc_info()
        line = tb.tb_lineno if tb else "?"
        print(f"Parse/validate failed (line {line}): {e}")
        return None


def fetch_analysis(client: genai.Client, club: str, season: str) -> SoccerAnalysis | None:
    """
    Fetch season analysis from Gemini (Google Search grounding, then parse).

    The API does not support tool use (Google Search) with response_mime_type
    application/json, so we use search-only then parse JSON (or reformat with
    a second call if needed).
    """
    prompt = build_prompt(club=club, season=season)

    response = call_gemini_search_only(client=client, prompt=prompt)
    if response is None or not (response.text or "").strip():
        print("Search-only call failed or empty response.")
        return None

    analysis = parse_response_to_analysis(response)
    if analysis is not None:
        return analysis

    # Second fallback: ask model to format previous answer into schema
    print("Parsing failed; reformatting with a second Gemini call.")
    response = call_gemini_format_only(client=client, raw_text=response.text)
    if response is not None:
        analysis = parse_response_to_analysis(response)
        if analysis is not None:
            return analysis

    return None


def analysis_to_html(analysis: SoccerAnalysis, club: str, season: str) -> str:
    """
    Turn a SoccerAnalysis instance into a full HTML document string.

    Uses one heading per field; field values may contain HTML from the model.
    """
    title = f"{club} {season} Season Analysis"
    sections = [
        ("Domestic performance", analysis.Domestic_performance),
        ("International performance", analysis.International_performance),
        ("Team notes", analysis.Team_notes),
        ("Team photos", analysis.Team_photos),
        ("Notable events", analysis.Notable_events),
    ]
    body_parts = []
    for heading, content in sections:
        body_parts.append(f'  <h2>{heading}</h2>')
        body_parts.append(f'  <div class="section-content">{content}</div>')

    body_html = "\n".join(body_parts)
    return (
        f'<!DOCTYPE html>\n<html lang="en">\n'
        f'<head>\n  <meta charset="UTF-8">\n  <title>{title}</title>\n'
        f'  <style>\n'
        f"    body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}\n"
        f"    .section-content {{ margin-bottom: 2rem; line-height: 1.5; }}\n"
        f"    .section-content a {{ color: #0066cc; }}\n"
        f"  </style>\n</head>\n<body>\n"
        f"  <h1>{title}</h1>\n"
        f"{body_html}\n"
        f"</body>\n</html>\n"
    )


def save_and_open_html(html_string: str, filepath: str) -> None:
    """Write HTML to file and open it in the default browser."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_string)
    url = "file://" + os.path.abspath(filepath)
    webbrowser.open(url)
    print(f"Report saved to {filepath} and opened in browser.")


if __name__ == "__main__":
    try:
        api_key = config("GOOGLE_API_KEY", default=None)
        if not api_key:
            print("GOOGLE_API_KEY not set. Add it to .env in this directory.")
            sys.exit(1)

        client = genai.Client(api_key=api_key)
        analysis = fetch_analysis(client=client, club=CLUB, season=SEASON)
        if analysis is None:
            print("Could not obtain a valid analysis from Gemini.")
            sys.exit(1)

        html = analysis_to_html(analysis=analysis, club=CLUB, season=SEASON)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, OUTPUT_HTML_FILENAME)
        save_and_open_html(html_string=html, filepath=output_path)
    except Exception:
        _, _, tb = sys.exc_info()
        line = tb.tb_lineno if tb else "?"
        print(f"Error at line {line}:")
        traceback.print_exc()
        sys.exit(1)
