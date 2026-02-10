"""
Hand test: load API key from .env and run a minimal check.
"""

from decouple import config
from google import genai
from google.genai import types
from pydantic import BaseModel
import json


def get_api_key() -> str | None:
    """
    Read the API key from the .env file in the current directory.

    Returns:
        The value of GOOGLE_API_KEY from .env, or None if unset or missing.
    """
    return config("GOOGLE_API_KEY", default=None)


class SoccerAnalysis(BaseModel):
    """Defines the required keys and value types for the JSON output."""

    Domestic_performance: str
    International_performance: str
    Team_notes: str
    Team_photos: str
    Notable_events: str


if __name__ == "__main__":

    # Get the API key
    # ===============
    api_key = get_api_key()
    if api_key:
        print("API key loaded successfully.")
    else:
        print("API key not found. Add GOOGLE_API_KEY to .env in this directory.")

    # Team name and season
    # =====================
    club = "Wrexham AFC"
    season = "2024-2025"

    # Build the prompt
    # ================
    prompt = (
        f"Using only soccer websites, give me an analysis of the "
        f"English soccer team {club}'s season {season}. "
        "The analysis should include: "
        "* Domestic league and cup performance. Include best and "
        "worst results. "
        "* International performance. If no games played, say so. "
        "* Team notes (best players, team and manager changes). "
        "* Team photos (if you can definitely find photos for this "
        "team for this season, include them as links. If not, say "
        "so.) "
        "* Any notable drama/scandals on or off the pitch "
    )
    response_schema = SoccerAnalysis

    # Call the Gemini API
    # ===================
    client = genai.Client(api_key=api_key)
    search_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    format_prompt = (
        f"Format this information as JSON: {search_response.text}"
    )
    formatted_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=format_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema
        )
    )
    parsed_data = json.loads(formatted_response.text)

    # Print the response
    # ==================
    for k, v in parsed_data.items():
        print(f"{k}: {v}")